#!/bin/bash
set -e

# URL del repositorio (ajustar si es necesario)
REPO_URL="https://github.com/devil1210/zeepub-bot.git"
TARGET_DIR="/opt/zeepub-bot"

echo "Iniciando configuración inicial de Zeepub Bot..."

# 0. Verificación de Red y DNS
echo "Verificando conectividad..."
if ! ping -c 1 github.com >/dev/null 2>&1; then
    echo "Advertencia: No se puede resolver github.com. Intentando arreglar DNS..."
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        echo "Hay conexión a internet pero falla el DNS. Forzando Google DNS..."
        echo "nameserver 8.8.8.8" > /etc/resolv.conf
        echo "nameserver 1.1.1.1" >> /etc/resolv.conf
    else
        echo "Error Crítico: No hay conexión a internet (ni siquiera a 8.8.8.8)."
        echo "Por favor verifica la configuración de red de tu contenedor LXC en Proxmox."
        exit 1
    fi
fi

# 1. Obtener el código
if [ ! -d "$TARGET_DIR/.git" ]; then
    echo "Clonando repositorio (rama stable)..."
    # Asegurar que el directorio esté limpio o clonar en él
    if [ -z "$(ls -A $TARGET_DIR 2>/dev/null)" ]; then
       git clone -b stable "$REPO_URL" "$TARGET_DIR"
    else
       echo "El directorio no está vacío. Intentando init y pull..."
       cd "$TARGET_DIR"
       git init
       git remote add origin "$REPO_URL"
       git fetch origin
       git checkout -t origin/stable -f
    fi
else
    echo "El repositorio ya existe. Actualizando..."
    cd "$TARGET_DIR"
    git pull origin stable
fi

cd "$TARGET_DIR"

# 2. Configurar entorno virtual
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

echo "Instalando dependencias..."
./venv/bin/pip install -r requirements.txt

# 3. Configurar .env
if [ ! -f ".env" ]; then
    echo "Creando .env desde ejemplo..."
    cp .env.example .env
    # Forzar SQLite por defecto para LXC
    sed -i 's|DATABASE_URL=.*|DATABASE_URL=sqlite:///data/zeepub.db|' .env
    echo "Configurado para usar SQLite."
fi

# 4. Crear directorios de datos
mkdir -p data pgdata

# 5. Habilitar servicios
echo "Habilitando servicios..."
systemctl enable zeepub-bot
systemctl enable zeepub-tunnel

# 6. Iniciar servicios
echo "Iniciando servicios..."
systemctl start zeepub-bot || echo "Advertencia: zeepub-bot falló al iniciar (¿falta configuración?)"
systemctl start zeepub-tunnel || echo "Advertencia: zeepub-tunnel falló al iniciar (¿falta TUNNEL_TOKEN?)"

# 7. Deshabilitar este script para el próximo arranque
systemctl disable first-boot.service

echo "Configuración completada exitosamente."
