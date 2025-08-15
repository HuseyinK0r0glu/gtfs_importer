from pydantic import BaseModel
from typing import Dict , Optional , Any , List
from datetime import datetime

class GtfsImportResponse(BaseModel):
    message : str 
    snapshot_id : str
    task_ids : Dict[str,str]
    status : str

class ImportStatusResponse(BaseModel):
    snapshot_id : str
    status : Optional[str] = None
    task_id: Optional[str] = None
    created_at : Optional[datetime] = None
    completed_at : Optional[datetime] = None
    result : Optional[Any] = None
    error_message : Optional[str] = None

class RouteResponse(BaseModel):
    route_id : str
    agency_id : Optional[str] = None
    route_short_name: Optional[str] = None
    route_long_name: Optional[str] = None
    route_type: Optional[str] = None
    route_desc: Optional[str] = None
    route_url: Optional[str] = None
    route_color: Optional[str] = None
    route_text_color: Optional[str] = None