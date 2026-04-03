# src/api/auth.py
from fastapi import Header, HTTPException, status
from src.core.config import settings

def verify_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")):
    """Verifica la autenticación mediante la clave de API compartida."""
    # Si no se configuró clave en settings, permitimos acceso (dev)
    if not settings.AGENT_API_KEY:
        return
    
    if not x_api_key or x_api_key != settings.AGENT_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso denegado: Clave de API no válida o faltante."
        )
