from fastapi import APIRouter

from .library import router as library_router
from .user import router as user_router

router = APIRouter(prefix="/v4")

router.include_router(user_router)
router.include_router(library_router)


@router.get("/health")
async def health_check():
    return {"status": "ok", "version": "4.0.0"}
