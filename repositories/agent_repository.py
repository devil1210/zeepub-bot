import json
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select

from models.agent_models import AgentExecution

from .base_repository import BaseRepository


class AgentRepository(BaseRepository[AgentExecution]):
    """
    CRUD for AI Agent Execution Logs.
    """

    def __init__(self, session=None, db_manager=None):
        super().__init__(AgentExecution, session=session, db_manager=db_manager)

    async def log_execution(
        self,
        func_name: str,
        status: str,
        duration: float | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentExecution:
        """
        Logs a single execution run of an AI agent/function.
        """
        metadata_str = json.dumps(metadata) if metadata else None
        execution = AgentExecution(
            func_name=func_name, status=status, duration=duration, error=error, metadata_json=metadata_str
        )
        async with self._get_session() as session:
            session.add(execution)
            if self.injected_session is None:
                await session.commit()
                await session.refresh(execution)
            return execution

    async def get_recent_executions(self, func_name: str, limit: int = 10) -> Sequence[AgentExecution]:
        stmt = (
            select(AgentExecution)
            .where(AgentExecution.func_name == func_name)
            .order_by(AgentExecution.created_at.desc())
            .limit(limit)
        )
        async with self._get_session() as session:
            result = await session.execute(stmt)
            return result.scalars().all()
