from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User
from services.library_service import LibraryService

from .auth import get_current_user, get_db

router = APIRouter(prefix="/library", tags=["library"])


class SeriesModel(BaseModel):
    id: str
    name: str
    author: str | None
    description: str | None
    cover_url: str | None


class BookModel(BaseModel):
    id: str
    title: str
    author: str | None
    volume: float | None


@router.get("/search", response_model=list[SeriesModel])
async def search_series(
    q: str = Query("", min_length=0),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[User, Depends(get_current_user)] = None,
):
    """
    Search endpoint compatible with the Mini App's gallery.
    """
    library_service = LibraryService(db)
    res = await library_service.search_series(q, page=page, items_per_page=limit)

    # Adapt results from LibraryService to our Pydantic model
    # Note: search_series returns a dict with 'results' and 'totalItems'
    items = []
    for s in res.get("results", []):
        items.append(
            SeriesModel(
                id=s.get("id") or s.get("series_hash"),
                name=s.get("name") or s.get("title"),
                author=s.get("author"),
                description=s.get("description"),
                cover_url=s.get("coverUrl") or s.get("cover_medium"),
            )
        )

    return items


@router.get("/series/{series_id}", response_model=SeriesModel)
async def get_series_detail(
    series_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Obtiene los detalles de una serie específica."""
    library_service = LibraryService(db)
    series = await library_service.get_series_details(series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Serie no encontrada")

    return SeriesModel(
        id=series.id, name=series.name, author=series.author, description=series.description, cover_url=series.cover_url
    )


@router.get("/series/{series_id}/books", response_model=list[BookModel])
async def get_series_books(
    series_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Retorna los libros/volúmenes pertenecientes a una serie."""
    library_service = LibraryService(db)
    books = await library_service.get_books_by_series(series_id)

    return [BookModel(id=b.id, title=b.title, author=b.author, volume=b.volume) for b in books]
