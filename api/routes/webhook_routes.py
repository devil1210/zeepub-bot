# api/routes/webhook_routes.py

import json
import logging
from typing import Any

from fastapi import APIRouter, Form, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from services.kofi_service import kofi_service

logger = logging.getLogger(__name__)


class WebhookRoutes:
    """
    Controlador de endpoints para webhooks externos (Ko-fi u otras plataformas).
    Responsabilidad única: Recepción, desempaquetado de payloads HTTP y respuesta status 200.
    """

    def __init__(self):
        self.router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])

    def get_router(self) -> APIRouter:
        return self.router

    def register_routes(self):
        """Registra los endpoints en el router."""
        self.router.add_api_route("/kofi", self.handle_kofi_webhook, methods=["POST"])
        self.router.add_api_route("/kofi/status", self.get_kofi_status, methods=["GET"])

    async def handle_kofi_webhook(
        self,
        request: Request,
        data: str | None = Form(default=None),
    ) -> Response:
        """
        Receptor oficial de Webhooks de Ko-fi.
        Ko-fi envía HTTP POST con Content-Type: application/x-www-form-urlencoded
        donde el campo 'data' contiene la carga útil en formato JSON string.

        También acepta Content-Type: application/json directo para pruebas o simulaciones.
        """
        payload: dict[str, Any] | str | None = None

        content_type = request.headers.get("content-type", "").lower()

        # 1. Caso estándar de Ko-fi: Form-URL-Encoded con campo 'data'
        if data:
            payload = data
        elif "application/x-www-form-urlencoded" in content_type:
            form = await request.form()
            payload = form.get("data")
        # 2. Caso alternativo / JSON directo para testing o integraciones custom
        elif "application/json" in content_type:
            try:
                payload = await request.json()
            except Exception as e:  # noqa: BLE001
                logger.error(f"Error decodificando JSON directo: {e}")
                raise HTTPException(status_code=400, detail="Invalid JSON format")
        else:
            # Intentar leer cuerpo crudo por si viene en form-urlencoded sin header estricto
            body_bytes = await request.body()
            body_str = body_bytes.decode(errors="ignore")
            if body_str.startswith("data="):
                from urllib.parse import parse_qs

                parsed = parse_qs(body_str)
                payload = parsed.get("data", [None])[0]
            elif body_str.startswith("{"):
                try:
                    payload = json.loads(body_str)
                except Exception:  # noqa: BLE001
                    payload = None

        if not payload:
            logger.warning(
                "⚠️ Webhook de Ko-fi recibido sin campo 'data' ni cuerpo válido."
            )
            raise HTTPException(
                status_code=400,
                detail="Missing 'data' field in request body. Ko-fi sends application/x-www-form-urlencoded with 'data'.",
            )

        # Procesar con el servicio de negocio
        result = await kofi_service.process_webhook(payload)

        if not result.get("success"):
            # Si el token de verificación fue rechazado
            if result.get("error") == "Invalid verification token":
                return JSONResponse(
                    status_code=403,
                    content={"success": False, "error": "Invalid verification token"},
                )
            return JSONResponse(
                status_code=400,
                content=result,
            )

        # Ko-fi requiere explícitamente código HTTP 200 para confirmar recepción exitosa
        return JSONResponse(
            status_code=200,
            content=result,
        )

    async def get_kofi_status(self) -> dict[str, Any]:
        """Verifica que el receptor de webhooks de Ko-fi está activo y listo."""
        return {
            "status": "active",
            "provider": "kofi",
            "endpoint": "/api/webhooks/kofi",
            "supported_methods": ["POST"],
            "expected_content_type": "application/x-www-form-urlencoded (field 'data')",
        }
