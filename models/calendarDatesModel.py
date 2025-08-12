from sqlalchemy import Column , String ,Integer
from db.database import Base

class CalendarDates(Base):
    __tablename__ = "calendar_dates"

    service_id = Column(String,primary_key=True)
    date = Column(String)
    exception_type = Column(Integer)

