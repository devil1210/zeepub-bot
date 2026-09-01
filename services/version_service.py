"""
services/version_service.py
Servicio centralizado de control de versiones, changelog y actualizaciones para ZeePub Bot.
"""

import json
import logging
import os
import subprocess
import time
import httpx

from config.config_settings import config

logger = logging.getLogger(__name__)


class VersionService:
    @staticmethod
    def get_current_branch() -> str:
        """Determina la rama activa del bot (prioridad: env > version_branch.txt > git > config > fallback)."""
        # 1. Variable de entorno directa
        env_branch = os.getenv("GIT_BRANCH")
        if env_branch and env_branch.strip():
            return env_branch.strip()

        # 2. Archivo estático version_branch.txt o data/version_branch.txt
        for p in ("version_branch.txt", "data/version_branch.txt", "/app/version_branch.txt"):
            if os.path.exists(p):
                try:
                    with open(p) as f:
                        val = f.read().strip()
                        if val:
                            return val
                except Exception:
                    pass

        # 3. Git local en host o contenedor
        try:
            out = subprocess.check_output(
                ["git", "branch", "--show-current"], stderr=subprocess.DEVNULL
            ).decode().strip()
            if out:
                return out
        except Exception:
            pass

        # 4. Configuración cargada
        cfg_branch = getattr(config, "GIT_BRANCH", None)
        if cfg_branch and cfg_branch.strip() and cfg_branch != "main":
            return cfg_branch.strip()

        return "feat/integrate-web-client"

    @staticmethod
    def get_local_commit_hash() -> str:
        """Obtiene el hash del commit local activo (7 caracteres)."""
        for p in ("version_hash.txt", "data/version_hash.txt", "/app/version_hash.txt"):
            if os.path.exists(p):
                try:
                    with open(p) as f:
                        val = f.read().strip()
                        if val:
                            return val[:7]
                except Exception:
                    pass
        try:
            out = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
            ).decode().strip()
            if out:
                return out[:7]
        except Exception:
            pass
        return "Desconocido"

    @classmethod
    async def get_version_status(cls) -> dict:
        """
        Consulta el estado de versión contra GitHub API y construye el changelog.
        """
        branch = cls.get_current_branch()
        local_hash = cls.get_local_commit_hash()
        remote_hash = "Desconocido"
        remote_message = ""
        changelog = []
        is_up_to_date = False

        headers = {"User-Agent": "ZeePubBot/2.0"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(
                    f"https://api.github.com/repos/devil1210/zeepub-bot/commits/{branch}",
                    headers=headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    remote_hash = data.get("sha", "")[:7]
                    remote_message = data.get("commit", {}).get("message", "").split("\n")[0]
            except Exception as e:
                logger.error(f"[VersionService] Error consultando commit remoto en rama '{branch}': {e}")

            if local_hash != "Desconocido" and remote_hash != "Desconocido":
                is_up_to_date = (local_hash.lower() == remote_hash.lower())

            # Obtener lista de cambios / commits
            try:
                if not is_up_to_date and local_hash != "Desconocido" and remote_hash != "Desconocido":
                    comp_url = f"https://api.github.com/repos/devil1210/zeepub-bot/compare/{local_hash}...{remote_hash}"
                    comp_resp = await client.get(comp_url, headers=headers)
                    if comp_resp.status_code == 200:
                        commits_data = comp_resp.json().get("commits", [])
                        for c in commits_data:
                            msg = c.get("commit", {}).get("message", "").split("\n")[0]
                            c_sha = c.get("sha", "")[:7]
                            changelog.append(f"<code>{c_sha}</code> {msg}")

                # Si está al día o no hay comparación disponible, obtener los 5 commits más recientes
                if not changelog and branch:
                    rec_url = f"https://api.github.com/repos/devil1210/zeepub-bot/commits?sha={branch}&per_page=5"
                    rec_resp = await client.get(rec_url, headers=headers)
                    if rec_resp.status_code == 200:
                        for c in rec_resp.json():
                            msg = c.get("commit", {}).get("message", "").split("\n")[0]
                            c_sha = c.get("sha", "")[:7]
                            changelog.append(f"<code>{c_sha}</code> {msg}")
            except Exception as e:
                logger.warning(f"[VersionService] No se pudo obtener changelog detallado: {e}")

        return {
            "branch": branch,
            "local_hash": local_hash,
            "remote_hash": remote_hash,
            "is_up_to_date": is_up_to_date,
            "remote_message": remote_message,
            "changelog": changelog,
        }

    @staticmethod
    def save_update_state(
        chat_id: int | str,
        message_id: int | str | None = None,
        thread_id: int | str | None = None,
        branch: str | None = None,
        local_hash: str | None = None,
        remote_hash: str | None = None,
        changelog: list | None = None,
    ):
        """Guarda el estado previo a reiniciar para notificar al iniciar con éxito."""
        try:
            os.makedirs("data", exist_ok=True)
            state = {
                "chat_id": chat_id,
                "message_id": message_id,
                "message_thread_id": thread_id,
                "branch": branch or VersionService.get_current_branch(),
                "local_hash": local_hash or VersionService.get_local_commit_hash(),
                "remote_hash": remote_hash,
                "changelog": changelog or [],
                "timestamp": time.time(),
            }
            with open("data/update_state.json", "w") as f:
                json.dump(state, f)
            logger.info(f"[VersionService] Estado de actualización guardado en data/update_state.json: {state}")
        except Exception as e:
            logger.error(f"[VersionService] Error guardando estado de actualización: {e}")
