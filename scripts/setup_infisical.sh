#!/bin/bash

# Script para automatizar la configuración de Infisical en nuevos entornos
# Uso: ./setup_infisical.sh [ENTORNO]

ENVIRONMENT=${1:-dev}

echo "🚀 Configurando Infisical para ZeePub Bot ($ENVIRONMENT)..."

if ! command -v infisical >/dev/null 2>&1; then
    echo "❌ Error: Infisical CLI no está instalado."
    echo "Instálalo con: npm install -g @infisical/cli"
    exit 1
fi

echo "🔑 Iniciando sesión..."
infisical login

echo "🔗 Vinculando proyecto..."
infisical init

echo "✅ Listo. Ahora puedes arrancar el bot con:"
echo "infisical run --env=$ENVIRONMENT -- python main.py"
