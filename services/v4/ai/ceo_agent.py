"""
services/v4/ai/ceo_agent.py
-----------------------------
CEOAgent V4: Orquestador de alto nivel.
Decide qué subagente ejecutar según el tipo de tarea.
"""

from __future__ import annotations

import logging
from typing import Any


class CEOAgent:
    """
    Orquestador del sistema de agentes V4.
    Un único punto de entrada para tareas de IA; delega al swarm correcto.

    Tareas soportadas:
      - "analyze_book"      → MetadataSwarm.analyze_book
      - "check_duplicates"  → MetadataSwarm.check_duplicates
      - "match_series"      → MetadataSwarm.match_existing_series
      - "db_audit"          → DBSupervisorAgent.run_audit
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._metadata_swarm = None
        self._db_supervisor = None

    # ------------------------------------------------------------------ #
    #  Entry point                                                         #
    # ------------------------------------------------------------------ #

    async def execute_task(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Enruta la tarea al subagente correcto y devuelve su resultado.
        """
        self.logger.info(f"[CEO] Tarea recibida: {task_type}")

        try:
            if task_type == "analyze_book":
                return await self._run_analyze_book(payload)

            if task_type == "check_duplicates":
                return await self._run_check_duplicates(payload)

            if task_type == "match_series":
                return await self._run_match_series(payload)

            if task_type == "db_audit":
                return await self._run_db_audit(payload)

            self.logger.warning(f"[CEO] Tarea desconocida: {task_type}")
            return {"status": "error", "reason": f"Unknown task_type: {task_type}"}

        except Exception as e:
            self.logger.error(f"[CEO] Error en {task_type}: {e}")
            return {"status": "error", "reason": str(e)}

    # ------------------------------------------------------------------ #
    #  Delegates                                                           #
    # ------------------------------------------------------------------ #

    async def _run_analyze_book(self, payload: dict) -> dict:
        swarm = self._get_metadata_swarm()
        proposal = await swarm.analyze_book(payload)
        return {"status": "ok", "proposal": proposal.__dict__}

    async def _run_check_duplicates(self, payload: dict) -> dict:
        swarm = self._get_metadata_swarm()
        report = await swarm.check_duplicates(payload.get("series_list", []))
        return {
            "status": "ok",
            "has_duplicates": report.has_duplicates,
            "pairs": report.pairs,
            "total_checked": report.total_checked,
        }

    async def _run_match_series(self, payload: dict) -> dict:
        from services.v4.ai.metadata_swarm import BookProposal

        swarm = self._get_metadata_swarm()
        proposal_dict = payload.get("proposal", {})
        proposal = BookProposal(**{k: v for k, v in proposal_dict.items() if k in BookProposal.__dataclass_fields__})
        match = await swarm.match_existing_series(proposal, payload.get("candidates", []))
        return {"status": "ok", "match": match}

    async def _run_db_audit(self, payload: dict) -> dict:
        from services.v4.ai.db_supervisor import DBSupervisorAgent

        if not self._db_supervisor:
            self._db_supervisor = DBSupervisorAgent()
        result = await self._db_supervisor.run_audit(payload)
        return {"status": "ok", "result": result}

    # ------------------------------------------------------------------ #
    #  Lazy init helpers                                                   #
    # ------------------------------------------------------------------ #

    def _get_metadata_swarm(self):
        if not self._metadata_swarm:
            from services.v4.ai.metadata_swarm import MetadataSwarm

            self._metadata_swarm = MetadataSwarm()
        return self._metadata_swarm
