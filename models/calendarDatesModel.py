from sqlalchemy import Column , String ,Integer , PrimaryKeyConstraint
from db.database import Base

class CalendarDate(Base):
    __tablename__ = "calendar_dates"

    service_id = Column(String, primary_key=True)
    date = Column(String, primary_key=True)  
    exception_type = Column(Integer, primary_key=True)  
    snapshot_id = Column(String, primary_key=True)

    # Define the composite primary key constraint
    __table_args__ = (
        PrimaryKeyConstraint('service_id', 'date', 'exception_type', 'snapshot_id'),
    )