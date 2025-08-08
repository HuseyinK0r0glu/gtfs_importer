from fastapi import FastAPI , UploadFile , File , Depends , HTTPException
from sqlalchemy.orm import Session
import shutil
import tempfile
import zipfile
import csv 
import os

from db.database import get_db
from models.routeModel import Route

async def firstApiCall():
    return {"message" : "Hello World"}

async def gtfsImporter(file : UploadFile = File(...) , db : Session = Depends(get_db)):

    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a zip")

    tmp_dir = tempfile.mkdtemp()
    tmp_zip_path = os.path.join(tmp_dir,file.filename)

    try:
        with open(tmp_zip_path , "wb") as buffer:
            shutil.copyfileobj(file.file,buffer)

        with zipfile.ZipFile(tmp_zip_path,"r") as zip_ref:
            zip_ref.extractall(tmp_dir)
        
        routes_path = os.path.join(tmp_dir,"routes.txt")
        if not os.path.exists(routes_path):
            raise HTTPException(status_code=400, detail="routes.txt not found in zip")

        with open(routes_path,newline='',encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
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
            db.commit()

        return {"message" : "GTFS routes imported succesfully"}
    except:
        # rollback undo changes made during that transcation
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        shutil.rmtree(tmp_dir)
