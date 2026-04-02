
async def handle_ai_stats(data: dict[str, Any], user_data: dict[str, Any]):
    """Devuelve estadísticas generales del módulo de IA."""
    try:
        with get_session() as session:
            # 1. Total series processed by AI (have series_spanish or proposal)
            processed_series = session.query(func.count(SeriesMetadata.id)).filter(
                SeriesMetadata.series_spanish.isnot(None)
            ).scalar()

            # 2. Total pending proposals
            pending = session.query(func.count(MetadataProposal.id)).filter_by(status="pending").scalar()

            # 3. Learning accuracy (from AILearningFeedback)
            total_feedback = session.query(func.count(AILearningFeedback.id)).scalar()
            accepted_feedback = (
                session.query(func.count(AILearningFeedback.id))
                .filter(AILearningFeedback.status.in_(["accepted", "no_changes"]))
                .scalar()
            )

            accuracy = 0
            if total_feedback and total_feedback > 0:
                accuracy = round((accepted_feedback / total_feedback) * 100, 1)

            # 4. Recent activity (last 5 processed)
            recent_activity = (
                session.query(AILearningFeedback)
                .order_by(desc(AILearningFeedback.created_at))
                .limit(5)
                .all()
            )

            return {
                "success": True,
                "stats": {
                    "processed_series": processed_series,
                    "pending_proposals": pending,
                    "accuracy": accuracy,
                    "total_feedback": total_feedback,
                    "recent_activity": [
                        {
                            "series": f.series_name_original,
                            "action": f.status,
                            "date": f.created_at.isoformat(),
                        }
                        for f in recent_activity
                    ],
                },
            }

    except Exception as e:
        logger.error(f"Error fetching AI stats: {e}")
        return {"success": False, "message": str(e)}


async def handle_ai_toggle_background_scan(data: dict[str, Any], user_data: dict[str, Any]):
    """Activa o desactiva el escaneo en segundo plano."""
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
    """Devuelve las listas de aprendizaje (historial) y cola (pendientes)."""
    list_type = data.get("type", "queue")  # 'queue' or 'learning'
    limit = data.get("limit", 20)
    offset = data.get("offset", 0)

    try:
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
                            "current_series": p.proposal_data.get("current_series", "Unknown"),
                            "proposed_series": p.proposal_data.get("proposed_series"),
                            "reason": p.proposal_data.get("reason"),
                            "created_at": p.created_at.isoformat(),
                        }
                        for p in items
                    ],
                    "total": total,
                }

            elif list_type == "learning":
                # Historical feedback
                query = session.query(AILearningFeedback).order_by(desc(AILearningFeedback.created_at))
                total = query.count()
                items = query.limit(limit).offset(offset).all()

                return {
                    "success": True,
                    "items": [
                        {
                            "id": f.id,
                            "series": f.series_name_original,
                            "proposed": f.series_name_proposed,
                            "final": f.series_name_final,
                            "status": f.status,
                            "ai_reason": f.ai_reason,
                            "created_at": f.created_at.isoformat(),
                        }
                        for f in items
                    ],
                    "total": total,
                }
            else:
                return {"success": False, "message": "Invalid list type"}

    except Exception as e:
        logger.error(f"Error fetching AI lists: {e}")
        return {"success": False, "message": str(e)}
