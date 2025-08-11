from fastapi import FastAPI
from typing import List

from routers import gtfsRouter
from models import routeModel, importStatusModel, stopModel, agencyModel

app = FastAPI()

from db.database import engine, Base 

Base.metadata.create_all(bind=engine)

app.add_api_route("/firstApiCall",gtfsRouter.firstApiCall,methods=["GET"])
app.add_api_route("/upload-gtfs",gtfsRouter.gtfsImporter,methods=["POST"])
app.add_api_route("/imports/{snapshot_id}",gtfsRouter.getImportBySnapshot,methods=["GET"])

if __name__ == "__main__":
    import uvicorn 
    uvicorn.run(app, host="0.0.0.0", port=8000)