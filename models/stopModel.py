from sqlalchemy import Column, String, Float, Integer , PrimaryKeyConstraint
from db.database import Base  

class Stop(Base):
    __tablename__ = "stops"

    stop_id = Column(String, primary_key=True)
    snapshot_id = Column(String, primary_key=True)

    stop_name = Column(String, nullable=False)
    stop_desc = Column(String)
    stop_lat = Column(String) 
    stop_lon = Column(String)  
    zone_id = Column(String)
    stop_url = Column(String)

    # Define the composite primary key constraint
    __table_args__ = (
        PrimaryKeyConstraint('stop_id', 'snapshot_id'),
    ) 