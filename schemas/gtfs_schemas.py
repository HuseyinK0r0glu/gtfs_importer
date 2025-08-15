from pydantic import BaseModel
from typing import Dict

class GtfsImportResponse(BaseModel):
    message : str 
    snapshot_id : str
    task_ids : Dict[str,str]
    status : str