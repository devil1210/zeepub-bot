import logging
from typing import Any

from services.library_service import LibraryService

logger = logging.getLogger(__name__)


async def handle_search(data: dict[str, Any], user_data: dict[str, Any]):
    """Busca libros en la base de datos local."""
    query = data.get("query")
    page = data.get("page", 1)
    search_type = data.get("type", "todos")
    sort = data.get("sort", "a-z")

    return await LibraryService.search_series(query or "", page=page, search_type=search_type, sort_by=sort)
