from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime
from .base import Base

class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    func_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    duration = Column(Float)
    error = Column(Text)
    metadata_json = Column(Text) # metadata is a reserved word in some contexts, using metadata_json

    def __repr__(self):
        return f"<AgentExecution(func='{self.func_name}', status='{self.status}')>"
