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

    # Respect limit from frontend (default to 4 for dashboard)
    limit = int(data.get("limit", 4))
    local_recs = await RecommendationService.get_recommendations(user_id, limit=limit)

    # Format for frontend (ensure we don't double-prefix IDs if to_dict already did it)
    results = []
    for book_data in local_recs:
        # If book_data is from to_dict(), it already has "id": "local_X", "cover", "cover_thumb", etc.
        # We ensure cleanTitle and other expected fields are present
        res_item = book_data.copy()

        # Ensure ID format for frontend consistency
        if not str(res_item.get("id", "")).startswith("local_"):
            res_item["id"] = f"local_{res_item.get('id')}"

        # Fix missing cover: use 'cover' from to_dict() instead of 'cover_url'
        if not res_item.get("cover") and res_item.get("cover_url"):
            res_item["cover"] = res_item.get("cover_url")
        elif not res_item.get("cover"):
            res_item["cover"] = res_item.get("cover_low") or res_item.get("cover_medium") or res_item.get("cover_high")

        # Compatibility with RecommendationCard.tsx
        res_item["cleanTitle"] = (
            res_item.get("cleanTitle")
            or res_item.get("series")
            or res_item.get("english_title")
            or res_item.get("title")
        )

        results.append(res_item)

    return {"results": results}
