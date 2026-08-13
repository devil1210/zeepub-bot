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
        self.router.add_api_route(
            "/oauth/telegram/login",
            self.telegram_oauth_login,
            methods=["GET"],
            summary="Telegram OAuth 2.0 Login Redirect",
        )
        self.router.add_api_route(
            "/oauth/telegram/callback",
            self.telegram_oauth_callback,
            methods=["GET"],
            summary="Telegram OAuth 2.0 Callback",
        )
        self.router.add_api_route(
            "/oauth/logout",
            self.telegram_oauth_logout,
            methods=["GET", "POST"],
            summary="Logout and Clear Session",
        )

    async def telegram_oauth_login(self, request: Request):
        """Redirige al usuario al portal oficial de autenticación de Telegram OAuth 2.0 / OpenID Connect."""
        client_id = config.TELEGRAM_CLIENT_ID or "8180322203"
        host = request.headers.get("host", config.PUBLIC_DOMAIN or "zp-dev.sp-core.vip")
        scheme = "https" if "sp-core.vip" in host or request.headers.get("x-forwarded-proto") == "https" else "http"
        redirect_uri = f"{scheme}://{host}/api/oauth/telegram/callback"

        from urllib.parse import urlencode

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid profile",
        }
        telegram_auth_url = f"https://oauth.telegram.org/auth?{urlencode(params)}"
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url=telegram_auth_url)

    async def telegram_oauth_callback(self, request: Request, code: str | None = None, error: str | None = None):
        """Callback que procesa el código de autorización devuelto por Telegram OAuth 2.0."""
        from fastapi.responses import RedirectResponse

        if error or not code:
            logger.warning(f"Telegram OAuth cancelado o con error: {error}")
            return RedirectResponse(url="/?oauth_error=cancelled")

        client_id = config.TELEGRAM_CLIENT_ID or "8180322203"
        client_secret = config.TELEGRAM_CLIENT_SECRET
        host = request.headers.get("host", config.PUBLIC_DOMAIN or "zp-dev.sp-core.vip")
        scheme = "https" if "sp-core.vip" in host or request.headers.get("x-forwarded-proto") == "https" else "http"
        redirect_uri = f"{scheme}://{host}/api/oauth/telegram/callback"

        import httpx

        token_url = "https://oauth.telegram.org/token"

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    token_url,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": redirect_uri,
                    },
                    timeout=10.0,
                )

                if res.status_code != 200:
                    logger.error(f"Fallo en token exchange de Telegram OAuth ({res.status_code}): {res.text}")
                    return RedirectResponse(url="/?oauth_error=token_failed")

                data = res.json()
                id_token = data.get("id_token") or data.get("access_token")

                tg_user_id = None
                tg_username = None
                if id_token and "." in str(id_token):
                    import base64
                    import json

                    parts = str(id_token).split(".")
                    if len(parts) >= 2:
                        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
                        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                        tg_user_id = payload.get("sub") or payload.get("id")
                        tg_username = payload.get("preferred_username") or payload.get("username")

                if not tg_user_id and data.get("user"):
                    user_obj = data["user"]
                    tg_user_id = user_obj.get("id")
                    tg_username = user_obj.get("username")

                if tg_user_id:
                    from api.deps import get_telegram_user_id

                    current_user_id = await get_telegram_user_id(
                        cf_access_authenticated_user_email=request.headers.get("Cf-Access-Authenticated-User-Email"),
                        cf_access_user_email=request.headers.get("cf-access-authenticated-user-email"),
                        cf_access_jwt_assertion=request.headers.get("Cf-Access-Jwt-Assertion"),
                    )

                    if current_user_id and current_user_id != 0:
                        from services.user_service import link_telegram_to_user

                        await link_telegram_to_user(current_user_id, str(tg_user_id))

                    response = RedirectResponse(url="/?oauth_success=true")
                    response.set_cookie(
                        key="tg_session",
                        value=str(tg_user_id),
                        max_age=86400 * 30,
                        httponly=False,
                        samesite="lax",
                    )
                    return response

                return RedirectResponse(url="/?oauth_success=true")
        except Exception as e:
            logger.error(f"Excepción en callback de Telegram OAuth: {e}", exc_info=True)
            return RedirectResponse(url="/?oauth_error=exception")

    async def telegram_oauth_logout(self, request: Request):
        """Cierra sesión eliminando la cookie tg_session y redirige a la página principal."""
        from fastapi.responses import RedirectResponse
        host = request.headers.get("host", config.PUBLIC_DOMAIN or "zp-dev.sp-core.vip")
        redirect_url = f"https://{host}/cdn-cgi/access/logout" if "sp-core.vip" in host else "/"
        response = RedirectResponse(url=redirect_url)
        response.delete_cookie(key="tg_session")
        return response
