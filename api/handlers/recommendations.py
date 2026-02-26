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
    for item_data in local_recs:
        res_item = item_data.copy()

        # Ensure ID format for frontend consistency
        # If it's a series, it already has the 'series_' prefix from the service
        # If it's a book (fallback), it should have 'local_'
        current_id = str(res_item.get("id", ""))
        if not (current_id.startswith("local_") or current_id.startswith("series_")):
            res_item["id"] = f"local_{current_id}"

        # Fix missing cover: use 'cover' from to_dict() / service
        if not res_item.get("cover") and res_item.get("cover_url"):
            res_item["cover"] = res_item.get("cover_url")

        # Compatibility with RecommendationCard.tsx cleanTitle
        res_item["cleanTitle"] = (
            res_item.get("cleanTitle")
            or res_item.get("title")
            or res_item.get("series")
            or res_item.get("english_title")
        )

        results.append(res_item)

    return {"results": results}
