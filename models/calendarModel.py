from sqlalchemy import Column , String , Integer , PrimaryKeyConstraint
from db.database import Base

class Calendar(Base):
    __tablename__ = "calendar"

    service_id = Column(String,primary_key=True)
    snapshot_id = Column(String,primary_key=True)

    monday = Column(Integer)
    tuesday = Column(Integer)
    wednesday = Column(Integer)
    thursday = Column(Integer)
    friday = Column(Integer)
    saturday = Column(Integer)
    sunday = Column(Integer)
    start_date = Column(String)
    end_date = Column(String)

    # Define the composite primary key constraint
    __table_args__ = (
        PrimaryKeyConstraint('service_id', 'snapshot_id'),
    ) 

