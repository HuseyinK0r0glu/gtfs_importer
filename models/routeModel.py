from sqlalchemy import Column , String , Integer , PrimaryKeyConstraint
from db.database import Base

class Route(Base):
    __tablename__ = "routes"

    route_id = Column(String,primary_key=True)
    snapshot_id = Column(String,primary_key=True)

    agency_id = Column(String)
    route_short_name = Column(String)
    route_long_name = Column(String)
    route_desc = Column(String)
    route_type = Column(String)
    route_url = Column(String)
    route_color = Column(String)
    route_text_color = Column(String)

    # Define the composite primary key constraint
    __table_args__ = (
        PrimaryKeyConstraint('route_id', 'snapshot_id'),
    ) 
