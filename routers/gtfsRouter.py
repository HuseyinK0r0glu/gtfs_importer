from fastapi import FastAPI , UploadFile , File , Depends , HTTPException
from sqlalchemy.orm import Session
import shutil
import tempfile
import zipfile
import json
import os
import uuid
from datetime import datetime

from db.database import get_db
from models.routeModel import Route
from models.importStatusModel import importStatus
from enums.importStatusEnum import importStatusEnum
from tasks import process_gtfs_routes , process_gtfs_stops , process_gtfs_agency

async def firstApiCall():
    return {"message" : "Hello World"}

async def gtfsImporter(file : UploadFile = File(...) , db : Session = Depends(get_db)):

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

        import_status.task_id = f"{routes_task.id},{stops_task.id},{agency_task.id}" 
        db.commit()

        return {
            "message" : "GTFS files queued for processing",
            "snapshot_id" : snapshot_id,
            "task_ids" : {
                "agency": agency_task.id,
                "routes": routes_task.id,
                "stops": stops_task.id
            },
            "status" : "PENDING"
        }

    except Exception as e:
        # rollback undo changes made during that transcation
        db.rollback()
        if os.path.exists(tmp_zip_path):
            os.remove(tmp_zip_path)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

async def getImportBySnapshot(snapshot_id : str , db : Session = Depends(get_db)):

    import_status = db.query(importStatus).filter(importStatus.snapshot_id == snapshot_id).first()

    if not import_status:
        raise HTTPException(status_code=404, detail="Import status not found")
    
    try:
        result_data = None
        if import_status.result:
            try:
                result_data = json.loads(import_status.result)
            except json.JSONDecodeError:
                result_data = import_status.result
        
        return {
            "snapshot_id": import_status.snapshot_id,
            "status": import_status.status.value if import_status.status else None,
            "task_id": import_status.task_id,
            "created_at": import_status.created_at,
            "completed_at": import_status.completed_at,
            "result": result_data,
            "error_message": import_status.error_message
        }
    except Exception as e:
        print(f"Error in getImportBySnapshot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")