import logging
import os
import shutil
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import desc, func, select, update

from api.handlers.helpers import check_staff
from config.config_settings import config
from core.db_manager_pg import pg_manager
from models.library_models import AILearningFeedback, LocalBook, MetadataProposal, SeriesMetadata
from services.ai_service import AIService
from services.settings_service import get_setting, set_setting
from utils.helpers import generate_series_hash
from utils.library_db import get_session

logger = logging.getLogger(__name__)


async def handle_ai_generate_summary(data: dict[str, Any], user_data: dict[str, Any]):
    """Genera una sinopsis corta por IA para un libro."""
    check_staff(user_data)
    book_id_raw = data.get("bookId")
    if not book_id_raw:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId")

    try:
        book_id = int(str(book_id_raw).replace("local_", ""))
    except ValueError as e:
        raise HTTPException(status_code=400, detail="ID de libro inválido") from e

    async with pg_manager.get_session() as session:
        stmt = select(LocalBook).where(LocalBook.id == book_id)
        res = await session.execute(stmt)
        book = res.scalar()

        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        if not book.description:
            return {
                "success": False,
                "message": "El libro no tiene una descripción base para resumir.",
            }

        # Generar sinopsis
        summary = await AIService.generate_synopsis(book.title, book.description)
        if summary:
            book.summary = summary
            await session.commit()
            return {"success": True, "summary": summary}
        else:
            return {"success": False, "message": "No se pudo generar el resumen."}


async def handle_ai_scan_series(data: dict[str, Any], user_data: dict[str, Any]):
    """Analiza una serie completa con IA para unificar metadatos."""
    check_staff(user_data)
    series_hash = data.get("series_hash")
    series_name = data.get("series_name")  # Optional fallback
    dry_run = data.get("dry_run", False)

    if not config.GEMINI_API_KEY:
        return {"success": False, "message": "IA no configurada (Falta API Key)"}

    try:
        with get_session() as session:
            # Buscar libros de esa serie
            query = session.query(LocalBook).filter(LocalBook.series_hash == series_hash)
            books = query.order_by(LocalBook.volume.asc()).all()

            if not books:
                return {"success": False, "message": "Serie no encontrada"}

            rep_book = books[0]  # Usar cualquiera como representante base
            current_name = rep_book.series or series_name or rep_book.title

            # Obtener nombre español si ya existe
            series_meta = session.query(SeriesMetadata).filter_by(series_hash=series_hash).first()
            current_spanish = series_meta.series_spanish if series_meta else rep_book.series_spanish

            # --- DRY RUN MODE (PROPOSAL) ---
            if dry_run:
                books_dicts = [b.to_dict() for b in books]
                proposal = await AIService.analyze_series_for_updates(
                    series_hash, current_name, books_dicts, current_spanish
                )

                if "error" in proposal:
                    return {
                        "success": False,
                        "message": f"Error de IA: {proposal['error']}",
                    }

                # If no changes are needed, log feedback immediately
                if proposal.get("no_changes_needed"):
                    await AIService.log_feedback(
                        series_hash=series_hash,
                        original=current_name,
                        proposed=proposal.get("proposed_series", current_name),
                        final=proposal.get("proposed_series", current_name),
                        status="no_changes",
                        ai_reason=proposal.get("reason", "Serie ya optimizada"),
                    )

                    # Also save as approved proposal for AI learning
                    existing = (
                        session.query(MetadataProposal)
                        .filter_by(series_hash=series_hash)
                        .filter(MetadataProposal.status.in_(["pending", "approved"]))
                        .first()
                    )

                    if existing:
                        # Update existing proposal
                        existing.proposal_data = proposal
                        existing.status = "approved"
                        existing.processed_at = datetime.utcnow()
                    else:
                        # Create new approved proposal (as reference for AI)
                        new_prop = MetadataProposal(
                            series_hash=series_hash,
                            proposal_data=proposal,
                            status="approved",
                            processed_at=datetime.utcnow(),
                        )
                        session.add(new_prop)

                    session.commit()

                return {"success": True, "proposal": proposal, "dry_run": True}

            # --- EXECUTE MODE (STAGING) ---
            # Ya NO aplicamos cambios directamente. Guardamos como propuesta.
            books_dicts = [b.to_dict() for b in books]
            proposal = await AIService.analyze_series_for_updates(
                series_hash, current_name, books_dicts, current_spanish
            )

            if not proposal or "error" in proposal:
                return {
                    "success": False,
                    "message": f"Error de IA: {proposal.get('error', 'Fallo desconocido')}",
                }

            # Verificar si ya existe una pendiente
            existing = (
                session.query(MetadataProposal)
                .filter_by(series_hash=series_hash, status="pending")
                .first()
            )
            if existing:
                existing.proposal_data = proposal
                existing.created_at = datetime.utcnow()
            else:
                new_prop = MetadataProposal(
                    series_hash=series_hash, proposal_data=proposal, status="pending"
                )
                session.add(new_prop)

            session.commit()

            return {
                "success": True,
                "message": f"Propuesta para '{current_name}' generada. Revisa la bandeja de entrada para aprobarla.",
            }

    except Exception as e:
        logger.error(f"Error in AI scan series: {e}")
        return {"success": False, "message": str(e)}


async def handle_ai_apply_changes(data: dict[str, Any], user_data: dict[str, Any]):
    """Aplica los cambios propuestos por la IA a una serie."""
    check_staff(user_data)
    if not config.GEMINI_API_KEY:
        return {"success": False, "message": "IA no configurada"}

    proposal = data.get("proposal")
    proposal_id = data.get("proposal_id")

    if not proposal and not proposal_id:
        raise HTTPException(status_code=400, detail="Faltan datos de la propuesta")

    with get_session() as session:
        # Si nos pasan un proposal_id, cargamos los datos y lo marcamos como aprobado al final
        db_proposal = None
        if proposal_id:
            db_proposal = session.query(MetadataProposal).get(proposal_id)
            if not db_proposal:
                raise HTTPException(status_code=404, detail="Propuesta no encontrada")
            proposal = db_proposal.proposal_data
        else:
            # Intentar encontrar una propuesta pendiente automática para esta misma serie
            # (Por si el usuario triggeró el escaneo manualmente pero ya había una pendiente)
            series_hash_raw = proposal.get("series_hash")
            if series_hash_raw:
                db_proposal = (
                    session.query(MetadataProposal)
                    .filter_by(series_hash=series_hash_raw, status="pending")
                    .first()
                )

        series_hash = proposal.get("series_hash")
        # Changes is a list of approved changes: { "book_id": 123, "proposed_filename": "..." }
        approved_changes = data.get("approved_changes", [])
        # Global series metadata overrides
        proposed_series = data.get("proposed_series")
        proposed_spanish = data.get("proposed_spanish")

        # Optional flags
        apply_renames = data.get("apply_renames", True)
        apply_meta = data.get("apply_meta", True)

        updated_count = 0
        errors = []

        # 1. Update Series Metadata (Global)
        if apply_meta and proposed_series:
            # Sync with SeriesMetadata table
            series = session.query(SeriesMetadata).filter_by(series_hash=series_hash).first()
            # If not in data, fallback to proposal
            if not proposed_spanish:
                proposed_spanish = proposal.get("proposed_spanish")

            # Debug logging
            logger.info(
                f"📝 Applying AI changes - Series: {proposed_series}, Spanish: {proposed_spanish}"
            )

            # --- HASH MIGRATION LOGIC ---
            # Si el nombre de la serie cambia, el hash DEBE cambiar para mantener la integridad.

            new_hash = generate_series_hash(
                proposed_series,
                series.author if series else None,
                series.book_type if series else None,
            )

            effective_hash = series_hash

            # Si el hash cambió, migrar todo
            if new_hash != series_hash:
                logger.info(f"🔄 Migrando serie de {series_hash} a {new_hash} (Nombre cambiado)")

                # Check collision (Merge Scenario)
                existing_target_series = (
                    session.query(SeriesMetadata).filter_by(series_hash=new_hash).first()
                )

                if existing_target_series:
                    logger.info(f"Target series {new_hash} exists. Merging into it.")
                    effective_hash = new_hash
                    # Merge tags/metadata logic implied: we keep target or mix
                    # Update target with proposed name/spanish if target matches proposed
                    existing_target_series.series_name = proposed_series
                    existing_target_series.series_spanish = proposed_spanish or proposed_series
                    if proposal.get("description"):
                        existing_target_series.description = proposal["description"]

                    # Delete old series metadata stub if distinct
                    if series and series.id != existing_target_series.id:
                        session.delete(series)

                    series = existing_target_series  # Point reference to target
                else:
                    # Just update the hash of the current series
                    if series:
                        old_hash = series.series_hash
                        series.series_hash = new_hash
                        effective_hash = new_hash

                        # IMPORTANTE: Debemos actualizar el hash en todos los libros locales
                        # asociados a este hash para mantener la consistencia de identidad.
                        session.execute(
                            update(LocalBook)
                            .where(LocalBook.series_hash == old_hash)
                            .values(series_hash=new_hash)
                        )
                        logger.info(f"📍 Libros actualizados de hash {old_hash} a {new_hash}")
                    else:
                        # Should have been created above, but safety check
                        pass

            if series:
                # series_name sigue siendo el nombre visual principal corregido
                series.series_name = proposed_series
                series.series_english = proposed_series  # Nueva columna específica para IA
                series.series_spanish = proposed_spanish or series.series_spanish or proposed_series
                if proposal.get("description"):
                    series.description = proposal["description"]

                # Sincronizamos tags proactivamente si la IA propone nuevos géneros BASE
                if proposal.get("genres"):
                    current_tags = set(series.tags) if series.tags else set()
                    new_base_tags = set(proposal["genres"])
                    series.tags = list(current_tags | new_base_tags)
            else:
                pass

            # 1.1 Update Translator Group Metadata
            group_full = proposal.get("group_full")
            group_siglas = proposal.get("group_siglas")
            if group_full and group_siglas and group_full != "Unknown":
                from models.library_models import TranslatorsGroup

                # Try to find by name (case insensitive)
                existing_group = (
                    session.query(TranslatorsGroup)
                    .filter(func.lower(TranslatorsGroup.name) == func.lower(group_full))
                    .first()
                )
                if existing_group:
                    existing_group.siglas = group_siglas
                else:
                    new_group = TranslatorsGroup(name=group_full, siglas=group_siglas)
                    session.add(new_group)

            # Cloud Sync immediately if enabled (Using updated series/hash)
            if config.ENABLE_SUPABASE and series:
                try:
                    from core.supabase_manager import supabase_manager

                    client = supabase_manager.get_client()
                    s_data = {
                        "series_hash": series.series_hash,
                        "series_name": series.series_name,
                        "series_spanish": series.series_spanish,
                        "series_english": series.series_english,  # Sync new col to cloud
                        "description": series.description,
                        "tags": series.tags,
                        "author": series.author,
                        "book_count": series.book_count,
                        "rating_average": series.rating_average,
                    }
                    client.table("series_metadata").upsert(
                        s_data, on_conflict="series_hash"
                    ).execute()
                except Exception as cloud_e:
                    logger.warning(f"Failed to sync series to cloud: {cloud_e}")

            # Update all books in this hash group (OLD hash) to the new info using effective_hash
            stmt = select(LocalBook).where(LocalBook.series_hash == series_hash)
            books = session.execute(stmt).scalars().all()

            for book in books:
                book.series_metadata_id = series.id if series else None
                # Si el hash cambió, ya lo actualizamos arriba vía SQL masivo por eficiencia,
                # pero nos aseguramos de que el objeto en memoria esté sincronizado si se usa después.
                book.series_hash = effective_hash
                book.series = proposed_series
                book.series_english = proposed_series  # Nueva columna visual (IA)
                book.is_uncensored = proposal.get("is_uncensored_series", False)
                book.series_spanish = proposed_spanish or series.series_spanish or proposed_series

                # Aprovechar y actualizar volumen si está en la propuesta
                orig_filename = book.filename or book.title
                if proposal.get("volumes") and orig_filename in proposal["volumes"]:
                    book.volume = proposal["volumes"][orig_filename]

            updated_count += len(books)

            # Commit metadata changes immediately to ensure they're visible to subsequent AI analysis
            session.commit()
            logger.info(
                f"✅ Series metadata updated and committed: {proposed_series} (ES: {proposed_spanish}) Hash: {effective_hash}"
            )

        # 2. Apply File Renames
        if apply_renames and approved_changes:
            for change in approved_changes:
                book_id_raw = change.get("book_id")
                proposed_filename = change.get("proposed_filename")

                if not book_id_raw or not proposed_filename:
                    continue

                try:
                    book_id = int(str(book_id_raw).replace("local_", ""))
                except ValueError:
                    errors.append(f"ID de libro inválido: {book_id_raw}")
                    continue

                book = session.query(LocalBook).filter(LocalBook.id == book_id).scalar()
                if not book or not book.filepath or not os.path.exists(book.filepath):
                    errors.append(f"Libro {book_id} no encontrado en disco")
                    continue

                old_path = book.filepath
                dir_name = os.path.dirname(old_path)
                new_path = os.path.join(dir_name, proposed_filename)

                if old_path != new_path:
                    # Check for DB collision first
                    collision = session.query(LocalBook).filter_by(filepath=new_path).first()
                    if collision and collision.id != book.id:
                        errors.append(
                            f"No se puede renombrar: El destino ya existe en la BD (ID: {collision.id})"
                        )
                        continue

                    if os.path.exists(new_path) and not os.path.samefile(old_path, new_path):
                        # File system collision check (just in case DB is out of sync)
                        errors.append(
                            "No se puede renombrar: El archivo destino ya existe en disco"
                        )
                        continue

                    try:
                        shutil.move(old_path, new_path)
                        book.filepath = new_path
                        book.filename = proposed_filename
                        # Update database record
                        updated_count += 1
                    except Exception as e:
                        errors.append(f"Error renombrando {book.filename}: {e}")

        session.commit()

        # 3. Consolidar metadata de serie tras los cambios
        from services.scanner_service import ScannerService

        ScannerService.sync_series_metadata(session, effective_hash)
        session.commit()

        # 4. Log feedback for learning

        status = "accepted"
        if proposal.get("is_perfect_match"):
            status = "accepted"  # IA was right that nothing was needed
        elif proposed_series != proposal.get("proposed_series") or proposed_spanish != proposal.get(
            "proposed_spanish"
        ):
            status = "edited"

        await AIService.log_feedback(
            series_hash=effective_hash,
            original=proposal.get("current_series"),
            proposed=proposal.get("proposed_series"),
            final=proposed_series,
            proposed_spanish=proposal.get("proposed_spanish"),
            final_spanish=proposed_spanish,
            status=status,
            ai_reason=proposal.get("reason"),
        )

        # Si venía de una propuesta almacenada, marcarla como aprobada
        if db_proposal:
            db_proposal.status = "approved"
            db_proposal.processed_at = datetime.utcnow()
            session.commit()

    return {
        "success": True,
        "message": "Cambios aplicados correctamente."
        if updated_count > 0 or proposal.get("is_perfect_match")
        else "No se detectaron cambios pendientes.",
        "updated_count": updated_count,
        "errors": errors,
    }


async def handle_ai_apply_merge(data: dict[str, Any], user_data: dict[str, Any]):
    """Fusiona dos series (source -> target)."""
    check_staff(user_data)
    proposal_id = data.get("proposal_id")
    if not proposal_id:
        raise HTTPException(status_code=400, detail="Falta proposal_id")

    from services.scanner_service import ScannerService

    with get_session() as session:
        db_proposal = session.query(MetadataProposal).get(proposal_id)
        if not db_proposal or db_proposal.type != "merge":
            raise HTTPException(status_code=404, detail="Propuesta de fusión no encontrada")

        hash_a = db_proposal.series_hash
        hash_b = db_proposal.secondary_hash
        proposal = db_proposal.proposal_data

        # 1. Mover todos los libros de B a A
        res = session.execute(
            update(LocalBook).where(LocalBook.series_hash == hash_b).values(series_hash=hash_a)
        )
        moved_count = res.rowcount

        # 2. Actualizar metadata de la serie A si el usuario aprobó un nombre específico
        main_name = proposal.get("suggested_main_name")
        main_spanish = proposal.get("suggested_spanish_name")
        if main_name:
            series_a = session.query(SeriesMetadata).filter_by(series_hash=hash_a).first()
            if series_a:
                series_a.series_name = main_name
                if main_spanish:
                    series_a.series_spanish = main_spanish

            # Sincronizar nombre en los libros movidos
            session.execute(
                update(LocalBook)
                .where(LocalBook.series_hash == hash_a)
                .values(series=main_name, series_spanish=main_spanish or main_name)
            )

            # Cloud Sync A
            if config.ENABLE_SUPABASE:
                try:
                    from core.supabase_manager import supabase_manager

                    client = supabase_manager.get_client()
                    if series_a:
                        client.table("series_metadata").upsert(
                            {
                                "series_hash": series_a.series_hash,
                                "series_name": series_a.series_name,
                                "series_spanish": series_a.series_spanish,
                            },
                            on_conflict="series_hash",
                        ).execute()
                    # Delete B from cloud too
                    client.table("series_metadata").delete().eq("series_hash", hash_b).execute()
                except Exception:
                    pass

        # 3. Eliminar la serie B nula
        session.query(SeriesMetadata).filter_by(series_hash=hash_b).delete()

        # 4. Marcar como procesada
        db_proposal.status = "approved"
        db_proposal.processed_at = datetime.utcnow()

        session.commit()

        # 5. Volver a sincronizar metadata para consolidar conteos, etc.
        ScannerService.sync_series_metadata(session, hash_a)
        session.commit()

        return {
            "success": True,
            "message": f"Fusión completada. {moved_count} libros movidos a la serie principal.",
        }


async def handle_ai_get_proposals(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene propuestas de metadatos IA pendientes."""
    check_staff(user_data)
    with get_session() as session:
        proposals = (
            session.query(MetadataProposal)
            .filter_by(status="pending")
            .order_by(MetadataProposal.created_at.desc())
            .all()
        )
        return {
            "success": True,
            "proposals": [
                {
                    "id": p.id,
                    "series_hash": p.series_hash,
                    "secondary_hash": p.secondary_hash,
                    "type": p.type,
                    "proposal": p.proposal_data,
                    "created_at": p.created_at.isoformat(),
                }
                for p in proposals
            ],
        }


async def handle_ai_reject_proposal(data: dict[str, Any], user_data: dict[str, Any]):
    """Rechaza propuestas de la IA."""
    check_staff(user_data)
    proposal_id = data.get("proposal_id")
    if not proposal_id:
        raise HTTPException(status_code=400, detail="Falta proposal_id")

    with get_session() as session:
        p = session.query(MetadataProposal).get(proposal_id)
        if p:
            p.status = "rejected"
            p.processed_at = datetime.utcnow()
            session.commit()
            return {"success": True, "message": "Propuesta rechazada."}
        else:
            return {"success": False, "message": "Propuesta no encontrada."}


async def handle_ai_reset_series(data: dict[str, Any], user_data: dict[str, Any]):
    """Resetea metadatos de serie a valores por defecto (borra SeriesMetadata)."""
    check_staff(user_data)
    series_hash = data.get("series_hash")
    if not series_hash:
        raise HTTPException(status_code=400, detail="Falta series_hash")

    with get_session() as session:
        # 1. Resetear libros
        session.execute(
            update(LocalBook)
            .where(LocalBook.series_hash == series_hash)
            .values(series_spanish=None)
        )

        # 2. Resetear Serie
        series = session.query(SeriesMetadata).filter_by(series_hash=series_hash).first()
        if series:
            series.series_spanish = None

        # 3. Eliminar propuestas pendientes/anteriores
        session.query(MetadataProposal).filter_by(series_hash=series_hash).delete()

        session.commit()
        return {
            "success": True,
            "message": "Metadatos de la serie reseteados. El Jardinero IA la procesará en breve.",
        }


async def handle_ai_stats(data: dict[str, Any], user_data: dict[str, Any]):
    """Devuelve estadísticas del módulo IA."""
    import asyncio

    check_staff(user_data)
    try:
        # Gather async DB stats
        async with pg_manager.get_session() as session:
            # 1. Total series processed by AI (have series_spanish or proposal)
            processed_series = (
                await session.execute(
                    select(func.count(SeriesMetadata.id)).where(SeriesMetadata.series_spanish.isnot(None))
                )
            ).scalar() or 0

            # 2. Total pending proposals
            pending = (
                await session.execute(
                    select(func.count(MetadataProposal.id)).where(MetadataProposal.status == "pending")
                )
            ).scalar() or 0

            # 3. Learning accuracy (from AILearningFeedback)
            total_feedback = (
                await session.execute(select(func.count(AILearningFeedback.id)))
            ).scalar() or 0

            accepted_feedback = (
                await session.execute(
                    select(func.count(AILearningFeedback.id)).where(
                        AILearningFeedback.status.in_(["accepted", "no_changes"])
                    )
                )
            ).scalar() or 0

            accuracy = 0
            if total_feedback and total_feedback > 0:
                accuracy = round((accepted_feedback / total_feedback) * 100, 1)

            # 4. Recent activity (last 5 processed)
            recent_res = await session.execute(
                select(AILearningFeedback)
                .order_by(desc(AILearningFeedback.created_at))
                .limit(5)
            )
            recent_activity = recent_res.scalars().all()

            # 5. Total books (for dashboard)
            total_books = (await session.execute(select(func.count(LocalBook.id)))).scalar() or 0

            # Serialize recent activity while session is still open
            recent_list = [
                {
                    "series": f.series_name_original,
                    "action": f.status,
                    "date": f.created_at.isoformat(),
                }
                for f in recent_activity
            ]

        # 6. System Status (outside async session to avoid psycopg2/asyncpg conflicts)
        ai_active = bool(config.GEMINI_API_KEY)
        ai_key_masked = (
            f"{config.GEMINI_API_KEY[:4]}...{config.GEMINI_API_KEY[-4:]}"
            if config.GEMINI_API_KEY and len(config.GEMINI_API_KEY) > 8
            else "NOT_SET"
        )

        # Fetch background scan setting via thread (sync psycopg2 call)
        bg_scan = await asyncio.to_thread(get_setting, "ai_background_maintenance", "false")
        background_scan_enabled = str(bg_scan).lower() == "true"

        return {
            "success": True,
            "result": {
                "total_processed": processed_series,
                "processed_series": processed_series,
                "pending_optimization": pending,
                "pending_proposals": pending,
                "time_saved_hours": round(processed_series * 0.15, 1),
                "total_books": total_books,
                "accuracy": accuracy,
                "total_feedback": total_feedback,
                "ai_active": ai_active,
                "ai_key_masked": ai_key_masked,
                "background_scan_enabled": background_scan_enabled,
                "recent_activity": recent_list,
            },
        }

    except Exception as e:
        logger.error(f"Error fetching AI stats: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def handle_ai_toggle_background_scan(data: dict[str, Any], user_data: dict[str, Any]):
    """Activa/Desactiva el escaneo en segundo plano."""
    check_staff(user_data)
    enabled = data.get("enabled", False)
    try:
        set_setting("ai_background_maintenance", "true" if enabled else "false")
        return {
            "success": True,
            "message": f"Escaneo en segundo plano {'activado' if enabled else 'desactivado'}",
            "enabled": enabled,
        }
    except Exception as e:
        logger.error(f"Error toggling background scan: {e}")
        return {"success": False, "message": str(e)}


async def handle_ai_get_lists(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene listas de control (ignorados, whitelist, learning)."""
    import asyncio

    check_staff(user_data)
    list_type = data.get("type", "queue")  # 'queue' or 'learning'
    limit = data.get("limit", 20)
    offset = data.get("offset", 0)

    def _sync_query():
        with get_session() as session:
            if list_type == "queue":
                # Pending proposals
                query = (
                    session.query(MetadataProposal)
                    .filter_by(status="pending")
                    .order_by(desc(MetadataProposal.created_at))
                )
                total = query.count()
                items = query.limit(limit).offset(offset).all()

                return {
                    "success": True,
                    "items": [
                        {
                            "id": p.id,
                            "series_hash": p.series_hash,
                            "current_series": p.proposal_data.get("current_series", "Unknown") if p.proposal_data else "Unknown",
                            "proposed_series": p.proposal_data.get("proposed_series") if p.proposal_data else None,
                            "reason": p.proposal_data.get("reason") if p.proposal_data else None,
                            "created_at": p.created_at.isoformat() if p.created_at else None,
                        }
                        for p in items
                    ],
                    "total": total,
                }

            elif list_type == "learning":
                # Historical feedback — field names must match frontend 'reviewed' tab expectations
                query = session.query(AILearningFeedback).order_by(
                    desc(AILearningFeedback.created_at)
                )
                total = query.count()
                items = query.limit(limit).offset(offset).all()

                return {
                    "success": True,
                    "items": [
                        {
                            "id": f.id,
                            "series_hash": getattr(f, "series_hash", None) or f"feedback_{f.id}",
                            "original_name": f.series_name_original,
                            "proposed_name": f.series_name_proposed,
                            "final_name": f.series_name_final,
                            "status": f.status,
                            "ai_reason": f.ai_reason,
                            "reviewed_at": f.created_at.isoformat() if f.created_at else None,
                            "books_count": getattr(f, "books_count", 0) or 0,
                        }
                        for f in items
                    ],
                    "total": total,
                }
            else:
                return {"success": False, "message": "Invalid list type"}

    try:
        return await asyncio.to_thread(_sync_query)
    except Exception as e:
        logger.error(f"Error fetching AI lists: {e}", exc_info=True)
        return {"success": False, "message": str(e)}
