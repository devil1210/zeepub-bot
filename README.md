# Zeepub Bot

**Zeepub Bot** es un bot de Telegram avanzado que permite buscar y descargar libros electrónicos en formato EPUB. Integra una **Mini App** (Web App) para una experiencia de usuario moderna, búsqueda por palabra clave, navegación por catálogos OPDS y un sistema robusto de límites de descarga.

***

## 🚀 Características

- **Mini App Integrada**: Interfaz web moderna dentro de Telegram para navegar y descargar.
- **Búsqueda Global**: Busca libros en tu catálogo OPDS directamente desde Telegram.
- **Navegación OPDS**: Explora colecciones, géneros y novedades.
- **Descarga Directa**: Envía archivos EPUB al chat con metadatos enriquecidos (portada, sinopsis, autor).
- **Soporte para Grupos**: Funciona en grupos con topics/forums, respondiendo en el hilo correcto.
- **Seguridad**: Validación criptográfica de `initData` para prevenir suplantación de identidad.
- **Modo Administrador**:
  - Acceso a bibliotecas restringidas (Evil Mode).
  - Selector de destino para publicar libros en canales o chats específicos.
- **Límites de Descarga**: 
  - Sistema de niveles (Lector, VIP, Premium) con cuotas configurables.
  - Persistencia de contadores de descarga que sobreviven reinicios del bot.
  - Reset automático diario a medianoche (00:00).
  - Visualización del tiempo restante hasta el próximo reset en `/status`.
- **Comandos Dinámicos**:
  - `/help` muestra comandos específicos según el rol del usuario (Lector, Publisher, Admin).
  - Todas las descripciones en español.
  - Comandos básicos para todos los usuarios.
  - Comandos adicionales para Publishers (backup, links, exportación).
  - Comandos administrativos exclusivos para Admins (evil mode, reset, debug).
- **Arquitectura Moderna**:
  - **Backend**: Python (FastAPI + python-telegram-bot) asíncrono.
  - **Frontend**: React (Vite) servido estáticamente.
  - **Infraestructura**: Docker + Cloudflare Tunnel (sin abrir puertos).
  - **Base de Datos**: Soporte para PostgreSQL y SQLite con gestión de URLs acortadas.
- **Publisher Workflow**:
  - Menú de selección en `/start` para elegir destino de publicación (Telegram/Facebook).
  - Preferencia temporal que se aplica al siguiente libro seleccionado.
  - Publicación directa sin menús de interrupción.
- **Comandos de Publishers**:
  - `/export_db`: Exporta la tabla `url_mappings` a CSV.
  - `/link_list [limit]`: Lista los links acortados más recientes (hasta 50).
  - `/status_links`: Muestra el estado de los últimos 5 links con validación en tiempo real.
  - `/purge_link <hash>`: Elimina un link acortado específico de la base de datos.
- **Comandos de Administración** (Solo Admins):
  - `/backup_db`: Genera y envía un backup completo de la base de datos PostgreSQL.
  - `/restore_db`: Restaura la base de datos desde un archivo .sql.
  - `/reset <user_id>`: Resetea el contador de descargas de un usuario.
  - `/debug_state`: Muestra el estado actual del usuario (para debugging).
  - `/latest_books [chat_id]`: Ver últimos libros publicados (con filtro opcional por chat).
  - `/import_history`: Importar historial desde JSON de Telegram.
  - `/export_history`: Exportar historial a CSV.
  - `/clear_history confirm`: Borrar todo el historial de publicaciones.
- **Reportes Automáticos**:
  - Sistema de reportes semanales automáticos cada lunes a las 9:00 AM con estadísticas de links (total, válidos, rotos, tasa de éxito).
  - Los reportes se envían automáticamente a todos los publishers configurados.
- **Formato Mejorado de EPUBs**:
  - Extracción avanzada de metadatos con soporte para `epub:type="fulltitle"`.
  - Formato de título completo: `Serie ║ Colección ║ Título Interno`.
  - Preservación de puntuación y subtítulos multilinea.
  - Función centralizada de enriquecimiento de metadatos para consistencia.
- **Integración con Facebook**:
  - Preparación automatizada de posts con formato completo (título, metadata, sinopsis, info del archivo).
  - Publicación directa en grupos de Facebook con un solo clic.
  - Vista previa correcta del título (sin slug) para Facebook.
- **Sistema de Historial de Libros** (Solo Admins):
  - Registro automático de todos los libros publicados (desde bot y Mini App).
  - Almacenamiento de metadatos completos: maquetadores, demografía, géneros, ilustrador, traducción.
  - `/latest_books`: Ver últimos 10 libros publicados (todos los chats).
  - `/latest_books <chat_id>`: Filtrar libros por chat específico.
  - `/import_history`: Importar historial desde exportación JSON de Telegram.
  - `/export_history`: Exportar historial completo a CSV.
  - `/clear_history confirm`: Borrar todo el historial.

***

## 📁 Estructura del Proyecto

```text
├── main.py                    # Punto de entrada (Polling mode - Legacy)
├── run_with_api.py            # Punto de entrada Principal (API + Bot)
├── Dockerfile                 # Construcción Multi-Etapa (Node + Python)
├── docker-compose.yml         # Orquestación (Bot + Cloudflare Tunnel)
├── config/                    # Configuración
│   └── config_settings.py     # Variables de entorno y validación
├── core/                      # Lógica central
│   ├── bot.py                 # Inicialización del bot
│   └── state_manager.py       # Gestión de estado en memoria
├── api/                       # Backend FastAPI
│   ├── routes.py              # Endpoints de la Mini App
│   └── main.py                # Definición de la app FastAPI
├── zeepub-web/                # Frontend React (Mini App)
│   ├── src/                   # Código fuente React
│   └── vite.config.js         # Configuración de build
├── services/                  # Servicios del bot
│   ├── telegram_service.py    # Lógica de envío de EPUBs y FB posts
│   ├── epub_service.py        # Extracción de metadatos y títulos internos
│   ├── opds_service.py        # Navegación de catálogos OPDS
│   ├── history_service.py     # Registro y gestión de historial de libros
│   ├── weekly_reports.py      # Sistema de reportes automáticos semanales
│   ├── backup_scheduler.py    # Scheduler de backups diarios
│   └── daily_reset_scheduler.py # Scheduler de reset de descargas a medianoche
├── utils/                     # Utilidades
│   ├── security.py            # Validación de seguridad (HMAC)
│   ├── url_cache.py           # Gestión de URLs acortadas (SQLite/PostgreSQL)
│   ├── url_validator.py       # Validación periódica de links
│   └── download_limiter.py    # Sistema de límites y persistencia de descargas
└── tests/                     # Pruebas unitarias
```

***

## 🛠️ Requisitos

- **Docker** y **Docker Compose**
- Token de Telegram (BotFather)
- Token de Cloudflare Tunnel (Zero Trust)
- URL de un catálogo OPDS compatible

***

## 🔧 Instalación y Despliegue

La forma recomendada de desplegar es usando **Docker** y **Cloudflare Tunnel**. Esto garantiza que la Mini App tenga acceso HTTPS seguro sin necesidad de abrir puertos en tu router ni configurar certificados SSL manualmente.

### 1. Clonar el repositorio

```bash
git clone https://github.com/devil1210/zeepub-bot.git
cd zeepub-bot
```

### 2. Configurar Variables de Entorno

Crea un archivo `.env` basado en el ejemplo:

```bash
cp .env.example .env
nano .env
```

**Variables Críticas:**

```env
# Telegram
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ADMIN_USERS=123456789,987654321 # IDs de admins separados por coma

# Cloudflare Tunnel
TUNNEL_TOKEN=eyJhIjoi... (Token obtenido del panel Zero Trust)
PUBLIC_DOMAIN=tu-dominio.com (Ej: bot.midominio.com)

# OPDS
OPDS_SERVER_URL=https://tu-biblioteca-opds.com
OPDS_ROOT_START=/opds-root
OPDS_ROOT_EVIL=/opds-evil # Ruta para administradores

# Configuración
LOG_LEVEL=INFO
MAX_DOWNLOADS_PER_DAY=5

# Publishers (para comandos admin y reportes)
FACEBOOK_PUBLISHERS=123456789,987654321
FACEBOOK_PAGE_ACCESS_TOKEN=tu_token_de_fb
FACEBOOK_GROUP_ID=tu_group_id

# Dominio para links acortados
DL_DOMAIN=https://tu-dominio.com

# ZITADEL Actions
ZITADEL_SIGNING_KEY=tu_clave_de_firma_zitadel
```

### 3. Desplegar con Docker

El proyecto usa una construcción multi-etapa. Docker se encargará de:
1.  Compilar el frontend (React) usando Node.js.
2.  Copiar los archivos estáticos al contenedor de Python.
3.  Iniciar el bot y el túnel de Cloudflare.

```bash
docker compose up -d --build
```

### 4. Configurar Cloudflare Tunnel

En tu panel de [Cloudflare Zero Trust](https://one.dash.cloudflare.com/):
1.  Ve a **Access** > **Tunnels**.
2.  Selecciona tu túnel y ve a **Public Hostname**.
3.  Añade un nuevo hostname:
    *   **Public Hostname**: `tu-dominio.com` (El mismo que pusiste en `PUBLIC_DOMAIN`)
    *   **Service**: `HTTP` -> `zeepubs_bot:8000` (Nota: usa el nombre del servicio Docker, no localhost)

***

## 🛡️ Seguridad

El bot implementa medidas de seguridad para proteger la API de la Mini App:

- **Validación de `initData`**: El backend verifica la firma criptográfica de Telegram en cada petición (`X-Telegram-Data`). Esto impide que usuarios malintencionados suplanten la identidad de otros.
- **Sin Puertos Expuestos**: Gracias a Cloudflare Tunnel, no es necesario exponer el puerto 8000 a internet. Todo el tráfico entra cifrado por el túnel.

***

## 🔄 Sistema de Actualizaciones

El bot integra **Watchtower** para facilitar la actualización de imágenes Docker.

- **Comando**: `/update_system` (Solo Admin)
- **Funcionamiento**: Verifica versiones consultando la API de GitHub (sin dependencias de git local) y solicita a Watchtower que busque nuevas imágenes. Si encuentra una nueva versión, descarga la imagen y reinicia el contenedor automáticamente.
- **Filtrado Inteligente**: Configurado para que Watchtower solo supervise el contenedor del bot (`zeepubs_bot`), ignorando otros servicios del VPS.
- **Resiliencia**: Incluye mecanismo de "suicide fallback" que fuerza el reinicio del contenedor si Watchtower falla al detenerlo tras una actualización exitosa.
- **Verificación**: Persistencia robusta del estado para asegurar que el bot notifique el éxito tras el reinicio.

## 🛠 Desarrollo

El proyecto incluye pruebas unitarias para verificar la API y el comportamiento del bot.

```bash
# Ejecutar tests dentro del contenedor
docker exec zeepub_bot pytest tests/
```

***

## 🤝 Contribuciones

1.  Haz fork del repositorio.
2.  Crea una rama (`git checkout -b feature/nueva-funcion`).
3.  Haz tus cambios y commits.
4.  Envía un Pull Request.

***

## 📜 Licencia

Este proyecto está bajo la licencia **MIT**.

## 🧱 Persistencia opcional con Postgres + Alembic

Para entornos de producción recomendamos usar un DBMS gestionado (Postgres) en
vez del SQLite embebido. El proyecto incluye soporte para SQLAlchemy cuando la
variable `DATABASE_URL` está configurada; alembic está incluido para gestionar
las migraciones del esquema de `url_mappings`.

Ejemplo mínimo:

```bash
# en .env
DATABASE_URL=postgresql+psycopg2://zeepub:zeepub@db:5432/zeepub

# crear migraciones (en dev)
pip install -r requirements-dev.txt
alembic -c alembic.ini upgrade head
```

El `docker-compose.yml` del repo añade un servicio `db` (Postgres) y puedes
usar la variable `DATABASE_URL` para que la app use Postgres durante el runtime.