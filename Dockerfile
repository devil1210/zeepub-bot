# ─────────────────────────────────────────────────────────────────────────────
# ZeePub Bot — Dockerfile multi-stage optimizado para V4
# ─────────────────────────────────────────────────────────────────────────────
#
# STAGE 1 ─ Frontend (Node 20 Alpine)
# STAGE 2 ─ Runtime (Python 3.12 slim, sin dev deps)
#
# Build:
#   docker build -t zeepub-bot:v4 \
#     --build-arg GIT_COMMIT=$(git rev-parse --short HEAD) \
#     --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ) .
# ─────────────────────────────────────────────────────────────────────────────

# ── STAGE 1: Frontend ────────────────────────────────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

# Cache de dependencias NPM (invalidar solo si cambia package.json)
COPY web_client/package*.json ./
RUN npm ci --prefer-offline --no-audit

# Copiar fuente y construir
COPY web_client/ ./
RUN npm run build

# ── STAGE 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS runtime

# Metadatos OCI
LABEL org.opencontainers.image.title="ZeePub Bot V4"
LABEL org.opencontainers.image.description="Bot de Telegram para gestión de biblioteca EPUB con IA"
LABEL org.opencontainers.image.source="https://github.com/devil1210/zeepub-bot"

WORKDIR /app

# ── Dependencias del sistema ──────────────────────────────────────────────────
# Instalados en una sola capa y limpiados para reducir tamaño de imagen
RUN apt-get update && apt-get install -y --no-install-recommends \
    # DB client para healthcheck y scripts de migración
    postgresql-client \
    # Necesario para compilar psycopg2, lxml y Pillow
    libpq-dev \
    gcc \
    # curl para descargar cloudflared
    curl \
    # git para bake del hash de commit
    git \
    # Limpieza
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ── Cloudflared ───────────────────────────────────────────────────────────────
# Descarga solo el binario (no el instalador .deb completo)
RUN ARCH=$(dpkg --print-architecture) && \
    curl -fsSL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}" \
    -o /usr/local/bin/cloudflared && \
    chmod +x /usr/local/bin/cloudflared

# ── Dependencias Python ───────────────────────────────────────────────────────
# Copiar requirements ANTES del código fuente para aprovechar el cache de Docker
# (si solo cambia código pero no requirements, pip install se salta)
COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ── Código fuente ─────────────────────────────────────────────────────────────
# .dockerignore excluye: __pycache__, .git, node_modules, pgdata, .env, etc.
COPY . .

# Traer el frontend compilado desde Stage 1
COPY --from=frontend-build /app/frontend/dist /app/web_client/dist

# ── Metadata de versión ───────────────────────────────────────────────────────
ARG GIT_COMMIT=unknown
ARG BUILD_DATE=unknown
RUN printf '%s' "$GIT_COMMIT" > /app/version_hash.txt && \
    printf '%s' "$BUILD_DATE" > /app/build_date.txt

# ── Directorios de runtime ────────────────────────────────────────────────────
# Creados aquí para que pertenezcan a un usuario no-root
RUN mkdir -p /app/data /library /app/logs

# ── Usuario no-root (seguridad) ───────────────────────────────────────────────
RUN useradd --no-create-home --shell /bin/false -u 1000 zeepub && \
    chown -R zeepub:zeepub /app /library
USER zeepub

# ── Variables de entorno por defecto ──────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    LOG_LEVEL=INFO \
    PORT=8000

# ── Puerto de la API FastAPI ──────────────────────────────────────────────────
EXPOSE 8000

# ── Punto de entrada ──────────────────────────────────────────────────────────
RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]
