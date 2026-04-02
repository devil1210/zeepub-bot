# src/api/routers/bridge_router.py
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from src.core.db import db_manager
from src.models.library import LocalBook, SeriesMetadata

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bridge", tags=["SPbot Bridge v2"])

@router.get("/status")
async def bridge_status():
    """Simple check for SPbot connection."""
    return {"status": "connected", "bridge_version": "2.0"}

@router.get("/books")
async def list_books(
    q: Optional[str] = Query(None, min_length=3),
    limit: int = 50,
    session: AsyncSession = Depends(db_manager.get_session)
):
    """Lista libros con búsqueda opcional."""
    stmt = select(LocalBook).limit(limit)
    if q:
        stmt = stmt.where(LocalBook.title.ilike(f"%{q}%"))
    
    result = await session.execute(stmt)
    books = result.scalars().all()
    
    return [
        {
            "hash": b.hash,
            "title": b.title,
            "volume": float(b.volume_number),
            "uncensored": b.is_uncensored,
            "color": b.color_mode,
            "series_id": str(b.series_id) if b.series_id else None
        } for b in books
    ]

@router.get("/series")
async def list_series(
    session: AsyncSession = Depends(db_manager.get_session)
):
    """Lista todas las series disponibles."""
    result = await session.execute(select(SeriesMetadata).order_by(SeriesMetadata.title))
    series_list = result.scalars().all()
    
    return [
        {
            "id": str(s.id),
            "title": s.title,
            "hash": s.hash,
            "type": s.book_type,
            "book_count": len(s.books)
        } for s in series_list
    ]

@router.get("/book/{book_hash}")
async def get_book_details(
    book_hash: str,
    session: AsyncSession = Depends(db_manager.get_session)
):
    """Obtiene detalles completos de un libro por su hash."""
    stmt = select(LocalBook).where(LocalBook.hash == book_hash)
    result = await session.execute(stmt)
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado en la biblioteca Nexus.")
    
    return {
        "title": book.title,
        "hash": book.hash,
        "path": book.file_path,
        "series": book.series.title if book.series else "Standalone",
        "format_details": {
            "uncensored": book.is_uncensored,
            "color_mode": book.color_mode
        }
    }
