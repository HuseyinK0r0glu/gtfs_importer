from sqlalchemy import Column, String, Float, Integer
from db.database import Base  

class Stop(Base):
    __tablename__ = "stops"
    stop_id = Column(String, primary_key=True)
    stop_name = Column(String, nullable=False)
    stop_desc = Column(String)
    stop_lat = Column(String) 
    stop_lon = Column(String)  
    zone_id = Column(String)
    stop_url = Column(String)