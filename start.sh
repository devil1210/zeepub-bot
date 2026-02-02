#!/bin/bash

# Start cloudflared in the background if token is present
# Workaround: Ensure zeepubs_bot resolves to localhost for the tunnel
echo "127.0.0.1 zeepubs_bot" >> /etc/hosts

if [ -n "$TUNNEL_TOKEN" ]; then
    echo "Starting Cloudflare Tunnel..."
    cloudflared tunnel run --token "$TUNNEL_TOKEN" &
else
    echo "WARNING: TUNNEL_TOKEN not set. Cloudflare Tunnel will not start."
fi

# Start the bot
echo "Starting ZeePub Bot..."
# Detección inteligente del entorno (Docker vs VPS Local)
if [ -f "/root/zeepub_bot/venv/bin/python" ]; then
    PYTHON_EXE="/root/zeepub_bot/venv/bin/python"
elif [ -f "/app/venv/bin/python" ]; then
    PYTHON_EXE="/app/venv/bin/python"
else
    PYTHON_EXE="python3"
fi

exec $PYTHON_EXE run_with_api.py
