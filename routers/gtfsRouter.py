from fastapi import FastAPI , UploadFile , File , Depends , HTTPException
from sqlalchemy.orm import Session
import shutil
import tempfile
import zipfile
import csv 
import os
import uuid
from datetime import datetime

from db.database import get_db
from models.routeModel import Route
from models.importStatusModel import importStatus
from enums.importStatusEnum import importStatusEnum
from tasks import process_gtfs_routes

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

        task = process_gtfs_routes.delay(tmp_zip_path,snapshot_id)

        import_status.task_id = task.id
        db.commit()

        return {
            "message" : "GTFS file queud for processing",
            "snapshot_id" : snapshot_id,
            "task_id" : task.id,
            "status" : "PENDING"
        }

    except Exception as e:
        # rollback undo changes made during that transcation
        db.rollback()
        if os.path.exists(tmp_zip_path):
            os.remove(tmp_zip_path)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
