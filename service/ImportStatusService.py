from sqlalchemy.orm import Session
from typing import Optional
from models.importStatusModel import importStatus

def get_import_status_by_snapshot_id(db : Session,snapshot_id : str) -> Optional[importStatus]:
    return db.query(importStatus).filter(importStatus.snapshot_id == snapshot_id).first()
