from sqlalchemy import Column, String, Integer, PrimaryKeyConstraint
from db.database import Base

class StopTime(Base):
    __tablename__ = "stop_times"

    trip_id = Column(String, primary_key=True)
    stop_sequence = Column(Integer, primary_key=True)
    
    arrival_time = Column(String)
    departure_time = Column(String)
    stop_id = Column(String)
    stop_headsign = Column(String)
    pickup_type = Column(String)
    drop_off_type = Column(String)
    shape_dist_traveled = Column(String)
    
    # Define the composite primary key constraint
    __table_args__ = (
        PrimaryKeyConstraint('trip_id', 'stop_sequence'),
    ) 