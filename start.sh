#!/bin/bash
# start.sh — Orquestador Zeepub-Nexus en el VPS (Auto-generado)

echo "--- 🏥 Iniciando Zeepub-Nexus ---"

# 1. Asegurar que Python trate a 'src' como un paquete raíz
export PYTHONPATH=$PYTHONPATH:/app

# 2. Iniciar Cloudflare Tunnel si existe el token en el entorno
if [ -n "$TUNNEL_TOKEN" ]; then
    echo "☁️ Iniciando túnel Cloudflare con el token proporcionado..."
    cloudflared tunnel --no-autoupdate run --token "$TUNNEL_TOKEN" &
else
    echo "⚠️ TUNNEL_TOKEN no detectado. Si necesitas acceso externo vía Cloudflare, configúralo en el .env."
fi

# 3. Lanzar la aplicación principal (Nexus Orchestrator)
# Usamos -m para que Python maneje correctamente las importaciones de paquetes
echo "🚀 Lanzando orquestador (Bot + API)..."
python -m src.nexus_start
