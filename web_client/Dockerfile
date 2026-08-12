# ---------------------------------------------------
# Etapa 1: Build de la aplicación React (Vite)
# ---------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar manifiestos e instalar dependencias
COPY package*.json ./
RUN npm ci --prefer-offline --no-audit

# Copiar el código fuente y construir la distribución estática
COPY . .
RUN npm run build

# ---------------------------------------------------
# Etapa 2: Servidor de Producción con Nginx
# ---------------------------------------------------
FROM nginx:alpine AS runner

# Copiar archivos estáticos compilados y configuración de Nginx
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
