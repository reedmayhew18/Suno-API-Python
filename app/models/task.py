"""
SQLAlchemy model for Task entity.
"""
from sqlalchemy import Column, Integer, BigInteger, String, JSON
from app.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), unique=True, index=True, nullable=False)
    action = Column(String(40), index=True, nullable=False)
    status = Column(String(20), index=True, nullable=False, default="NOT_START")
    fail_reason = Column(String, nullable=True)
    submit_time = Column(BigInteger, index=True, default=0)
    start_time = Column(BigInteger, index=True, default=0)
    finish_time = Column(BigInteger, index=True, default=0)
    search_item = Column(String(100), index=True, nullable=True)
    data = Column(JSON, nullable=True)
    
    def to_dict(self):
        """
        Serialize the Task model to a dict of column names to values.
        """
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}