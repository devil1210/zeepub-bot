import logging
import time
from typing import Any

from sqlalchemy import or_, select, text

from api.handlers.helpers import check_staff
from core.db_manager_pg import pg_manager
from models.library_models import LocalBook

logger = logging.getLogger(__name__)


async def handle_admin_stats(data: dict[str, Any], user_data: dict[str, Any], request=None):
    """Calcula y devuelve estadísticas globales reales desde PostgreSQL para el Panel Admin."""
    check_staff(user_data)

    total_users = 0
    total_books = 0
    dls_24h = 0
    dls_prev_24h = 0
    users_7d = 0
    storage_gb = 0

    try:
        async with pg_manager.get_session() as session:
            # 1. Basic Counts
            total_users = (await session.execute(text("SELECT COUNT(*) FROM users"))).scalar() or 0
            total_books = (await session.execute(text("SELECT COUNT(*) FROM local_books"))).scalar() or 0
            users_7d = (
                await session.execute(
                    text("SELECT COUNT(*) FROM users WHERE created_at >= (CURRENT_TIMESTAMP - INTERVAL '7 days')")
                )
            ).scalar() or 0

            # 2. Storage
            res_size = await session.execute(text("SELECT SUM(file_size) FROM local_books"))
            total_bytes = res_size.scalar() or 0
            storage_gb = round(total_bytes / (1024**3), 2)

            # 3. Download Metrics
            dls_24h = (
                await session.execute(
                    text(
                        "SELECT COUNT(*) FROM download_history WHERE downloaded_at >= (CURRENT_TIMESTAMP - INTERVAL '1 day')"
                    )
                )
            ).scalar() or 0
            dls_prev_24h = (
                await session.execute(
                    text(
                        "SELECT COUNT(*) FROM download_history WHERE downloaded_at >= (CURRENT_TIMESTAMP - INTERVAL '2 days') AND downloaded_at < (CURRENT_TIMESTAMP - INTERVAL '1 day')"
                    )
                )
            ).scalar() or 0

            # 4. Revenue Estimation (Real from levels)
            cursor = await session.execute(
                text("""
                SELECT ul.price, COUNT(u.telegram_id)
                FROM user_levels ul
                LEFT JOIN users u ON u.level_id = ul.id
                GROUP BY ul.id, ul.price
            """)
            )
            tier_revenue = cursor.fetchall()
            total_revenue = sum((price or 0.0) * count for price, count in tier_revenue)
    except Exception as e:
        logger.error(f"Error fetching global stats from Postgres: {e}")
        total_revenue = 0

    # Calculate Uptime
    start_time = time.time()
    try:
        from api.main import app_state

        start_time = app_state.get("start_time", time.time())
    except ImportError:
        pass

    uptime_seconds = int(time.time() - start_time)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_text = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"

    # Active Sessions (via StateManager)
    from core.state_manager import state_manager

    active_sessions = len(state_manager.user_state)

    # 5. Popular Book (Last 30 days)
    popular_book = None
    try:
        async with pg_manager.get_session() as session:
            cursor = await session.execute(
                text("""
                SELECT title, clean_title, book_hash, COUNT(*) as dls
                FROM download_history
                WHERE downloaded_at >= NOW() - INTERVAL '30 days'
                GROUP BY book_hash, title, clean_title
                ORDER BY dls DESC
                LIMIT 1
            """)
            )
            row = cursor.fetchone()
            if row:
                p_title, p_clean_title, p_book_hash, p_dls = row
                popular_book = {
                    "title": p_clean_title or p_title,
                    "downloads": p_dls,
                    "author": "N/A",
                }
                stmt_lb = select(LocalBook).where(or_(LocalBook.book_hash == p_book_hash, LocalBook.title == p_title))
                lb_res = await session.execute(stmt_lb)
                lb = lb_res.scalar_one_or_none()
                if lb:
                    popular_book["author"] = lb.author
                    popular_book["cover"] = lb.cover_low
    except Exception as e:
        logger.error(f"Error fetching popular book: {e}")

    return {
        "revenue": round(total_revenue, 2),
        "activeSessions": active_sessions,
        "storageUsedGB": storage_gb,
        "storageTotalGB": 1000,
        "popularBook": popular_book,
        "growthTrend": [
            {
                "date": "Semana 1",
                "users": total_users - users_7d,
                "downloads": dls_prev_24h,
            },
            {"date": "Semana 2", "users": total_users, "downloads": dls_24h},
        ],
        "totalUsers": total_users,
        "users7d": users_7d,
        "totalBooks": total_books,
        "downloads24h": dls_24h,
        "downloadsPrev24h": dls_prev_24h,
        "uptime": uptime_text,
    }
