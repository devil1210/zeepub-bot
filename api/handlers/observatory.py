import logging
from typing import Any

from sqlalchemy import text

from api.handlers.helpers import check_staff
from core.db_manager_pg import pg_manager

logger = logging.getLogger(__name__)


async def handle_observatory_overview(data: dict[str, Any], user_data: dict[str, Any]):
    """Retorna el resumen general del sistema para el observatorio."""
    check_staff(user_data)

    result = {
        "totalBooks": 0,
        "totalUsers": 0,
        "downloadsToday": 0,
        "pendingPublications": 0,
        "activityLast7Days": [],
        "usersByLevel": [],
    }

    try:
        async with pg_manager.get_session() as session:
            total_books = (await session.execute(text("SELECT COUNT(*) FROM local_books"))).scalar() or 0
            total_users = (await session.execute(text("SELECT COUNT(*) FROM users"))).scalar() or 0

            downloads_today = (
                await session.execute(text("SELECT COUNT(*) FROM download_history WHERE downloaded_at >= CURRENT_DATE"))
            ).scalar() or 0

            pending_pubs = (
                await session.execute(text("SELECT COUNT(*) FROM publication_queue WHERE status = 'pending'"))
            ).scalar() or 0

            result["totalBooks"] = total_books
            result["totalUsers"] = total_users
            result["downloadsToday"] = downloads_today
            result["pendingPublications"] = pending_pubs

            activity = await session.execute(
                text("""
                    SELECT
                        DATE(downloaded_at) as fecha,
                        COUNT(*) as descargas
                    FROM download_history
                    WHERE downloaded_at >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY DATE(downloaded_at)
                    ORDER BY fecha
                """)
            )
            activity_rows = activity.fetchall()
            result["activityLast7Days"] = [{"date": str(row[0]), "downloads": row[1]} for row in activity_rows]

            levels = await session.execute(
                text("""
                    SELECT
                        COALESCE(ul.name, 'Sin nivel') as nivel,
                        COUNT(u.id) as usuarios
                    FROM users u
                    LEFT JOIN user_levels ul ON u.level_id = ul.id
                    GROUP BY ul.name
                    ORDER BY usuarios DESC
                """)
            )
            level_rows = levels.fetchall()
            result["usersByLevel"] = [{"level": row[0], "count": row[1]} for row in level_rows]

    except Exception as e:
        logger.error(f"Error fetching observatory overview: {e}")

    return {"success": True, **result}


async def handle_observatory_executions(data: dict[str, Any], user_data: dict[str, Any]):
    """Retorna las ejecuciones de agentes para el observatorio."""
    check_staff(user_data)

    hours = data.get("hours", 24)
    status_filter = data.get("status", None)

    result = {
        "executions": [],
        "stats": {
            "success": 0,
            "error": 0,
            "avgDuration": 0,
        },
    }

    try:
        async with pg_manager.get_session() as session:
            query = """
                SELECT
                    id, timestamp, func_name, status, duration, error
                FROM agent_executions
                WHERE timestamp >= NOW() - INTERVAL :hours_str
            """
            params = {"hours_str": f"{hours} hours"}

            if status_filter:
                query += " AND status = :status"
                params["status"] = status_filter

            query += " ORDER BY timestamp DESC LIMIT 200"

            rows = await session.execute(text(query), params)
            executions = rows.fetchall()

            result["executions"] = [
                {
                    "id": row[0],
                    "timestamp": row[1].isoformat() if row[1] else None,
                    "funcName": row[2],
                    "status": row[3],
                    "duration": float(row[4]) if row[4] else None,
                    "error": row[5],
                }
                for row in executions
            ]

            success_count = sum(1 for e in result["executions"] if e["status"] == "success")
            error_count = sum(1 for e in result["executions"] if e["status"] == "error")
            durations = [e["duration"] for e in result["executions"] if e["duration"]]
            avg_duration = sum(durations) / len(durations) if durations else 0

            result["stats"]["success"] = success_count
            result["stats"]["error"] = error_count
            result["stats"]["avgDuration"] = round(avg_duration, 2)

    except Exception as e:
        logger.error(f"Error fetching observatory executions: {e}")

    return {"success": True, **result}


async def handle_observatory_publications(data: dict[str, Any], user_data: dict[str, Any]):
    """Retorna el estado del sistema de publicaciones."""
    check_staff(user_data)

    result = {
        "queue": {"pending": 0, "publishing": 0, "sent": 0, "failed": 0},
        "recentQueue": [],
        "channels": [],
        "templates": [],
        "discoveredChats": [],
    }

    try:
        async with pg_manager.get_session() as session:
            pending = (
                await session.execute(text("SELECT COUNT(*) FROM publication_queue WHERE status = 'pending'"))
            ).scalar() or 0
            publishing = (
                await session.execute(text("SELECT COUNT(*) FROM publication_queue WHERE status = 'publishing'"))
            ).scalar() or 0
            sent = (
                await session.execute(text("SELECT COUNT(*) FROM publication_queue WHERE status = 'sent'"))
            ).scalar() or 0
            failed = (
                await session.execute(text("SELECT COUNT(*) FROM publication_queue WHERE status = 'failed'"))
            ).scalar() or 0

            result["queue"]["pending"] = pending
            result["queue"]["publishing"] = publishing
            result["queue"]["sent"] = sent
            result["queue"]["failed"] = failed

            recent = await session.execute(
                text("""
                    SELECT
                        pq.id, pq.book_hash, pc.name as canal, pc.platform,
                        pq.scheduled_for, pq.status, pq.published_at, pq.error_message
                    FROM publication_queue pq
                    LEFT JOIN publication_channels pc ON pq.channel_id = pc.id
                    ORDER BY pq.scheduled_for DESC
                    LIMIT 50
                """)
            )
            recent_rows = recent.fetchall()
            result["recentQueue"] = [
                {
                    "id": row[0],
                    "bookHash": row[1],
                    "channel": row[2],
                    "platform": row[3],
                    "scheduledFor": row[4].isoformat() if row[4] else None,
                    "status": row[5],
                    "publishedAt": row[6].isoformat() if row[6] else None,
                    "errorMessage": row[7],
                }
                for row in recent_rows
            ]

            channels = await session.execute(
                text("""
                    SELECT id, name, platform, target_id, is_active, is_favorite, created_at
                    FROM publication_channels
                    ORDER BY is_favorite DESC, name ASC
                """)
            )
            channel_rows = channels.fetchall()
            result["channels"] = [
                {
                    "id": row[0],
                    "name": row[1],
                    "platform": row[2],
                    "targetId": row[3],
                    "isActive": row[4],
                    "isFavorite": row[5],
                    "createdAt": row[6].isoformat() if row[6] else None,
                }
                for row in channel_rows
            ]

            templates = await session.execute(
                text("SELECT id, name, platform, created_at FROM publication_templates ORDER BY created_at DESC")
            )
            template_rows = templates.fetchall()
            result["templates"] = [
                {
                    "id": row[0],
                    "name": row[1],
                    "platform": row[2],
                    "createdAt": row[3].isoformat() if row[3] else None,
                }
                for row in template_rows
            ]

            discovered = await session.execute(
                text("""
                    SELECT chat_id, title, type, member_count, last_seen_at
                    FROM discovered_chats
                    ORDER BY last_seen_at DESC
                    LIMIT 20
                """)
            )
            discovered_rows = discovered.fetchall()
            result["discoveredChats"] = [
                {
                    "chatId": row[0],
                    "title": row[1],
                    "type": row[2],
                    "memberCount": row[3],
                    "lastSeenAt": row[4].isoformat() if row[4] else None,
                }
                for row in discovered_rows
            ]

    except Exception as e:
        logger.error(f"Error fetching observatory publications: {e}")

    return {"success": True, **result}


async def handle_observatory_metrics(data: dict[str, Any], user_data: dict[str, Any]):
    """Retorna las métricas completas del sistema."""
    check_staff(user_data)

    result = {
        "library": {"totalBooks": 0, "totalSeries": 0, "totalRatings": 0, "avgRating": 0},
        "downloads": {"total": 0, "today": 0, "week": 0},
        "trend": [],
        "topBooks": [],
    }

    try:
        async with pg_manager.get_session() as session:
            total_books = (await session.execute(text("SELECT COUNT(*) FROM local_books"))).scalar() or 0
            total_series = (await session.execute(text("SELECT COUNT(*) FROM series_metadata"))).scalar() or 0
            total_ratings = (await session.execute(text("SELECT COUNT(*) FROM user_ratings"))).scalar() or 0
            avg_rating = (await session.execute(text("SELECT AVG(rating) FROM user_ratings"))).scalar() or 0

            result["library"]["totalBooks"] = total_books
            result["library"]["totalSeries"] = total_series
            result["library"]["totalRatings"] = total_ratings
            result["library"]["avgRating"] = round(float(avg_rating), 1) if avg_rating else 0

            total_downloads = (await session.execute(text("SELECT COUNT(*) FROM download_history"))).scalar() or 0
            today_downloads = (
                await session.execute(text("SELECT COUNT(*) FROM download_history WHERE downloaded_at >= CURRENT_DATE"))
            ).scalar() or 0
            week_downloads = (
                await session.execute(
                    text(
                        "SELECT COUNT(*) FROM download_history WHERE downloaded_at >= CURRENT_DATE - INTERVAL '7 days'"
                    )
                )
            ).scalar() or 0

            result["downloads"]["total"] = total_downloads
            result["downloads"]["today"] = today_downloads
            result["downloads"]["week"] = week_downloads

            trend = await session.execute(
                text("""
                    SELECT
                        DATE(downloaded_at) as fecha,
                        COUNT(*) as descargas
                    FROM download_history
                    WHERE downloaded_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE(downloaded_at)
                    ORDER BY fecha
                """)
            )
            trend_rows = trend.fetchall()
            result["trend"] = [{"date": str(row[0]), "downloads": row[1]} for row in trend_rows]

            top = await session.execute(
                text("""
                    SELECT
                        COALESCE(lb.title, dh.title, 'Desconocido') as titulo,
                        COUNT(*) as descargas
                    FROM download_history dh
                    LEFT JOIN local_books lb ON dh.book_hash = lb.book_hash
                    GROUP BY COALESCE(lb.title, dh.title)
                    ORDER BY descargas DESC
                    LIMIT 10
                """)
            )
            top_rows = top.fetchall()
            result["topBooks"] = [{"title": row[0], "downloads": row[1]} for row in top_rows]

    except Exception as e:
        logger.error(f"Error fetching observatory metrics: {e}")

    return {"success": True, **result}
