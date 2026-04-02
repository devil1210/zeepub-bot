import logging
from datetime import datetime

from services.maintenance.base import MaintenanceTool
from services.maintenance.cover_tool import CoverRefreshTool
from services.maintenance.enrich_tool import MetadataEnrichmentTool
from services.maintenance.integrity_tool import DatabaseIntegrityTool
from services.maintenance.slug_tool import SlugRecalculateTool

logger = logging.getLogger(__name__)


class MaintenanceOrchestrator:
    _tools: dict[str, MaintenanceTool] = {
        "cover_refresh": CoverRefreshTool(),
        "slug_recalculate": SlugRecalculateTool(),
        "metadata_enrich": MetadataEnrichmentTool(),
        "db_integrity": DatabaseIntegrityTool(),
    }

    _is_running = False
    _current_task = None
    _status = {
        "status": "idle",
        "tool": None,
        "progress": 0,
        "total": 0,
        "message": "",
        "results": None,
        "last_run": None,
        "error": None,
    }

    @classmethod
    async def run_tool(cls, tool_key: str, **kwargs):
        if cls._is_running:
            return {"success": False, "message": "Ya hay una tarea de mantenimiento en ejecución."}

        tool = cls._tools.get(tool_key)
        if not tool:
            return {"success": False, "message": f"Herramienta no encontrada: {tool_key}"}

        cls._is_running = True
        cls._status.update(
            {
                "status": "running",
                "tool": tool_key,
                "progress": 0,
                "total": 0,
                "message": f"Iniciando {tool.name}...",
                "results": None,
                "error": None,
            }
        )

        async def progress_cb(current, total, msg):
            cls._status["progress"] = current
            cls._status["total"] = total
            cls._status["message"] = msg

        try:
            results = await tool.run(progress_callback=progress_cb, **kwargs)
            cls._status.update(
                {
                    "status": "completed" if results.get("success") else "error",
                    "results": results,
                    "last_run": datetime.utcnow().isoformat(),
                    "error": results.get("error") if not results.get("success") else None,
                }
            )
            return results
        except Exception as e:
            logger.error(f"Error running maintenance tool {tool_key}: {e}")
            cls._status.update({"status": "error", "error": str(e), "last_run": datetime.utcnow().isoformat()})
            return {"success": False, "error": str(e)}
        finally:
            cls._is_running = False

    @classmethod
    def get_status(cls):
        return cls._status
