from sqlalchemy.orm import Session
from typing import Optional, List
from models.tripsModel import Trip

def get_trips_by_route_id(db : Session , snapshot_id : str , route_id : str) -> List[Trip]:
    return db.query(Trip).filter(Trip.route_id == route_id , Trip.snapshot_id == snapshot_id).all()