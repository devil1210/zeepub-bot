from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from models.users import User
from services.user_service import UserService

from .auth import get_current_user, get_user_service

router = APIRouter(prefix="/user", tags=["user"])


class UISettingsUpdate(BaseModel):
    primary_color: str | None = None
    font_size: int | None = None
    theme: str | None = None


@router.get("/access")
async def get_user_access(user: User = Depends(get_current_user)):
    """
    Retorna el estado de acceso y configuración del usuario.
    Mantiene paridad con el esquema esperado por el frontend.
    """
    # Mapeo de paridad con el frontend legacy/actual
    return {
        "user_id": user.telegram_id,
        "username": user.username,
        "level": {
            "name": user.level.name if user.level else "Lector",
            "priority": user.level.priority if user.level else 1,
            "hasAccess": True,  # Si llegó aquí, tiene acceso básico
        },
        "ui": {
            "primaryColor": user.ui_settings.primary_color if user.ui_settings else "#3b82f6",
            "theme": user.ui_settings.theme if user.ui_settings else "dark",
        },
        "isAdmin": user.telegram_id in [133994080] or (user.level and user.level.priority >= 100),  # Ejemplo simple
    }


@router.post("/settings")
async def update_settings(
    settings: UISettingsUpdate,
    user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Actualiza las preferencias del usuario."""
    updated = await user_service.update_ui_settings(user.telegram_id, **settings.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")

    await user_service.commit_changes()
    return {"success": True}
