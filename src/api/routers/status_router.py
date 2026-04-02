# src/api/routers/status_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import psutil
import time
from datetime import datetime
from src.core.db import db_manager
from src.models.library import LocalBook, MetadataProposal

router = APIRouter(prefix="/api/status", tags=["Status"])

START_TIME = time.time()

@router.get("/")
async def get_status():
    """Métricas de sistema y base de datos en tiempo real."""
    
    # 1. Métricas de Sistema
    process = psutil.Process()
    mem_info = process.memory_info()
    
    # 2. Métricas de Base de Datos (Atomic Query)
    async with db_manager.session_scope() as session:
        # Contar total de libros
        total_books_res = await session.execute(select(func.count(LocalBook.id)))
        total_books = total_books_res.scalar() or 0
        
        # Contar propuestas de IA pendientes
        proposals_res = await session.execute(select(func.count(MetadataProposal.id)))
        pending_ia = proposals_res.scalar() or 0

    return {
        "status": "online",
        "uptime": f"{int(time.time() - START_TIME)}s",
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_usage_percent": psutil.cpu_percent(interval=None),
            "ram_usage_mb": round(mem_info.rss / (1024 * 1024), 2),
            "threads": process.num_threads()
        },
        "library": {
            "total_books": total_books,
            "pending_ai_corrections": pending_ia,
            "engine_version": "Nexus-Skeleton v2.0"
        }
    }
