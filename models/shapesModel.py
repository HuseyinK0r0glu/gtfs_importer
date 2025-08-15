from sqlalchemy import Column, String, Integer, Float, PrimaryKeyConstraint
from db.database import Base

class Shape(Base):
    __tablename__ = "shapes"
    
    shape_id = Column(String, primary_key=True)
    shape_pt_sequence = Column(Integer, primary_key=True)
    snapshot_id = Column(String,primary_key=True)
    
    shape_pt_lat = Column(Float)  
    shape_pt_lon = Column(Float)  
    shape_dist_traveled = Column(String)  
    
    __table_args__ = (
        PrimaryKeyConstraint('shape_id', 'shape_pt_sequence', 'snapshot_id'),
    )