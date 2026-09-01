# handlers/commands/extra_commands_handler.py
"""
Manejador modular de comandos enriquecidos para usuarios y administración.
Cumple estrictamente con el principio de responsabilidad única y límite < 500 líneas.
"""

import logging
import os
import psutil
import unicodedata
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from core.state_manager import state_manager
from services.cache_service import cache_manager, catalog_cache
from services.cover_service import _cover_file_id_cache
from services.library_service import LibraryService
from services.library_ui.catalog_views import mostrar_generos, mostrar_series
from services.library_ui.info_views import check_is_admin_or_staff
from services.library_ui.series_views import mostrar_volumenes_local
from services.rich_message_service import RichMessageService
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    """Normaliza texto eliminando acentos y convirtiendo a minúsculas."""
    if not text:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", text.lower().strip())
        if unicodedata.category(c) != "Mn"
    )


class ExtraCommandsHandler:
    """Controlador de comandos adicionales para lectores y administradores."""

    def __init__(self, app=None):
        self.app = app

    # ==========================================
    # 👥 COMANDOS DE LECTORES
    # ==========================================

    async def handle_random(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recomienda una novela aleatoria."""
        chat_id = update.effective_chat.id
        thread_id = get_thread_id(update)
        uid = update.effective_user.id
        st = state_manager.get_user_state(uid)

        series = await LibraryService.get_random_series()
        if not series or not series.get("id"):
            await update.effective_message.reply_text("⚠️ No se encontraron novelas en el catálogo.")
            return

        st.setdefault("historial", []).append(("main",))
        await mostrar_volumenes_local(update, context, series_hash=series["id"], force_new=True)

    async def handle_top(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el Top 10 de novelas más descargadas."""
        chat_id = update.effective_chat.id
        thread_id = get_thread_id(update)
        uid = update.effective_user.id
        st = state_manager.get_user_state(uid)

        top_series = await LibraryService.get_top_downloaded_series(limit=10)
        if not top_series:
            await update.effective_message.reply_text("ℹ️ Aún no hay suficientes estadísticas de descarga.")
            return

        table_cells = []
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        btn_rows = []
        current_btn_row = []

        for idx, s in enumerate(top_series):
            medal = medals[idx] if idx < len(medals) else f"#{idx+1}"
            s_name = s.get("name") or "Sin título"
            dl_cnt = s.get("download_count", 0)
            table_cells.append([
                {"text": f"{medal} {idx+1}", "align": "center"},
                {"text": str(s_name)[:30], "align": "left"},
                {"text": f"📥 {dl_cnt}", "align": "right"},
            ])

            s_id = s.get("id", "")
            if s_id:
                s_short = s_id[:16]
                current_btn_row.append({"text": f"{medal} {s_name[:12]}", "callback_data": f"local_series|{s_short}"})
                if len(current_btn_row) == 2:
                    btn_rows.append(current_btn_row)
                    current_btn_row = []

        if current_btn_row:
            btn_rows.append(current_btn_row)

        blocks = [
            {"type": "heading", "size": 2, "text": "🏆 Top 10 Novelas Más Populares"},
            {
                "type": "table",
                "is_bordered": True,
                "is_striped": True,
                "is_compact": True,
                "cells": table_cells,
            },
            {
                "type": "paragraph",
                "text": "<i>Selecciona cualquiera de las novelas para ver sus volúmenes y descargar:</i>",
            },
        ]
        for row in btn_rows:
            blocks.append({"type": "buttons", "align": "center", "buttons": row})

        blocks.append({
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🏠 Menú Principal", "callback_data": "volver_menu"},
                {"text": "❌ Salir", "callback_data": "salir"},
            ],
        })

        await RichMessageService.send_rich_message(
            chat_id=chat_id,
            blocks=blocks,
            message_thread_id=thread_id,
        )

    async def handle_novedades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra los volúmenes recientemente incorporados."""
        chat_id = update.effective_chat.id
        thread_id = get_thread_id(update)
        uid = update.effective_user.id
        st = state_manager.get_user_state(uid)

        recent = await LibraryService.get_recent_books(page=1, items_per_page=8)
        items = recent.get("items", [])
        if not items:
            await update.effective_message.reply_text("ℹ️ No hay incorporaciones recientes registradas.")
            return

        table_cells = []
        btn_rows = []
        current_btn_row = []

        for b in items:
            title = b.get("title") or b.get("english_title") or "Novela"
            vol = b.get("volume", 1)
            b_hash = b.get("id") or b.get("book_hash") or ""
            table_cells.append([
                {"text": f"📖 {title[:28]}", "align": "left"},
                {"text": f"Vol. {vol}", "align": "right"},
            ])
            if b_hash:
                current_btn_row.append({"text": f"📚 {title[:14]} (V{vol})", "callback_data": f"lib|{b_hash[:16]}"})
                if len(current_btn_row) == 2:
                    btn_rows.append(current_btn_row)
                    current_btn_row = []

        if current_btn_row:
            btn_rows.append(current_btn_row)

        blocks = [
            {"type": "heading", "size": 2, "text": "✨ Novedades e Incorporaciones Recientes"},
            {
                "type": "table",
                "is_bordered": True,
                "is_striped": True,
                "is_compact": True,
                "cells": table_cells,
            },
        ]
        for row in btn_rows:
            blocks.append({"type": "buttons", "align": "center", "buttons": row})

        blocks.append({
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "📚 Ver Catálogo", "callback_data": "nav_local|all_series"},
                {"text": "🏠 Inicio", "callback_data": "volver_menu"},
            ],
        })

        await RichMessageService.send_rich_message(
            chat_id=chat_id,
            blocks=blocks,
            message_thread_id=thread_id,
        )

    async def handle_genero(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Filtra directamente por género (ej. /genero accion)."""
        if not context.args:
            await mostrar_generos(update, context)
            return

        query_gen = " ".join(context.args).strip()
        norm_query = _normalize_text(query_gen)
        genres = await LibraryService.get_genres()

        matched_gen = next((g for g in genres if _normalize_text(g) == norm_query), None)
        if not matched_gen:
            matched_gen = next((g for g in genres if norm_query in _normalize_text(g)), None)

        if matched_gen:
            await mostrar_series(update, context, origin_type="genre", filter_val=matched_gen, page=1, force_new=True)
        else:
            await update.effective_message.reply_text(
                f"⚠️ No se encontró el género <b>{query_gen}</b>.\n"
                f"Géneros disponibles: {', '.join(genres)}",
                parse_mode="HTML",
            )

    # ==========================================
    # 🛡️ COMANDOS DE ADMINISTRACIÓN
    # ==========================================

    async def handle_stats_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra panel de salud y diagnóstico del sistema."""
        uid = update.effective_user.id
        if not await check_is_admin_or_staff(uid, update.effective_user):
            await update.effective_message.reply_text("⛔ Comando restringido a administradores.")
            return

        chat_id = update.effective_chat.id
        thread_id = get_thread_id(update)

        # Memoria y proceso
        proc = psutil.Process(os.getpid())
        ram_mb = proc.memory_info().rss / (1024 * 1024)
        cpu_pct = proc.cpu_percent(interval=0.1)

        # Estadísticas de caché
        c_stats = await cache_manager.get_stats()
        cat_stats = await catalog_cache.get_stats()
        hit_rate = cat_stats.get("hit_rate", 0) * 100

        # Conteo de libros y series
        from core.db_manager_pg import pg_manager
        from sqlalchemy import func, select
        from models.library import LocalBook, Series
        from models.communications import PublicationQueue

        async with pg_manager.get_session() as session:
            s_count = (await session.execute(select(func.count(Series.id)))).scalar() or 0
            b_count = (await session.execute(select(func.count(LocalBook.id)))).scalar() or 0
            q_pending = (await session.execute(select(func.count(PublicationQueue.id)).where(PublicationQueue.status == "pending"))).scalar() or 0

        blocks = [
            {"type": "heading", "size": 2, "text": "⚡ Diagnóstico del Sistema • ZeePub"},
            {
                "type": "table",
                "is_bordered": True,
                "is_striped": True,
                "is_compact": True,
                "cells": [
                    [{"text": "🧠 RAM Bot", "align": "left"}, {"text": f"{ram_mb:.1f} MB", "align": "right"}],
                    [{"text": "⚙️ CPU Bot", "align": "left"}, {"text": f"{cpu_pct:.1f}%", "align": "right"}],
                    [{"text": "🎯 Hit Rate Caché", "align": "left"}, {"text": f"{hit_rate:.1f}%", "align": "right"}],
                    [{"text": "🖼️ Portadas en Caché", "align": "left"}, {"text": f"{len(_cover_file_id_cache)} file_ids", "align": "right"}],
                    [{"text": "📚 Series Indexadas", "align": "left"}, {"text": str(s_count), "align": "right"}],
                    [{"text": "📖 Volúmenes EPUB", "align": "left"}, {"text": str(b_count), "align": "right"}],
                    [{"text": "⏳ Cola Publicación", "align": "left"}, {"text": f"{q_pending} pendientes", "align": "right"}],
                ],
            },
            {
                "type": "buttons",
                "align": "center",
                "buttons": [
                    {"text": "🧹 Limpiar Caché", "callback_data": "admin_action|clearcache"},
                    {"text": "📋 Ver Cola", "callback_data": "admin_action|viewqueue"},
                ],
            },
        ]

        await RichMessageService.send_rich_message(
            chat_id=chat_id,
            blocks=blocks,
            message_thread_id=thread_id,
        )

    async def handle_clearcache_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Purga todas las cachés en memoria."""
        uid = update.effective_user.id
        if not await check_is_admin_or_staff(uid, update.effective_user):
            await update.effective_message.reply_text("⛔ Comando restringido a administradores.")
            return

        await catalog_cache.clear()
        _cover_file_id_cache.clear()
        await cache_manager.cleanup_expired()

        await update.effective_message.reply_text(
            "🧹 <b>Caché purgada exitosamente</b>\n"
            "• Catálogo, géneros y estadísticas reseteados a 0 ms.\n"
            "• Caché de file_ids de portadas limpiada.",
            parse_mode="HTML",
        )

    async def handle_cola_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra las publicaciones pendientes en cola."""
        uid = update.effective_user.id
        if not await check_is_admin_or_staff(uid, update.effective_user):
            await update.effective_message.reply_text("⛔ Comando restringido a administradores.")
            return

        chat_id = update.effective_chat.id
        thread_id = get_thread_id(update)

        from core.db_manager_pg import pg_manager
        from sqlalchemy import select, desc
        from models.communications import PublicationQueue

        async with pg_manager.get_session() as session:
            stmt = select(PublicationQueue).where(PublicationQueue.status == "pending").order_by(PublicationQueue.scheduled_for.asc()).limit(8)
            res = await session.execute(stmt)
            items = res.scalars().all()

        if not items:
            await update.effective_message.reply_text("✅ La cola de publicaciones está vacía (0 pendientes).")
            return

        cells = []
        for it in items:
            sched_str = it.scheduled_for.strftime("%d/%m %H:%M UTC") if it.scheduled_for else "Inmediato"
            b_hash = (it.book_hash or "")[:10]
            cells.append([
                {"text": f"ID #{it.id}", "align": "left"},
                {"text": f"📦 {b_hash}", "align": "left"},
                {"text": f"⏰ {sched_str}", "align": "right"},
            ])

        blocks = [
            {"type": "heading", "size": 2, "text": "⏳ Cola de Publicaciones Programadas"},
            {
                "type": "table",
                "is_bordered": True,
                "is_striped": True,
                "is_compact": True,
                "cells": cells,
            },
            {
                "type": "paragraph",
                "text": "<i>El procesador automático envía las publicaciones según su horario programado.</i>",
            },
        ]

        await RichMessageService.send_rich_message(
            chat_id=chat_id,
            blocks=blocks,
            message_thread_id=thread_id,
        )
