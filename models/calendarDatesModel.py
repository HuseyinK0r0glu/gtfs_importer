from sqlalchemy import Column , String ,Integer , PrimaryKeyConstraint
from db.database import Base

class CalendarDates(Base):
    __tablename__ = "calendar_dates"

    service_id = Column(String,primary_key=True)
    snapshot_id = Column(String,primary_key=True)

    date = Column(String)
    exception_type = Column(Integer)

    # Define the composite primary key constraint
    __table_args__ = (
        PrimaryKeyConstraint('service_id', 'snapshot_id'),
    ) 
