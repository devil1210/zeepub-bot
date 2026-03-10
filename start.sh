#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# start.sh — ZeePub Bot V4
# Punto de entrada del contenedor Docker.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

echo "🚀 Iniciando ZeePub Bot V4..."
echo "   Commit : $(cat /app/version_hash.txt 2>/dev/null || echo 'unknown')"
echo "   Build   : $(cat /app/build_date.txt 2>/dev/null || echo 'unknown')"

# ── Cloudflare Tunnel ─────────────────────────────────────────────────────────
if [ -n "${TUNNEL_TOKEN:-}" ]; then
    echo "🌐 Iniciando Cloudflare Tunnel..."
    cloudflared tunnel run --token "$TUNNEL_TOKEN" &
    TUNNEL_PID=$!
    echo "   PID tunnel: $TUNNEL_PID"
else
    echo "⚠️  TUNNEL_TOKEN no configurado. Cloudflare Tunnel no iniciará."
fi

# ── Esperar a PostgreSQL ──────────────────────────────────────────────────────
# docker-compose ya tiene healthcheck en el servicio db, pero por si acaso
# correr en entornos sin compose (kubernetes, etc.)
DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-zeepub}"
RETRIES=30

echo "⏳ Esperando a PostgreSQL en ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q 2>/dev/null; do
    RETRIES=$((RETRIES - 1))
    if [ $RETRIES -le 0 ]; then
        echo "❌ PostgreSQL no respondió tras 30 intentos. Abortando."
        exit 1
    fi
    sleep 2
done
echo "✅ PostgreSQL disponible."

# ── Migración: usuarios V3 → V4 (solo si se pide explícitamente) ─────────────
if [ "${RUN_MIGRATION:-false}" = "true" ]; then
    echo "♻️  Ejecutando migración V3→V4..."
    python scripts/migrate_users_v3_to_v4.py || echo "⚠️  Migración falló o ya ejecutada."
fi

# ── Arranque del bot + API ────────────────────────────────────────────────────
echo "🤖 Arrancando bot y API..."
exec python run_with_api.py
