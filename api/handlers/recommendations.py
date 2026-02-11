import logging
from typing import Any

from services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)


async def handle_recommendations(data: dict[str, Any], user_data: dict[str, Any]):
    """Devuelve recomendaciones personalizadas (Beta exclusiva Staff)."""

    user_id = user_data.get("user_id")
    settings = user_data.get("settings", {})

    # Check both camelCase and snake_case for backward compatibility
    show_recs = settings.get("showRecommendations")
    if show_recs is None:
        show_recs = settings.get("show_recommendations", True)

    try:
        # Ensure only staff or higher, or explicitly enabled via config/flag?
        # The docstring says "Beta exclusiva Staff", but code might have changed.
        # Original code didn't check level explicitly inside function, relies on caller or just returns limited?
        # Let's check original implementation in miniapp_handlers.py lines 341-391.

        # Original logic:
        # if show_recs is False: return []
        # recs = await RecommendationService.get_recommendations(user_id)
        # ... processing ...
        pass
    except Exception as e:
        logger.error(f"Error in recommendation handler: {e}")
        return {"results": []}

    if not show_recs:
        return {"results": []}

    local_recs = await RecommendationService.get_recommendations(user_id, limit=10)

    # Format for frontend
    results = []
    for book_data in local_recs:
        # book_data is a dictionary from RecommendationService
        numeric_id = book_data.get("id")
        results.append(
            {
                "id": f"local_{numeric_id}",
                "cover": book_data.get("cover_url"),
                "title": book_data.get("title"),
                "author": book_data.get("author"),
                "downloadUrl": f"local_{numeric_id}",
                "is_folder": False,
                "series": book_data.get("series"),
                "seriesIndex": book_data.get("seriesIndex"),
                "cleanTitle": book_data.get("clean_title")
                or book_data.get("series")
                or book_data.get("title"),
                "rating_average": book_data.get("rating_average", 0),
                "book_type": book_data.get("book_type"),
            }
        )
    return {"results": results}
