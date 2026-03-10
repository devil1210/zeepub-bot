import json
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent_models import AgentExecution

from .base_repository import BaseRepository


class AgentRepository(BaseRepository[AgentExecution]):
    """
    CRUD for AI Agent Execution Logs.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(AgentExecution, session)

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
        self.session.add(execution)
        await self.session.commit()
        await self.session.refresh(execution)
        return execution

    async def get_recent_executions(self, func_name: str, limit: int = 10) -> Sequence[AgentExecution]:
        stmt = (
            select(AgentExecution)
            .where(AgentExecution.func_name == func_name)
            .order_by(AgentExecution.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
