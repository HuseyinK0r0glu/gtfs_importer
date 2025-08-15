from sqlalchemy.orm import Session
from typing import Optional, List
from models.routeModel import Route

def get_route_by_route_id(db : Session,snapshot_id : str , route_id : str) -> Optional[Route]:
    return db.query(Route).filter(Route.route_id == route_id,Route.snapshot_id == snapshot_id).first()

