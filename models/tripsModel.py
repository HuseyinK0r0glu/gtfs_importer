from sqlalchemy import Column , Integer , String
from db.database import Base

class Trip(Base):
    __tablename__ = "trips"

    trip_id = Column(String , primary_key=True)
    route_id = Column(String)
    service_id = Column(String)
    trip_headsign = Column(String)
    direction_id = Column(String)
    block_id = Column(String)
    shape_id = Column(String)
