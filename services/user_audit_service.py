"""
User Audit Service
Servicio para registrar cambios en usuarios y permisos.
"""

import logging
from typing import Any

from sqlalchemy.orm import Session

from models.user_audit_models import UserAuditLog
from utils.library_db import get_session

logger = logging.getLogger(__name__)


class UserAuditService:
    """Servicio para registrar cambios en usuarios"""

    @staticmethod
    def log_change(
        user_id: str,
        username: str,
        action: str,
        changed_by_id: str,
        changed_by_username: str,
        field_changed: str | None = None,
        old_value: Any = None,
        new_value: Any = None,
        changes_summary: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session: Session | None = None,
    ) -> UserAuditLog:
        """
        Registra un cambio en el audit log.

        Args:
            user_id: ID del usuario afectado
            username: Username del usuario afectado
            action: Tipo de acción ('update_level', 'update_permissions', etc.)
            changed_by_id: ID del usuario que hizo el cambio
            changed_by_username: Username del usuario que hizo el cambio
            field_changed: Campo específico modificado (opcional)
            old_value: Valor anterior
            new_value: Valor nuevo
            changes_summary: Resumen completo de cambios
            ip_address: IP del cliente
            user_agent: User agent del cliente
            session: Sesión de SQLAlchemy (opcional, se crea una si no se provee)

        Returns:
            UserAuditLog: Registro creado
        """
        own_session = session is None
        if own_session:
            session = get_session()

        try:
            log_entry = UserAuditLog(
                user_id=user_id,
                username=username,
                changed_by_id=changed_by_id,
                changed_by_username=changed_by_username,
                action=action,
                field_changed=field_changed,
                old_value=old_value,
                new_value=new_value,
                changes_summary=changes_summary,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            session.add(log_entry)

            if own_session:
                session.commit()
                logger.info(
                    f"[Audit] {action} - User: {username} ({user_id}) by {changed_by_username}"
                )

            return log_entry

        except Exception as e:
            if own_session:
                session.rollback()
            logger.error(f"Error logging audit change: {e}")
            raise
        finally:
            if own_session:
                session.close()

    @staticmethod
    def get_user_history(
        user_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        Obtiene el historial de cambios de un usuario.

        Args:
            user_id: ID del usuario
            limit: Número máximo de registros
            offset: Offset para paginación

        Returns:
            Lista de registros de cambios
        """
        session = get_session()
        try:
            logs = (
                session.query(UserAuditLog)
                .filter(UserAuditLog.user_id == user_id)
                .order_by(UserAuditLog.created_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )

            return [log.to_dict() for log in logs]
        finally:
            session.close()

    @staticmethod
    def get_recent_changes(
        limit: int = 100, offset: int = 0, changed_by_id: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Obtiene los cambios recientes en el sistema.

        Args:
            limit: Número máximo de registros
            offset: Offset para paginación
            changed_by_id: Filtrar por quién hizo el cambio (opcional)

        Returns:
            Lista de registros de cambios
        """
        session = get_session()
        try:
            query = session.query(UserAuditLog)

            if changed_by_id:
                query = query.filter(UserAuditLog.changed_by_id == changed_by_id)

            logs = (
                query.order_by(UserAuditLog.created_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )

            return [log.to_dict() for log in logs]
        finally:
            session.close()

    @staticmethod
    def log_level_change(
        user_id: str,
        username: str,
        old_level_id: int | None,
        new_level_id: int,
        old_level_name: str | None,
        new_level_name: str,
        changed_by_id: str,
        changed_by_username: str,
        session: Session | None = None,
    ) -> UserAuditLog:
        """Registra un cambio de nivel de usuario"""
        return UserAuditService.log_change(
            user_id=user_id,
            username=username,
            action="update_level",
            changed_by_id=changed_by_id,
            changed_by_username=changed_by_username,
            field_changed="level_id",
            old_value={"level_id": old_level_id, "level_name": old_level_name},
            new_value={"level_id": new_level_id, "level_name": new_level_name},
            changes_summary={"from": old_level_name or "None", "to": new_level_name},
            session=session,
        )

    @staticmethod
    def log_permissions_change(
        user_id: str,
        username: str,
        changes: dict[str, dict[str, Any]],
        changed_by_id: str,
        changed_by_username: str,
        session: Session | None = None,
    ) -> UserAuditLog:
        """
        Registra cambios en permisos de usuario.

        Args:
            changes: Dict con formato {"field_name": {"old": value, "new": value}}
        """
        return UserAuditService.log_change(
            user_id=user_id,
            username=username,
            action="update_permissions",
            changed_by_id=changed_by_id,
            changed_by_username=changed_by_username,
            changes_summary=changes,
            session=session,
        )

    @staticmethod
    def log_profile_change(
        user_id: str,
        username: str,
        changes: dict[str, dict[str, Any]],
        changed_by_id: str,
        changed_by_username: str,
        session: Session | None = None,
    ) -> UserAuditLog:
        """Registra cambios en el perfil de usuario"""
        return UserAuditService.log_change(
            user_id=user_id,
            username=username,
            action="update_profile",
            changed_by_id=changed_by_id,
            changed_by_username=changed_by_username,
            changes_summary=changes,
            session=session,
        )
