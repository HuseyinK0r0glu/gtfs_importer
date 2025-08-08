from fastapi import FastAPI
from typing import List

from routers import gtfsRouter

app = FastAPI()

app.add_api_route("/firstApiCall",gtfsRouter.firstApiCall,methods=["GET"])

if __name__ == "__main__":
    import uvicorn 
    uvicorn.run(app, host="0.0.0.0", port=8000)