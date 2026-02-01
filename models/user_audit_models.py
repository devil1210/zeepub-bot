from datetime import datetime

from sqlalchemy import JSON, BigInteger, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from models.library_models import Base


class UserAuditLog(Base):
    """
    Registro de cambios (audit log) para usuarios.
    Almacena todas las modificaciones realizadas a los permisos y configuraciones de usuarios.
    """

    __tablename__ = "user_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Usuario afectado
    user_id = Column(
        BigInteger, ForeignKey("users.telegram_id"), index=True, nullable=False
    )
    username = Column(String(255))  # Snapshot del username en el momento del cambio

    # Quién hizo el cambio
    changed_by_id = Column(BigInteger, ForeignKey("users.telegram_id"), index=True)
    changed_by_username = Column(String(255))

    # Relaciones
    user = relationship("User", foreign_keys=[user_id], backref="audit_logs")
    admin = relationship("User", foreign_keys=[changed_by_id])

    # Tipo de cambio
    action = Column(
        String(50), nullable=False
    )  # 'update_level', 'update_permissions', 'update_profile', etc.

    # Detalles del cambio
    field_changed = Column(String(100))  # Campo específico modificado
    old_value = Column(JSON)  # Valor anterior
    new_value = Column(JSON)  # Valor nuevo

    # Metadata adicional
    changes_summary = Column(
        JSON
    )  # Resumen completo de todos los cambios en esta acción
    ip_address = Column(String(45))  # IPv4 o IPv6
    user_agent = Column(String(512))

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "changed_by_id": self.changed_by_id,
            "changed_by_username": self.changed_by_username,
            "action": self.action,
            "field_changed": self.field_changed,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changes_summary": self.changes_summary,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
