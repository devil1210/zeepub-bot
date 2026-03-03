# api/routes/auth_routes.py

import hashlib
import hmac
import logging

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from config.config_settings import config

logger = logging.getLogger(__name__)


class AuthRoutes:
    """
    Handle authentication-related endpoints: Zitadel actions, tokens.
    Single Responsibility: Authentication, authorization, and token management.
    """

    def __init__(self):
        self.router = APIRouter(prefix="/api")

    def get_router(self) -> APIRouter:
        """Return the configured router."""
        return self.router

    async def zitadel_enrich_token(self, request: Request):
        """
        Endpoint para ZITADEL Actions v2 (Function: preuserinfo).
        Enriquece el token con roles y preferred_username.
        """
        try:
            logger.info("🔐 Zitadel token enrichment request")

            # Parse request body
            body = await request.body()

            if not body:
                return Response(content={"error": "Request body vacío"}, status_code=400)

            # Parse form data (Zitadel sends form-encoded data)
            try:
                from urllib.parse import parse_qs

                parsed_data = parse_qs(body.decode("utf-8"))

                # Extract token from form data
                token_data = parsed_data.get("token", [""])[0]

                if not token_data:
                    return Response(content={"error": "Token no encontrado en la solicitud"}, status_code=400)

                # Validate token signature
                if not self._validate_zitadel_signature(token_data, request):
                    return Response(content={"error": "Firma de token inválida"}, status_code=401)

                # Enrich token with user data
                enriched_data = self._enrich_token_data(token_data)

                return JSONResponse(content=enriched_data, headers={"Content-Type": "application/json"})

            except Exception as e:
                logger.error(f"❌ Error parsing Zitadel form data: {e}")
                return Response(content={"error": "Error al procesar solicitud"}, status_code=400)
        except Exception as e:
            logger.error(f"❌ Error in Zitadel token enrichment: {e}")
            return Response(content={"error": "Error processing action"}, status_code=500)

    def _validate_zitadel_signature(self, token: str, request: Request) -> bool:
        """Validate Zitadel token signature."""
        try:
            # Get Zitadel secret from config
            zitadel_secret = config.get("ZITADEL_SECRET")
            if not zitadel_secret:
                logger.warning("⚠️ Zitadel secret not configured")
                return False

            # Calculate expected signature
            expected_signature = hmac.new(zitadel_secret.encode(), token.encode(), hashlib.sha256).hexdigest()

            # Get actual signature from headers
            actual_signature = request.headers.get("X-Zitadel-Signature", "")

            # Compare signatures
            return hmac.compare_digest(expected_signature, actual_signature)

        except Exception as e:
            logger.error(f"❌ Error validating Zitadel signature: {e}")
            return False

    def _enrich_token_data(self, token: str) -> dict:
        """Enrich token with additional user data."""
        try:
            # This would integrate with actual user service
            # For now, returning basic enrichment

            enriched_data = {
                "token": token,
                "enriched": True,
                "timestamp": "2025-03-02T00:00:00Z",
                "version": "2.0",
                "preferred_username": "zeepub_user",
                "roles": ["user", "reader"],
                "permissions": ["read:library", "download:books"],
            }

            logger.info("✅ Token enriched successfully")
            return enriched_data

        except Exception as e:
            logger.error(f"❌ Error enriching token data: {e}")
            return {"token": token, "enriched": False, "error": "Error en el enriquecimiento"}

    def register_routes(self):
        """Register all authentication routes."""
        self.router.add_api_route(
            "/zitadel-action",
            self.zitadel_enrich_token,
            methods=["POST"],
            summary="Zitadel token enrichment",
            description="Enrich Zitadel token with user roles and preferences",
        )
