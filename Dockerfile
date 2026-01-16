# Etapa 1: Construcción del Frontend
FROM node:20-alpine as frontend-build
WORKDIR /app/frontend
COPY web_client/package*.json ./
RUN npm install
COPY web_client/ ./
RUN npm run build

# Etapa 2: Backend y Bot
FROM python:3.12-slim

WORKDIR /app

# Copiar archivos de requirements y código
# Copiar archivos de requirements y código
COPY requirements.txt ./
RUN apt-get update && apt-get install -y postgresql-client curl git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Install cloudflared
RUN curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && \
    dpkg -i cloudflared.deb && \
    rm cloudflared.deb

# Bake git hash
ARG GIT_COMMIT=unknown
ARG BUILD_DATE=unknown
RUN echo $GIT_COMMIT > version_hash.txt && echo $BUILD_DATE > build_date.txt

COPY . .

# Copiar el frontend construido desde la etapa anterior
COPY --from=frontend-build /app/frontend/dist /app/web_client/dist

# Variables de entorno por defecto (se pueden sobrescribir)
ENV LOG_LEVEL=INFO

# Exponer el puerto de la API
EXPOSE 8000

RUN chmod +x start.sh
CMD ["./start.sh"]
