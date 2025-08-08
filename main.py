from fastapi import FastAPI
from typing import List

from routers import gtfsRouter

app = FastAPI()

from db.database import engine, Base 

Base.metadata.create_all(bind=engine)

app.add_api_route("/firstApiCall",gtfsRouter.firstApiCall,methods=["GET"])
app.add_api_route("/upload-gtfs",gtfsRouter.gtfsImporter,methods=["POST"])

if __name__ == "__main__":
    import uvicorn 
    uvicorn.run(app, host="0.0.0.0", port=8000)