#!/bin/bash
echo "🔄 Actualizando ZeePub Bot..."

# Build/Image update
echo "📥 Descargando última versión del código..."
git pull

echo "🐳 Descargando imágenes Docker actualizadas..."
docker-compose pull

echo "🚀 Reiniciando contenedores..."
docker-compose up -d --remove-orphans

echo "🧹 Limpiando imágenes antiguas..."
docker image prune -f

echo "✅ ¡Actualización completada!"
