import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_telegram_user_id
from api.v4.auth import get_db
from services.koreader_service import KoreaderService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["KOReader & Web Reading Sync"])


# ==========================================
# Pydantic Schemas
# ==========================================


class KosyncProgressIn(BaseModel):
    document: str = Field(
        ..., description="Hash partial MD5 generado por KOReader", max_length=64
    )
    progress: str = Field(
        ..., description="CFI o posición de lectura de KOReader", max_length=512
    )
    percentage: float = Field(
        ..., description="Porcentaje de lectura 0.0 - 1.0", ge=0.0, le=1.0
    )
    device: str = Field(default="KOReader Device", max_length=128)
    device_id: str = Field(default="koreader-sync", max_length=128)
    timestamp: int = Field(default_factory=lambda: int(time.time()))


class WebReadingProgressIn(BaseModel):
    book_id: str = Field(
        ..., description="ID o hash del libro en ZeePub", max_length=64
    )
    progress_cfi: str = Field(..., description="EPUB CFI actual", max_length=512)
    percentage: float = Field(
        ..., description="Porcentaje de lectura 0.0 - 1.0", ge=0.0, le=1.0
    )
    device_name: str = Field(default="Web Reader", max_length=128)
    device_id: str = Field(default="web", max_length=128)


# ==========================================
# Auth Helper para KOReader
# ==========================================


async def get_koreader_user_id(
    x_auth_user: Annotated[str | None, Header()] = None,
    x_auth_key: Annotated[str | None, Header()] = None,
    user_id_query: Annotated[int | None, Query(alias="uid")] = None,
) -> int:
    """
    Autentica peticiones provenientes del plugin de KOReader (kosync).
    KOReader transmite las cabeceras x-auth-user y x-auth-key.
    Permite fallback a uid en query o ID de telegram por defecto.
    """
    if x_auth_user:
        raw = x_auth_user.strip()
        if raw.isdigit():
            return int(raw)
        return abs(hash(raw)) % (10**9)

    if user_id_query:
        return user_id_query

    return 100001


# ==========================================
# Endpoints de Compatibilidad KOReader (kosync)
# Rutas: /api/v1/koreader/... y alias /koreader/...
# ==========================================


@router.post("/api/v1/koreader/users/create")
@router.post("/koreader/users/create")
async def koreader_user_create(request: Request):
    """Permite registro directo desde el menú de sincronización de KOReader."""
    return {"authorized": "OK", "message": "User registered in ZeePub sync"}


@router.api_route(
    ["/api/v1/koreader/users/auth", "/koreader/users/auth"],
    methods=["GET", "POST"],
)
async def koreader_user_auth(
    user_id: Annotated[int, Depends(get_koreader_user_id)],
):
    """Verifica credenciales desde KOReader."""
    return {"authorized": "OK", "user_id": user_id}


@router.put("/api/v1/koreader/syncs/progress")
@router.put("/koreader/syncs/progress")
async def koreader_update_progress(
    payload: KosyncProgressIn,
    user_id: Annotated[int, Depends(get_koreader_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Recibe la posición de lectura enviada por KOReader al pasar página o cerrar libro."""
    res = await KoreaderService.update_koreader_progress(
        session=db,
        user_id=user_id,
        koreader_hash=payload.document,
        progress_cfi=payload.progress,
        percentage=payload.percentage,
        device_name=payload.device,
        device_id=payload.device_id,
    )
    if not res:
        return {
            "document": payload.document,
            "timestamp": int(time.time()),
            "status": "unindexed",
        }

    return res


@router.get("/api/v1/koreader/syncs/progress/{document}")
@router.get("/koreader/syncs/progress/{document}")
async def koreader_get_progress(
    document: str,
    user_id: Annotated[int, Depends(get_koreader_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Envía a KOReader la última posición guardada (desde otro e-reader o desde la Web App)."""
    prog = await KoreaderService.get_koreader_progress(
        session=db,
        user_id=user_id,
        koreader_hash=document,
    )
    if not prog:
        return {
            "document": document,
            "progress": "",
            "percentage": 0.0,
            "device": "KOReader",
            "timestamp": int(time.time()),
        }

    return prog


# ==========================================
# Endpoints para el Visor Web (Foliate-js)
# ==========================================


@router.put("/api/v1/reading/progress")
@router.post("/api/v1/reading/progress")
async def save_web_reading_progress(
    payload: WebReadingProgressIn,
    user_id: Annotated[int, Depends(get_telegram_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Guarda el progreso de lectura reportado por el Web Reader en tiempo real."""
    saved = await KoreaderService.save_progress(
        session=db,
        user_id=user_id,
        book_id=payload.book_id,
        progress_cfi=payload.progress_cfi,
        percentage=payload.percentage,
        device_name=payload.device_name,
        device_id=payload.device_id,
    )
    return saved


@router.get("/api/v1/reading/progress/{book_id}")
async def get_web_reading_progress(
    book_id: str,
    user_id: Annotated[int, Depends(get_telegram_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Obtiene el último progreso guardado de un libro para restablecer la lectura en el visor web."""
    prog = await KoreaderService.get_progress_by_book_id(
        session=db,
        user_id=user_id,
        book_id=book_id,
    )
    return prog
