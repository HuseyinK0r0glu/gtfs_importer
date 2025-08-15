from fastapi import FastAPI
from typing import List

from routers import gtfsRouter
from models import calendarDatesModel , calendarModel , routeModel, importStatusModel, stopModel, agencyModel

from schemas.gtfs_schemas import GtfsImportResponse , ImportStatusResponse

app = FastAPI()

from db.database import engine, Base 

Base.metadata.create_all(bind=engine)

app.add_api_route("/firstApiCall",gtfsRouter.firstApiCall,methods=["GET"])
app.add_api_route("/upload-gtfs",gtfsRouter.gtfsImporter,methods=["POST"],response_model=GtfsImportResponse)
app.add_api_route("/all_imports",gtfsRouter.getlAllImports,methods=["GET"],response_model=List[ImportStatusResponse])
app.add_api_route("/imports/{snapshot_id}",gtfsRouter.getImportBySnapshot,methods=["GET"],response_model=ImportStatusResponse)

if __name__ == "__main__":  
    import uvicorn 
    uvicorn.run(app, host="0.0.0.0", port=8000)