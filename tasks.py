from fastapi import HTTPException
from celeryApp import celery_app
import shutil
import zipfile
import tempfile
import csv
import os
import json
from datetime import datetime
import uuid

from db.database import SessionLocal
from models.routeModel import Route
from models.stopModel import Stop
from models.agencyModel import Agency
from models.calendarDatesModel import CalendarDates
from models.calendarModel import Calendar
from models.tripsModel import Trip
from models.stopTimesModel import StopTime
from models.shapesModel import Shape
from enums.importStatusEnum import importStatusEnum  
from models.importStatusModel import importStatus

def determineOverallStatus(snapshot_id,results, expected_task_count=8,db_session=None):

    if db_session:
        db = db_session
        should_close = False
    else:
        db = SessionLocal()
        should_close = True

    import_status = db.query(importStatus).filter(importStatus.snapshot_id == snapshot_id).first()
    
    if not import_status:
        print("import status not found")
        return

    if not results:
        return importStatusEnum.PENDING

    for result in results:
        if result.get('status') == "FAILED":
            import_status.completed_at = datetime.utcnow()
            db.commit()
            return importStatusEnum.REJECTED
    
    if len(results) < expected_task_count:
        return importStatusEnum.PENDING
    
    import_status.completed_at = datetime.utcnow()
    db.commit()
    return importStatusEnum.ACCEPTED


def update_import_status(snapshot_id, status, result=None, error_message=None, db_session=None):

    #!!!
    if db_session:
        db = db_session
        should_close = False
    else:
        db = SessionLocal()
        should_close = True
    
    try:
        import_status = db.query(importStatus).filter(importStatus.snapshot_id == snapshot_id).first()
        if import_status:
            
            if result:
                try:
                    existing_result = json.loads(import_status.result) if import_status.result else None
                except Exception:
                    existing_result = None

                if existing_result is None:
                    combined_result = [result]
                elif isinstance(existing_result, list):
                    combined_result = existing_result + [result]
                else:
                    combined_result = [existing_result, result]

                import_status.result = json.dumps(combined_result)
                
                # Determine overall status based on all results
                overallStatus = determineOverallStatus(snapshot_id,combined_result, expected_task_count=8,db_session=db)
                import_status.status = overallStatus
                
            else:
                try:
                    existing_results = json.loads(import_status.result) if import_status.result else []
                    overallStatus = determineOverallStatus(snapshot_id,existing_results, expected_task_count=8,db_session=db)
                    import_status.status = overallStatus
                    
                except Exception:
                    pass

            if error_message:
                import_status.error_message = error_message
            
            db.commit()
    finally:
        if should_close:
            db.close()

@celery_app.task(bind=True)
def process_gtfs_routes(self,tmp_zip_path,snapshot_id):

    if not snapshot_id:
        snapshot_id = str(uuid.uuid4())

    try:

        self.update_state(state='PROGRESS', meta={'status': 'Processing routes...'})

        db = SessionLocal()

        tmp_dir = tempfile.mkdtemp()

        try:
            with zipfile.ZipFile(tmp_zip_path,"r") as zip_ref:
                zip_ref.extractall(tmp_dir)

            routes_path = os.path.join(tmp_dir,"routes.txt")
            if not os.path.exists(routes_path):
                raise HTTPException(status_code=400, detail="routes.txt not found in zip")


            with open(routes_path,newline='',encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                routesCount = 0
                for row in reader:
                    route = Route(
                        route_id=row["route_id"],
                        agency_id=row.get("agency_id", ""),
                        route_short_name=row.get("route_short_name", ""),
                        route_long_name=row.get("route_long_name", ""),
                        route_desc=row.get("route_desc", ""),
                        route_type=row.get("route_type", ""),
                        route_url=row.get("route_url", ""),
                        route_color=row.get("route_color", ""),
                        route_text_color=row.get("route_text_color", "")
                    )
                    db.merge(route)
                    routesCount+=1
                db.commit()

                shutil.rmtree(tmp_dir)

                result = {
                    'status': 'SUCCESS',
                    'snapshot_id': snapshot_id,
                    'routes_imported': routesCount,
                    'message': f'Successfully imported {routesCount} routes'
                }

                update_import_status(snapshot_id, None, result, db_session=db)

                return result
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Error processing routes: {str(e)}")
        finally:
            db.close()
            # Clean up temp files even if error occurs
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
    except Exception as e:

        failed_result = {
            'status': 'FAILED',
            'snapshot_id': snapshot_id,
            'error': str(e)
        }
        
        update_import_status(snapshot_id, None, failed_result, str(e))
        
        return failed_result


@celery_app.task(bind=True)
def process_gtfs_stops(self,tmp_zip_path,snapshot_id):

    if not snapshot_id:
        snapshot_id = str(uuid.uuid4())

    try:

        self.update_state(state='PROGRESS', meta={'status': 'Processing stops...'})

        db = SessionLocal()

        tmp_dir = tempfile.mkdtemp()

        try:
            with zipfile.ZipFile(tmp_zip_path,"r") as zip_ref:
                zip_ref.extractall(tmp_dir)

            stops_path = os.path.join(tmp_dir,"stops.txt")
            if not os.path.exists(stops_path):
                raise HTTPException(status_code=400, detail="stops.txt not found in zip")

            with open(stops_path,newline='',encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                stopsCount = 0
                for row in reader:
                    stop = Stop(
                        stop_id=row["stop_id"],
                        stop_name=row["stop_name"],
                        stop_desc=row.get("stop_desc", ""),
                        stop_lat=row.get("stop_lat", ""),
                        stop_lon=row.get("stop_lon", ""),
                        zone_id=row.get("zone_id", ""),
                        stop_url=row.get("stop_url", "")
                    )
                    db.merge(stop)
                    stopsCount+=1
                db.commit()

                shutil.rmtree(tmp_dir)

                result = {
                    'status': 'SUCCESS',
                    'snapshot_id': snapshot_id,
                    'stops_imported': stopsCount,
                    'message': f'Successfully imported {stopsCount} stops'
                }

                update_import_status(snapshot_id, None, result, db_session=db)

                return result
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Error processing stops: {str(e)}")
        finally:
            db.close()
            # Clean up temp files even if error occurs
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
    except Exception as e:

        failed_result = {
            'status': 'FAILED',
            'snapshot_id': snapshot_id,
            'error': str(e)
        }
        
        update_import_status(snapshot_id, None, failed_result, str(e))
        
        return failed_result

@celery_app.task(bind=True)
def process_gtfs_agency(self,tmp_zip_path,snapshot_id):

    if not snapshot_id:
        snapshot_id = str(uuid.uuid4())

    try:

        self.update_state(state='PROGRESS', meta={'status': 'Processing agency...'})

        db = SessionLocal()

        tmp_dir = tempfile.mkdtemp()

        try:
            with zipfile.ZipFile(tmp_zip_path,"r") as zip_ref:
                zip_ref.extractall(tmp_dir)

            agency_path = os.path.join(tmp_dir,"agency.txt")
            if not os.path.exists(agency_path):
                raise HTTPException(status_code=400, detail="agency.txt not found in zip")


            with open(agency_path,newline='',encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                agencyCount = 0
                for row in reader:

                    agency = Agency(
                        agency_id=row["agency_id"],
                        agency_name=row['agency_name'],
                        agency_url=row['agency_url'],
                        agency_timezone=row['agency_timezone'],
                        agency_lang=row['agency_lang'],
                        agency_phone=row['agency_phone'],
                        agency_fare_url=row['agency_fare_url'],
                        agency_email=row['agency_email']
                    )
                    db.merge(agency)
                    agencyCount+=1
                db.commit()

                shutil.rmtree(tmp_dir)

                result = {
                    'status': 'SUCCESS',
                    'snapshot_id': snapshot_id,
                    'agencies_imported': agencyCount,
                    'message': f'Successfully imported {agencyCount} agencies'
                }

                update_import_status(snapshot_id, None, result, db_session=db)

                return result
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Error processing agency: {str(e)}")
        finally:
            db.close()
            # Clean up temp files even if error occurs
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
    except Exception as e:

        failed_result = {
            'status': 'FAILED',
            'snapshot_id': snapshot_id,
            'error': str(e)
        }
        
        update_import_status(snapshot_id, None, failed_result, str(e))
        
        return failed_result
    

@celery_app.task(bind=True) 
def process_gtfs_calendar_dates(self,tmp_zip_path,snapshot_id):

    if not snapshot_id:
        snapshot_id = str(uuid.uuid4())

    try:

        self.update_state(state='PROGRESS', meta={'status': 'Processing calendar_dates...'})

        db = SessionLocal()

        tmp_dir = tempfile.mkdtemp()

        try:
            with zipfile.ZipFile(tmp_zip_path,"r") as zip_ref:
                zip_ref.extractall(tmp_dir)

            calendar_dates_path = os.path.join(tmp_dir,"calendar_dates.txt")
            if not os.path.exists(calendar_dates_path):
                raise HTTPException(status_code=400, detail="calendar_dates.txt not found in zip")


            with open(calendar_dates_path,newline='',encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                calendarDates = 0
                for row in reader:

                    calendar_date = CalendarDates(
                        service_id=row["service_id"],
                        date=row["date"],
                        exception_type=int(row["exception_type"])
                    )

                    db.merge(calendar_date)
                    calendarDates+=1
                db.commit()

                shutil.rmtree(tmp_dir)

                result = {
                    'status': 'SUCCESS',
                    'snapshot_id': snapshot_id,
                    'calendar_dates_imported': calendarDates,
                    'message': f'Successfully imported {calendarDates} calendar dates'
                }

                update_import_status(snapshot_id, None, result, db_session=db)

                return result
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Error processing calendar dates: {str(e)}")
        finally:
            db.close()
            # Clean up temp files even if error occurs
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
    except Exception as e:

        update_import_status(snapshot_id, None, None, str(e))
        
        return {
            'status': 'FAILED',
            'snapshot_id': snapshot_id,
            'error': str(e)
        }
    

@celery_app.task(bind=True)
def process_gtfs_calendars(self,tmp_zip_path,snapshot_id):

    if not snapshot_id:
        snapshot_id = str(uuid.uuid4())

    try:

        self.update_state(state='PROGRESS', meta={'status': 'Processing calendars...'})

        db = SessionLocal()

        tmp_dir = tempfile.mkdtemp()

        try:
            with zipfile.ZipFile(tmp_zip_path,"r") as zip_ref:
                zip_ref.extractall(tmp_dir)

            calendars_path = os.path.join(tmp_dir,"calendar.txt")
            if not os.path.exists(calendars_path):
                raise HTTPException(status_code=400, detail="calendar.txt not found in zip")


            with open(calendars_path,newline='',encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                calendarCount = 0
                for row in reader:
                    
                    calendar = Calendar(
                        service_id=row["service_id"],
                        monday=row["monday"],
                        tuesday=row["tuesday"],
                        wednesday=row["wednesday"],
                        thursday=row["thursday"],
                        friday=row["friday"],
                        saturday=row["saturday"],
                        sunday=row["sunday"],
                        start_date=row["start_date"],
                        end_date=row["end_date"],
                    )

                    db.merge(calendar)
                    calendarCount+=1
                db.commit()

                shutil.rmtree(tmp_dir)

                result = {
                    'status': 'SUCCESS',
                    'snapshot_id': snapshot_id,
                    'calendars_imported': calendarCount,
                    'message': f'Successfully imported {calendarCount} calendars'
                }

                update_import_status(snapshot_id, None, result, db_session=db)

                return result
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Error processing calendars: {str(e)}")
        finally:
            db.close()
            # Clean up temp files even if error occurs
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
    except Exception as e:

        failed_result = {
            'status': 'FAILED',
            'snapshot_id': snapshot_id,
            'error': str(e)
        }
        
        update_import_status(snapshot_id, None, failed_result, str(e))
        
        return failed_result
    

@celery_app.task(bind=True)
def process_gtfs_trips(self,tmp_zip_path,snapshot_id):

    if not snapshot_id:
        snapshot_id = str(uuid.uuid4())

    try:

        self.update_state(state='PROGRESS', meta={'status': 'Processing trips...'})

        db = SessionLocal()

        tmp_dir = tempfile.mkdtemp()

        try:
            with zipfile.ZipFile(tmp_zip_path,"r") as zip_ref:
                zip_ref.extractall(tmp_dir)

            trips_path = os.path.join(tmp_dir,"trips.txt")
            if not os.path.exists(trips_path):
                raise HTTPException(status_code=400, detail="trips.txt not found in zip")


            with open(trips_path,newline='',encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                tripsCount = 0
                for row in reader:

                    trip = Trip(
                        trip_id=row["trip_id"],
                        route_id=row["route_id"], 
                        service_id=row["service_id"],
                        trip_headsign=row["trip_headsign"],
                        direction_id=row["direction_id"],
                        block_id=row["block_id"],
                        shape_id=row["shape_id"]
                    )

                    db.merge(trip)
                    tripsCount+=1
                db.commit()

                shutil.rmtree(tmp_dir)

                result = {
                    'status': 'SUCCESS',
                    'snapshot_id': snapshot_id,
                    'trips_imported': tripsCount,
                    'message': f'Successfully imported {tripsCount} trips'
                }

                update_import_status(snapshot_id, None, result, db_session=db)

                return result
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Error processing trips: {str(e)}")
        finally:
            db.close()
            # Clean up temp files even if error occurs
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
    except Exception as e:

        failed_result = {
            'status': 'FAILED',
            'snapshot_id': snapshot_id,
            'error': str(e)
        }
        
        update_import_status(snapshot_id, None, failed_result, str(e))
        
        return failed_result
    
@celery_app.task(bind=True)
def process_gtfs_stop_times(self,tmp_zip_path,snapshot_id):

    if not snapshot_id:
        snapshot_id = str(uuid.uuid4())

    try:

        self.update_state(state='PROGRESS', meta={'status': 'Processing stop times...'})

        db = SessionLocal()

        tmp_dir = tempfile.mkdtemp()

        try:
            with zipfile.ZipFile(tmp_zip_path,"r") as zip_ref:
                zip_ref.extractall(tmp_dir)

            stop_times_path = os.path.join(tmp_dir,"stop_times.txt")
            if not os.path.exists(stop_times_path):
                raise HTTPException(status_code=400, detail="stop_times.txt not found in zip")

            with open(stop_times_path,newline='',encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                stopTimesCount = 0
                batch_size = 1000  # Process in batches for better performance
                
                for row in reader:
                    stopTime = StopTime(
                        trip_id=row["trip_id"],
                        stop_sequence=int(row["stop_sequence"]),
                        arrival_time=row["arrival_time"],
                        departure_time=row["departure_time"],
                        stop_id=row["stop_id"],
                        stop_headsign=row["stop_headsign"],
                        pickup_type=row["pickup_type"],
                        drop_off_type=row["drop_off_type"],
                        shape_dist_traveled=row["shape_dist_traveled"],
                    )

                    db.merge(stopTime)
                    stopTimesCount+=1
                    
                    # Commit in batches and update progress
                    if stopTimesCount % batch_size == 0:
                        db.commit()
                        self.update_state(state='PROGRESS', meta={
                            'status': f'Processed {stopTimesCount} stop times...'
                        })
                
                # Final commit for remaining records
                db.commit()

                shutil.rmtree(tmp_dir)

                result = {
                    'status': 'SUCCESS',
                    'snapshot_id': snapshot_id,
                    'stop_times_imported': stopTimesCount,
                    'message': f'Successfully imported {stopTimesCount} stop times'
                }

                update_import_status(snapshot_id, None, result, db_session=db)

                return result
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Error processing stop times: {str(e)}")
        finally:
            db.close()
            # Clean up temp files even if error occurs
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
    except Exception as e:

        failed_result = {
            'status': 'FAILED',
            'snapshot_id': snapshot_id,
            'error': str(e)
        }
        
        update_import_status(snapshot_id, None, failed_result, str(e))
        
        return failed_result
    
@celery_app.task(bind=True)
def process_gtfs_shapes(self,tmp_zip_path,snapshot_id):

    if not snapshot_id:
        snapshot_id = str(uuid.uuid4())

    try:

        self.update_state(state='PROGRESS', meta={'status': 'Processing shapes...'})

        db = SessionLocal()

        tmp_dir = tempfile.mkdtemp()

        try:
            with zipfile.ZipFile(tmp_zip_path,"r") as zip_ref:
                zip_ref.extractall(tmp_dir)

            shapes_path = os.path.join(tmp_dir,"shapes.txt")
            if not os.path.exists(shapes_path):
                raise HTTPException(status_code=400, detail="shapes.txt not found in zip")


            with open(shapes_path,newline='',encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                shapesCount = 0
                for row in reader:

                    shape = Shape(
                        shape_id=row["shape_id"],
                        shape_pt_sequence=int(row["shape_pt_sequence"]),
                        shape_pt_lat=float(row["shape_pt_lat"]),
                        shape_pt_lon=float(row["shape_pt_lon"]),
                        shape_dist_traveled=row["shape_dist_traveled"],
                    )

                    db.merge(shape)
                    shapesCount+=1
                db.commit()

                shutil.rmtree(tmp_dir)

                result = {
                    'status': 'SUCCESS',
                    'snapshot_id': snapshot_id,
                    'shapes_imported': shapesCount,
                    'message': f'Successfully imported {shapesCount} shapes'
                }

                update_import_status(snapshot_id, None, result, db_session=db)

                return result
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Error processing shapes: {str(e)}")
        finally:
            db.close()
            # Clean up temp files even if error occurs
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
    except Exception as e:

        failed_result = {
            'status': 'FAILED',
            'snapshot_id': snapshot_id,
            'error': str(e)
        }
        
        update_import_status(snapshot_id, None, failed_result, str(e))
        
        return failed_result
