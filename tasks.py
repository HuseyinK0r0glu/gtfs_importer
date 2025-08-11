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
from enums.importStatusEnum import importStatusEnum  
from models.importStatusModel import importStatus

def update_import_status(snapshot_id, status, result=None, error_message=None):
    db = SessionLocal()
    try:
        import_status = db.query(importStatus).filter(importStatus.snapshot_id == snapshot_id).first()
        if import_status:
            import_status.status = status
            import_status.completed_at = datetime.utcnow()
            
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
            if error_message:
                import_status.error_message = error_message
                
            db.commit()
    finally:
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
                    db.add(route)
                    routesCount+=1
                db.commit()

                shutil.rmtree(tmp_dir)

                result = {
                    'status': 'SUCCESS',
                    'snapshot_id': snapshot_id,
                    'routes_imported': routesCount,
                    'message': f'Successfully imported {routesCount} routes'
                }

                update_import_status(snapshot_id, importStatusEnum.ACCEPTED, result)

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

        update_import_status(snapshot_id, importStatusEnum.REJECTED, None, str(e))
        
        return {
            'status': 'FAILED',
            'snapshot_id': snapshot_id,
            'error': str(e)
        }


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
                    db.add(stop)
                    stopsCount+=1
                db.commit()

                shutil.rmtree(tmp_dir)

                result = {
                    'status': 'SUCCESS',
                    'snapshot_id': snapshot_id,
                    'stops_imported': stopsCount,
                    'message': f'Successfully imported {stopsCount} stops'
                }

                update_import_status(snapshot_id, importStatusEnum.ACCEPTED, result)

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

        update_import_status(snapshot_id, importStatusEnum.REJECTED, None, str(e))
        
        return {
            'status': 'FAILED',
            'snapshot_id': snapshot_id,
            'error': str(e)
        }