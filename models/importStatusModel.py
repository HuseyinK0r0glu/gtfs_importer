from sqlalchemy import Column , String ,Integer , DateTime , Text , Enum
from db.database import Base
from datetime import datetime
from enums import importStatusEnum

class importStatus(Base):
    __tablename__ = "import_status"

    id = Column(String,primary_key=True)
    snapshot_id = Column(String, nullable=False)
    status = Column(Enum(importStatusEnum), nullable=False, default=importStatusEnum.PENDING)
    task_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(Text, nullable=True) 
    error_message = Column(Text, nullable=True)

