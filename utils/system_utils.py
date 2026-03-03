import os
import subprocess

CURRENT_VERSION = "v7.1.1"


def get_current_version() -> str:
    return CURRENT_VERSION


def get_commit_hash() -> str:
    # 1. Try file (Watchtower/Production)
    try:
        if os.path.exists("version_hash.txt"):
            with open("version_hash.txt") as f:
                return f.read().strip()[:7]
    except Exception:
        pass

    # 2. Try Git
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    return "unknown"


def get_version_string() -> str:
    v = get_current_version()
    h = get_commit_hash()
    if h and h != "unknown":
        return f"{v} ({h})"
    return v


def get_last_commit_message() -> str:
    """Obtiene el mensaje del último commit."""
    try:
        # git log -1 --pretty=%B
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "Actualización desconocida"
