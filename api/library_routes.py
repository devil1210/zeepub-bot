from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from utils.library_db import get_session, COVERS_DIR
from models.library_models import LocalBook, LibrarySource
from api.deps import require_mini_app_access, require_admin

router = APIRouter(tags=["library"])

@router.get("/api/library/sources")
async def get_sources(
    user_data: dict = Depends(require_mini_app_access)
):
    """
    Lista todas las fuentes de biblioteca configuradas.
    """
    session = get_session()
    try:
        sources = session.query(LibrarySource).all()
        return [
            {
                "id": s.id,
                "name": s.name,
                "path": s.path,
                "lastScanned": s.last_scanned.isoformat() if s.last_scanned else None
            } for s in sources
        ]
    finally:
        session.close()

@router.get("/api/library/search")
async def search_local_books(
    q: str = Query(..., min_length=1),
    source_id: Optional[int] = None,
    user_data: dict = Depends(require_mini_app_access)
):
    """
    Busca libros en la base de datos local.
    """
    session = get_session()
    try:
        query = session.query(LocalBook)
        
        if source_id:
            query = query.filter(LocalBook.source_id == source_id)
            
        # Búsqueda simple por ahora (LIKE)
        # TODO: Implementar FTS (Full Text Search) en Phase 5
        search_filter = f"%{q}%"
        results = query.filter(
            (LocalBook.title.ilike(search_filter)) |
            (LocalBook.author.ilike(search_filter)) |
            (LocalBook.series.ilike(search_filter))
        ).limit(50).all()
        
        return [b.to_dict() for b in results]
    finally:
        session.close()

@router.get("/api/library/books/{book_id}")
async def get_book_detail(
    book_id: str,
    user_data: dict = Depends(require_mini_app_access)
):
    """
    Retorna el detalle de un libro específico (con o sin prefijo local_).
    """
    session = get_session()
    try:
        clean_id = book_id.replace("local_", "")
        book = session.query(LocalBook).filter(LocalBook.id == int(clean_id)).first()
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        return book.to_dict()
    finally:
        session.close()

@router.get("/api/library/catalog")
async def get_catalog(
    source_id: Optional[int] = None,
    folder: Optional[str] = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    user_data: dict = Depends(require_mini_app_access)
):
    """
    Navega por la librería local simulando carpetas.
    Soporta paginación y ordenamiento (carpetas primero, luego libros).
    """
    session = get_session()
    try:
        if not source_id:
            # Si no hay source_id, listar fuentes como carpetas raíz
            sources = session.query(LibrarySource).all()
            items = [
                {
                    "id": f"source_{s.id}",
                    "title": s.name,
                    "is_folder": True,
                    "folder_path": "",
                    "source_id": s.id
                } for s in sources
            ]
            # No paginamos las fuentes (suelen ser pocas)
            return {
                "items": items,
                "total": len(items),
                "page": 1,
                "totalPages": 1
            }
        
        source = session.query(LibrarySource).filter(LibrarySource.id == source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Fuente no encontrada")

        # Buscar todos los libros en esta fuente
        books = session.query(LocalBook).filter(LocalBook.source_id == source_id).all()
        
        books_in_folder = []
        folders_map = {} # f_name -> representative_book (dict)
        
        # Sort books by volume/title to get a good representative (like Vol 1)
        sorted_books = sorted(books, key=lambda x: (x.series or "", x.volume or 0, x.title.lower()))

        base_path = source.path.rstrip("/")
        if folder:
            current_lookup = os.path.join(base_path, folder.strip("/"))
        else:
            current_lookup = base_path

        for b in sorted_books:
            b_dict = b.to_dict()
            rel_path = os.path.relpath(os.path.dirname(b.filepath), current_lookup)
            
            if rel_path == ".":
                # Libro en la carpeta actual
                books_in_folder.append(b_dict)
            elif not rel_path.startswith(".."):
                # Carpeta hija
                subfolder = rel_path.split(os.sep)[0]
                if subfolder not in folders_map:
                    folders_map[subfolder] = {
                        "representative": b_dict,
                        "all_series": {b.series} if b.series else set()
                    }
                else:
                    if b.series:
                        folders_map[subfolder]["all_series"].add(b.series)
        
        # Convertir carpetas a objetos con metadatos de su "representante"
        folders_list = []
        for f_name, meta in sorted(folders_map.items(), key=lambda x: x[0].lower()):
            rep = meta["representative"]
            # Si todos los libros en la carpeta pertenecen a una misma serie, usar el nombre de la serie como título
            display_title = f_name
            if len(meta["all_series"]) == 1:
                series_name = list(meta["all_series"])[0]
                if series_name:
                    display_title = series_name

            folders_list.append({
                "id": f"dir_{source_id}_{f_name}",
                "title": display_title,
                "is_folder": True,
                "folder_path": os.path.join(folder, f_name) if folder else f_name,
                "source_id": source_id,
                # Representative metadata
                "cover": rep.get("cover"),
                "author": rep.get("author"),
                "tags": rep.get("tags"),
                "series": rep.get("series")
            })
            
        # Ordenar libros
        books_in_folder.sort(key=lambda x: x["title"].lower())
        
        # Combinar: Carpetas primero, luego libros
        all_items = folders_list + books_in_folder
        total = len(all_items)
        
        # Paginación
        start = (page - 1) * page_size
        end = start + page_size
        paged_items = all_items[start:end]
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": paged_items,
            "total": total,
            "page": page,
            "totalPages": total_pages
        }
    finally:
        session.close()

# Las portadas se servirán vía StaticFiles montado en api/main.py
