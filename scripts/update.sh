#!/bin/bash
echo "🔄 Actualizando ZeePub Bot y WebApp..."

echo "📥 Descargando última versión del código..."
git pull origin feat/integrate-web-client

echo "🔨 Compilando e instalando contenedores actualizados..."
docker compose -f docker-compose.prod-lib.yml up -d --build --remove-orphans

echo "🧹 Limpiando imágenes antiguas..."
docker image prune -f

echo "✅ ¡Actualización de WebApp y Bot completada exitosamente!"
