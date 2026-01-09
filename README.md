# Zeepub Bot

**Zeepub Bot** es un bot de Telegram avanzado que permite buscar y descargar libros electrónicos en formato EPUB. Integra una **Mini App** (Web App) para una experiencia de usuario moderna, búsqueda por palabra clave, navegación por catálogos OPDS y un sistema robusto de límites de descarga.

![Bot Version](https://img.shields.io/badge/ZeePub_Bot-v6.1.0-blue?style=for-the-badge&logo=telegram)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.9%2B-yellow)
![Docker](https://img.shields.io/badge/docker-enabled-blue)

***

## 📋 Características v6 (Estable)

- **Librería Local (Local First)**: Indexación propia de metadatos para una búsqueda ultra-rápida e independiente.
- **Búsqueda Instantánea**: Motor SQLite FTS5 para encontrar libros por título, autor, serie o género.
- **UI Premium Minimalista**: Interfaz de Mini App pulida con efectos de cristal (Glassmorphism) y animaciones suaves.
- **Optimización de Imágenes**: Generación automática de miniaturas (thumbnails) para acelerar la carga en móviles.
- **Métricas Técnicas**: Conteo automático de palabras, páginas y estimación de tiempo de lectura.
- **Exportación Unificada**: Programador diario configurable que respalda tanto la caché de URLs como la base de datos de la librería.
- **Gestión de Niveles**: Sistema de cuotas para usuarios VIP y Premium con límites persistentes.
- **Arquitectura Modular (Plugins)**: Plugins activables para Mensajes Personalizados, Donaciones, Mantenimiento y más.

## 🧩 Plugins y Comandos Destacados

### 1. Mantenimiento y Datos (`ENABLE_DB_MAINTENANCE`)
- `/scan_library [force]`: (Admin) Escanea e indexa la biblioteca local.
- `/set_export_time HH:MM`: (Admin) Configura la hora de la exportación diaria (def: 04:00).
- `/export_db`: (Admin/Pub) Genera CSV de los enlaces registrados.
- `/verify`: (Admin) Verifica la consistencia de la base de datos de la librería.
- `/backup_db`: (Admin) Respaldo manual de la base de datos central.

### 2. Gestión de Usuarios (`ENABLE_USER_MANAGER`)
- `/refresh_user <uid>`: (Admin) Actualiza el perfil de un usuario desde Telegram.
- `/reset <uid>`: (Admin) Resetea el límite diario de descargas de un usuario.
- `/status`: Consulta el estado, nivel y cuota restante.

### 3. Mensajes y Grupos (`ENABLE_CUSTOM_MESSAGES`)
- `/set_welcome <slug>`: Configura mensaje de bienvenida dinámico.
- `/add_msge <id>`: Guarda el mensaje respondido para uso futuro.
- `/list_msge`: Lista mensajes guardados editables.

### 4. Core y Sistema
- `/start`, `/help`: Inicio y ayuda dinámica por niveles.
- `/menu`: Menú interactivo principal.
- `/update_system [force]`: (Admin) Actualización automática vía Watchtower.

***

## 📁 Estructura del Proyecto

```text
├── run_with_api.py            # Punto de entrada Principal (API + Bot)
├── config/                    # Configuración central (Pydantic-like stats)
├── core/                      # Lógica de inicialización y estados
├── api/                       # Backend FastAPI (Rutas Mini App y OPDS)
├── zeepub-web/                # Frontend React (Mini App)
├── plugins/                   # Arquitectura modular de comandos y features
│   ├── maintenance_plugin.py  # Escaneo, exportación y backups
│   ├── custom_messages_plugin.py # Gestión de plantillas y bienvenidas
│   └── user_manager_plugin.py # Gestión de niveles y límites
├── services/                  # Business Logic (Backups, Schedulers, Reports)
├── utils/                     # Utilidades (Caché, Limiter, Helpers)
├── data/                      # Persistencia (SQLite .db y Thumbnails)
└── tests/                     # Suite de pruebas unitarias
```

***

## 🛠️ Requisitos e Instalación

1. **Requisitos**: Docker, Docker Compose, un VPS con puerto 80/443 (o Cloudflare Tunnel).
2. **Configuración**: Copia `.env.example` a `.env` y rellena `TELEGRAM_TOKEN`, `ADMIN_USERS` y `OPDS_SERVER_URL`.
3. **Despliegue**:
   ```bash
   docker compose up -d --build
   ```

***

## 🛡️ Seguridad y Verificación

- **Validación HMAC**: Cada petición desde la Mini App se valida con la firma de Telegram (`initData`).
- **SQLite Engine**: Motor por defecto para máxima portabilidad (v6).
- **PEP8 Compliance**: Código 100% formateado con Black y verificado con Flake8.

## 📜 Licencia
Este proyecto está bajo la licencia **MIT**.