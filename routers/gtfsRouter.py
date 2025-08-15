from fastapi import FastAPI , UploadFile , File , Depends , HTTPException
from sqlalchemy.orm import Session
import shutil
import tempfile
import zipfile
import json
import os
import uuid
from datetime import datetime

from typing import List

from db.database import get_db
from models.routeModel import Route
from models.importStatusModel import importStatus
from enums.importStatusEnum import importStatusEnum
from tasks import process_gtfs_routes , process_gtfs_stops , process_gtfs_agency , process_gtfs_calendar_dates , process_gtfs_calendars , process_gtfs_trips , process_gtfs_stop_times , process_gtfs_shapes

from schemas.gtfs_schemas import GtfsImportResponse , ImportStatusResponse , RouteResponse , TripResponse

from service.ImportStatusService import get_import_status_by_snapshot_id , get_all_import_statuses
from service.RouteService import get_route_by_route_id
from service.TripService import get_trips_by_route_id

async def firstApiCall():
    return {"message" : "Hello World"}

async def gtfsImporter(file : UploadFile = File(...) , db : Session = Depends(get_db)) -> GtfsImportResponse:

    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a zip")

    snapshot_id = str(uuid.uuid4())

    tmp_dir = tempfile.mkdtemp()
    tmp_zip_path = os.path.join(tmp_dir,file.filename)

    try:
        with open(tmp_zip_path , "wb") as buffer:
            shutil.copyfileobj(file.file,buffer)

        import_status = importStatus(
            snapshot_id=snapshot_id,
            status=importStatusEnum.PENDING,
            task_id=None,
            created_at=datetime.utcnow(),
            completed_at=None,  
            result=None, 
            error_message=None
        )
        db.add(import_status)
        db.commit()

        routes_task = process_gtfs_routes.delay(tmp_zip_path,snapshot_id)
        stops_task = process_gtfs_stops.delay(tmp_zip_path,snapshot_id)
        agency_task = process_gtfs_agency.delay(tmp_zip_path,snapshot_id)
        calendar_dates_task = process_gtfs_calendar_dates.delay(tmp_zip_path,snapshot_id)
        calendar_task = process_gtfs_calendars.delay(tmp_zip_path,snapshot_id)
        trips_task = process_gtfs_trips.delay(tmp_zip_path,snapshot_id)
        stop_times_task = process_gtfs_stop_times.delay(tmp_zip_path,snapshot_id)
        shapes_task = process_gtfs_shapes.delay(tmp_zip_path,snapshot_id)

        import_status.task_id = f"{routes_task.id},{stops_task.id},{agency_task.id},{calendar_dates_task.id},{calendar_task.id},{trips_task.id},{stop_times_task.id},{shapes_task.id}" 
        db.commit()

        return GtfsImportResponse(
            message="GTFS files queued for processing", 
            snapshot_id=snapshot_id,
            task_ids={
                "agency": agency_task.id,
                "routes": routes_task.id,
                "stops": stops_task.id,
                "calendar_dates": calendar_dates_task.id,
                "calendar": calendar_task.id,
                "trips": trips_task.id,
                "stop_times": stop_times_task.id,
                "shapes": shapes_task.id
            },
            status="PENDING"
        )

    except Exception as e:
        # rollback undo changes made during that transcation
        db.rollback()
        if os.path.exists(tmp_zip_path):
            os.remove(tmp_zip_path)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

async def getImportBySnapshot(snapshot_id : str , db : Session = Depends(get_db)) -> ImportStatusResponse:

    import_status = get_import_status_by_snapshot_id(db,snapshot_id)

    if not import_status:
        raise HTTPException(status_code=404, detail="Import status not found")
    
    try:
        result_data = None
        if import_status.result:
            try:
                result_data = json.loads(import_status.result)
            except json.JSONDecodeError:
                result_data = import_status.result
        
        return ImportStatusResponse(
            snapshot_id=import_status.snapshot_id,
            status=import_status.status.value if import_status.status else None,
            task_id=import_status.task_id,
            created_at=import_status.created_at,
            completed_at=import_status.completed_at,
            result=result_data,
            error_message=import_status.error_message
        )

    except Exception as e:
        print(f"Error in getImportBySnapshot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
async def getlAllImports(db : Session = Depends(get_db)) -> List[ImportStatusResponse]:
    
    imports = get_all_import_statuses(db)

    if not imports:
        return []

    try:
        result = []

        for import_status in imports:
            result_data = None
            if import_status.result:
                try:
                    result_data = json.loads(import_status.result)
                except json.JSONDecodeError:
                    result_data = import_status.result
            
            import_status_response = ImportStatusResponse(
                snapshot_id=import_status.snapshot_id,
                status=import_status.status.value if import_status.status else None,
                task_id=import_status.task_id,
                created_at=import_status.created_at,
                completed_at=import_status.completed_at,
                result=result_data,
                error_message=import_status.error_message
            )

            result.append(import_status_response)

        return result
    except Exception as e:
        print(f"Error in getlAllImports: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
async def getRouteById(snapshot_id : str  , route_id : str, db : Session = Depends(get_db)) -> RouteResponse:
    
    route = get_route_by_route_id(db,snapshot_id,route_id)

    if not route:
        raise HTTPException(status_code=404, detail="route not found")
    
    return RouteResponse(
        route_id = route.route_id,
        agency_id = route.agency_id,
        route_short_name = route.route_short_name,
        route_long_name= route.route_long_name,
        route_type = route.route_type,
        route_desc = route.route_desc,
        route_url = route.route_url,
        route_color = route.route_color,
        route_text_color = route.route_text_color
    )

async def getTripsByRoute(snapshot_id : str , route_id : str , db : Session = Depends(get_db)) -> List[TripResponse]:
    
    trips = get_trips_by_route_id(db,snapshot_id,route_id)

    if not trips:
        raise HTTPException(status_code=404, detail="No trips found for this route")

    trip_responses = []
    for trip in trips:
        trip_response = TripResponse(
            trip_id = trip.trip_id, 
            service_id = trip.service_id,
            trip_headsign = trip.trip_headsign,
            direction_id = trip.direction_id,
            block_id = trip.block_id,
            shape_id = trip.shape_id
        )
        trip_responses.append(trip_response)

    return trip_responses