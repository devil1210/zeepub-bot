"""
Handlers para procesamiento masivo de librería
"""

import asyncio
import logging
from typing import Any

from sqlalchemy import text

from core.db_manager_pg import pg_manager
from utils.helpers import generar_slug_from_meta, parse_metadata_from_title

logger = logging.getLogger(__name__)


class BulkReviewService:
    """Servicio para revisión y corrección masiva de metadatos"""

    def __init__(self):
        self.active_jobs = {}

    async def analyze_library(self, filters: dict[str, Any] = None, batch_size: int = 100) -> dict[str, Any]:
        """
        Analiza toda la librería buscando problemas en metadatos

        Args:
            filters: Filtros opcionales para el análisis
            batch_size: Tamaño del lote para procesamiento

        Returns:
            Dict con resultados del análisis
        """
        logger.info("🔍 Iniciando análisis masivo de librería...")

        issues_found = []
        total_processed = 0
        total_series = 0

        async with pg_manager.get_session() as session:
            # Obtener total de series
            count_query = text("SELECT COUNT(*) FROM series_metadata WHERE series_name IS NOT NULL")
            total_result = await session.execute(count_query)
            total_series = total_result.scalar()

            # Procesar en lotes
            offset = 0
            while True:
                query = text("""
                    SELECT id, series_name, series_hash, series_english, series_spanish
                    FROM series_metadata
                    WHERE series_name IS NOT NULL
                    ORDER BY id
                    LIMIT :limit OFFSET :offset
                """)

                result = await session.execute(query, {"limit": batch_size, "offset": offset})

                batch = result.fetchall()
                if not batch:
                    break

                # Analizar cada serie en el lote
                for series_id, series_name, series_hash, series_english, series_spanish in batch:
                    issues = await self._analyze_series_metadata(
                        series_id, series_name, series_hash, series_english, series_spanish
                    )
                    if issues:
                        issues_found.extend(issues)

                    total_processed += 1

                # Log de progreso
                progress = (total_processed / total_series) * 100
                logger.info(f"📊 Progreso: {total_processed}/{total_series} ({progress:.1f}%)")

                offset += batch_size

                # Pequeña pausa para no sobrecargar la DB
                await asyncio.sleep(0.1)

        logger.info(f"✅ Análisis completado: {len(issues_found)} problemas encontrados")

        return {
            "issues": issues_found,
            "total_series": total_series,
            "processed": total_processed,
            "issues_count": len(issues_found),
        }

    async def _analyze_series_metadata(
        self, series_id: int, series_name: str, series_hash: str, series_english: str | None, series_spanish: str | None
    ) -> list[dict[str, Any]]:
        """
        Analiza los metadatos de una serie específica

        Returns:
            Lista de problemas encontrados
        """
        issues = []

        # 1. Verificar signos de interrogación faltantes
        if self._should_have_question_mark(series_name) and not series_name.endswith("?"):
            suggested_name = series_name + "?"
            issues.append(
                {
                    "type": "missing_question_mark",
                    "series_id": series_id,
                    "series_hash": series_hash,
                    "current_value": series_name,
                    "suggested_value": suggested_name,
                    "field": "series_name",
                    "severity": "medium",
                    "description": "El título parece ser una pregunta pero falta el signo de interrogación",
                }
            )

        # 2. Reprocesar título con parse_metadata_from_title corregido
        parsed = parse_metadata_from_title(series_name, preserve_special_chars=True)
        clean_name = parsed.get("series") or series_name

        if clean_name != series_name:
            issues.append(
                {
                    "type": "title_cleanup",
                    "series_id": series_id,
                    "series_hash": series_hash,
                    "current_value": series_name,
                    "suggested_value": clean_name,
                    "field": "series_name",
                    "severity": "low",
                    "description": "El título puede limpiarse usando el parseador actualizado",
                }
            )

        # 3. Verificar consistencia de slugs
        meta_dict = {"series_name": clean_name, "series_english": series_english, "series_spanish": series_spanish}
        correct_slug = generar_slug_from_meta(meta_dict)

        async with pg_manager.get_session() as session:
            slug_query = text("SELECT slug FROM series_metadata WHERE id = :series_id")
            slug_result = await session.execute(slug_query, {"series_id": series_id})
            current_slug = slug_result.scalar()

            if current_slug != correct_slug:
                issues.append(
                    {
                        "type": "slug_inconsistency",
                        "series_id": series_id,
                        "series_hash": series_hash,
                        "current_value": current_slug,
                        "suggested_value": correct_slug,
                        "field": "slug",
                        "severity": "high",
                        "description": "El slug no coincide con el título actualizado",
                    }
                )

        return issues

    def _should_have_question_mark(self, title: str) -> bool:
        """
        Determina si un título probablemente debería tener signo de interrogación
        """
        question_patterns = [
            "aren't",
            "isn't",
            "doesn't",
            "don't",
            "can't",
            "won't",
            "couldn't",
            "wouldn't",
            "shouldn't",
            "mightn't",
            "mustn't",
            "aren",
            "what",
            "when",
            "where",
            "why",
            "how",
            "who",
            "which",
            "are you",
            "is he",
            "is she",
            "do you",
            "did you",
            "will you",
            "can you",
            "could you",
            "would you",
            "should you",
        ]

        title_lower = title.lower()
        return any(pattern in title_lower for pattern in question_patterns)

    async def bulk_update_metadata(self, updates: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Aplica actualizaciones masivas de metadatos

        Args:
            updates: Lista de actualizaciones a aplicar

        Returns:
            Resultado de la operación
        """
        logger.info(f"🔄 Aplicando {len(updates)} actualizaciones masivas...")

        updated_count = 0
        errors = []

        async with pg_manager.get_session() as session:
            try:
                for update in updates:
                    try:
                        series_id = update["series_id"]
                        field = update["field"]
                        new_value = update["new_value"]

                        # Actualización específica según el campo
                        if field == "series_name":
                            query = text("""
                                UPDATE series_metadata
                                SET series_name = :new_value
                                WHERE id = :series_id
                            """)
                        elif field == "slug":
                            query = text("""
                                UPDATE series_metadata
                                SET slug = :new_value
                                WHERE id = :series_id
                            """)
                        else:
                            errors.append({"series_id": series_id, "error": f"Campo no soportado: {field}"})
                            continue

                        await session.execute(query, {"new_value": new_value, "series_id": series_id})

                        updated_count += 1

                    except Exception as e:
                        errors.append({"series_id": update.get("series_id"), "error": str(e)})
                        logger.error(f"Error actualizando serie {update.get('series_id')}: {e}")

                # Commit de todas las actualizaciones
                await session.commit()

            except Exception as e:
                await session.rollback()
                logger.error(f"Error en transacción masiva: {e}")
                errors.append({"error": f"Error en transacción: {str(e)}"})

        logger.info(f"✅ Actualizaciones completadas: {updated_count} exitosas, {len(errors)} errores")

        return {"updated": updated_count, "errors": errors, "total_requested": len(updates)}

    async def get_job_status(self, job_id: str) -> dict[str, Any]:
        """
        Obtiene el estado de un trabajo de procesamiento masivo
        """
        if job_id not in self.active_jobs:
            return {"status": "not_found", "message": "Job not found"}

        job = self.active_jobs[job_id]
        return {
            "status": job.get("status", "unknown"),
            "progress": job.get("progress", 0),
            "current": job.get("current", ""),
            "total": job.get("total", 0),
            "processed": job.get("processed", 0),
            "errors": job.get("errors", []),
        }


# Instancia global del servicio
bulk_review_service = BulkReviewService()
