from sqlalchemy import Column, Integer, String , PrimaryKeyConstraint
from db.database import Base

class Agency(Base):
    __tablename__ = "agency"
    
    agency_id = Column(String, primary_key=True)
    snapshot_id = Column(String, primary_key=True)

    agency_name = Column(String)
    agency_url = Column(String)
    agency_timezone = Column(String)
    agency_lang = Column(String)
    agency_phone = Column(String)
    agency_fare_url = Column(String)
    agency_email = Column(String)

    # Define the composite primary key constraint
    __table_args__ = (
        PrimaryKeyConstraint('agency_id', 'snapshot_id'),
    ) 