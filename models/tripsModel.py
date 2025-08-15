from sqlalchemy import Column , Integer , String , PrimaryKeyConstraint
from db.database import Base

class Trip(Base):
    __tablename__ = "trips"

    trip_id = Column(String , primary_key=True)
    snapshot_id = Column(String , primary_key=True)

    route_id = Column(String)
    service_id = Column(String)
    trip_headsign = Column(String)
    direction_id = Column(String)
    block_id = Column(String)
    shape_id = Column(String)

    # Define the composite primary key constraint
    __table_args__ = (
        PrimaryKeyConstraint('trip_id', 'snapshot_id'),
    ) 

