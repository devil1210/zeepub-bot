from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import TimestampedBase


class AgentExecution(TimestampedBase):
    """
    V4 Agent Execution logs tracking AI Swarm decisions.
    """

    __tablename__ = "agent_executions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Context
    func_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    # Metrics
    duration: Mapped[float | None] = mapped_column(Float)
    error: Mapped[str | None] = mapped_column(Text)

    # Output/Parameters
    metadata_json: Mapped[str | None] = mapped_column(Text)

    def __repr__(self):
        return f"<AgentExecution(func='{self.func_name}', status='{self.status}')>"
