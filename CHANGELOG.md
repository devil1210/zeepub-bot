# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

## [3.2.0] - 2025-12-15

### 🏗️ Refactorización Core
- **Bot Initialization**: Implementado `BotInitializer` para separar la lógica de arranque y gestión de schedulers.
- **Error Handling**: Implementado `ErrorHandler` centralizado con manejo inteligente de reintentos y notificaciones a admin.
- **Optimización HTTP**: `HTTPXRequest` configurado con connection pooling agresivo (size=20) y timeouts optimizados para alto rendimiento.

### 🛡️ Seguridad y Control
- **Rate Limiting**:
  - Implementado `RateLimiter` global asíncrono y thread-safe.
  - Aplicado límite de tasa al comando `/search` (30 req/min) para prevenir abuso.
- **Validación WebApp**: Agregada capacidad de validación de firma para `initData` en payloads de la Mini App.

### 🔧 Utilidades
- **Logging Estructurado**: Nuevo `StructuredLogger` para logs en formato JSON, facilitando la integración con sistemas de monitoreo futuros.

## [3.4.3] - 2025-12-15

### 🐛 Bugfixes
- **NameError**: Añadido import faltante de `asyncio` en `plugins/plugin_manager.py`.

## [3.4.2] - 2025-12-15

### 🐛 Bugfixes
- **ImportError**: Eliminada importación obsoleta de `Unauthorized` en `core/error_handler.py` (ahora `Forbidden`) que causaba crash en versiones recientes de `python-telegram-bot`.

## [3.4.1] - 2025-12-15

### 🧹 Calidad de Código
- **Linting**: Corregidos errores de estilo (`black`) y referencias indefinidas (`F821`) en `core/bot.py` detectados tras el release de la fase 3.

## [3.4.0] - 2025-12-15

### 🏗️ Arquitectura y Monitorización (Fase 3)
- **Monitoring**: Implementado `MetricsManager` (`utils/metrics.py`) exportando métricas de rendimiento (requests, descargas, usuarios activos) vía Prometheus.
- **Repository Pattern**: Implementada capa de persistencia asíncrona (`repositories/user_repository.py`) para desacoplar lógica de negocio del acceso a datos.
- **Async Migration**: Migración total a asíncrono de servicios críticos (`user_service`, `telegram_service`, `download_limiter`) eliminando bloqueos de I/O.
- **Lazy Loading**: Refactorizado `PluginManager` para carga diferida e inicialización concurrente de plugins, optimizando el tiempo de arranque.

## [3.3.0] - 2025-12-15

### 🚀 Optimización de Rendimiento
- **Async Caching**: Implementado `cache_service` con TTL para reducir carga en servidores externos y tiempos de espera.
- **OPDS Caching**: Integrado caché inteligente en la navegación de bibliotecas (10 minutos de expiración), mejorando drásticamente la velocidad de navegación.
- **Database Pooling**: Implementado `DatabaseManager` con pooling de conexiones para SQLite, mejorando la concurrencia en operaciones locales.

### 🧹 Calidad de Código
- **Type Hints**: Completada la cobertura de tipado estático en `config_settings.py` y nuevas clases de servicio.
- **Limpieza**: Refactorización de espacios en blanco y estilos para cumplir estrictamente con los estándares (flake8/black).

## [3.2.0] - 2025-12-15

### 🐛 Bugfixes
- **Telegram Service**: Corregido bug crítico que eliminaba archivos en canales de publicación si el comando se ejecutaba desde un grupo.
  - El auto-borrado ahora verifica estrictamente si el destino es el mismo chat de origen.

### ✨ Funcionalidades
- **Update Notification**: El mensaje de "Actualización Completada" ahora incluye, para los administradores, el mensaje del último commit (`git log -1`) que generó dicha versión, facilitando el seguimiento de cambios rápidos.

## [3.1.2] - 2025-12-15

### Calidad de Código
- **Correcciones de Estilo**: Aplicado formateo automático con `black` en `core/bot.py` y `handlers/callback_handlers.py` para resolver errores de linting (líneas en blanco excesivas y espacios en líneas vacías).

## [3.1.1] - 2025-12-15

### 🐛 Bugfixes
- **setlog**: Corregido el comando `/setlog` que no cambiaba efectivamente el nivel de logs.
  - Ahora actualiza tanto los loggers como los handlers (ambos niveles de filtrado de Python logging).
  - Agregado `httpcore`, `httpcore.http11`, `httpcore.connection` y `telegram.ext` a la lista de loggers actualizados dinámicamente.
  - Corregido `button_handler` global que interceptaba callbacks de plugins antes de que llegaran a sus handlers específicos.
- **HelpPlugin**: Restaurada la UI legacy del menú `/help` con todas las categorías (Inicio, Content, Admin, Datos, Mensajes, Donaciones, Links).
  - Implementado botón "Cerrar" con manejo interno del plugin.
- **SystemManagerPlugin**: 
  - Agregado método `setlog` faltante que causaba fallos silenciosos durante la inicialización del plugin.
  - La UI de `/setlog` ahora muestra el nivel actual y se actualiza dinámicamente al cambiar.

### 📦 Dependencias
- Agregado `python-dateutil==2.9.0.post0` para `stats_plugin`.

## [3.1.0] - 2025-12-14

### 🧩 Refactor Final (Help & System)
- **HelpPlugin**: La ayuda (`/help`) y su navegación interactiva ahora son un plugin independiente (`plugins/help_plugin.py`).
  - Activado con `ENABLE_HELP_PLUGIN`.
- **SystemManagerPlugin**: Ahora gestiona completamente los callbacks de botones de log (`setlog`), eliminando la última dependencia técnica en `handlers`.

### Limpieza
- `handlers/callback_handlers.py`: Reducido significativamente al migrar lógica de ayuda y logs.
- `handlers/command_handlers.py`: Completamente limpio de lógica de sistema y ayuda.

## [3.0.0] - 2025-12-14

### 🚀 Major Refactor (Plugins)
Re-arquitectura completa de la gestión del sistema para modularidad y seguridad.

#### Nuevos Plugins
- **UserManagerPlugin** (`plugins/user_manager_plugin.py`):
  - Comandos migrados: `/add_user`, `/remove_user`, `/reset`, `/id`, `/set_staff_status`.
  - Configurable: `ENABLE_USER_MANAGER`.
- **StatsPlugin** (`plugins/stats_plugin.py`):
  - Comandos migrados: `/stats` (Resumen y Lista por rol).
  - Configurable: `ENABLE_STATS_PLUGIN`.
- **SystemManagerPlugin** (Expandido):
  - Comando migrado: `/setlog` (Logging dinámico).

### Cambios Internos
- Limpieza masiva de `handlers/command_handlers.py`.
- Mejor separación de responsabilidades:
  - `handlers`: Solo lógica de navegación y libros.
  - `plugins`: Administración y herramientas.


### Refactorización
- **System Manager**: Migrada la lógica de sistema (`/update_system`, `/set_auto_delete_time`) a un nuevo plugin dedicado `SystemManagerPlugin`.
  - Configurable vía `ENABLE_SYSTEM_MANAGER` (por defecto `True`).
  - Mejora la limpieza del código base y seguridad.


### Correcciones
- **Soporte de Topics (Foros)**: Ahora `/reglas`, `/niveles` y `/list_msge` responden correctamente en el hilo (topic) donde fueron invocados, en lugar de enviarse al chat General.


### Correcciones
- **Comandos**: Agregado `/reglas` y otros comandos admin al mensaje de ayuda `/help` que faltaban.


### Funcionalidades
- **Group Manager**: Agregado comando `/reglas` (alias `/rules`). Usa un mensaje guardado con slug `reglas` (si existe) o un texto por defecto.


### Mejoras
- **Donations Plugin**:
  - El comando `/niveles` ahora busca un mensaje personalizado llamado `niveles` (configurable con `/add_msge`).
  - Soporta variables de precio dinámicas: `[white]`, `[vip]`, `[premium]`, `[duration]`, que se reemplazan con los valores configurados en `/set_price`.


### Correcciones
- **Custom Messages**: Ahora el comando `/list_msge <slug> [id]` permite probar el reemplazo de variables (ej: `[Nombre]`) simulando que se envía al usuario con el ID especificado.


### Mejoras
- **Group Manager Plugin**:
  - Soporte para variables en mensajes de bienvenida (Ej: `[Nombre]` -> Nombre del usuario).
  - Comandos `/authorize_group` y `/revoke_group` ahora aceptan un ID de chat opcional, permitiendo gestionar grupos por privado.
- **Custom Messages Plugin**:
  - Base de datos actualizada para almacenar el contenido de texto de los mensajes, permitiendo su modificación dinámica (reemplazo de variables) al enviarlos.


### Funcionalidades
- **Plugin Group Manager**: Gestión de grupos con autorización explícita y mensajes de bienvenida personalizados (integrado con `custom_messages`).
  - `/authorize_group`: Autorizar al bot.
  - `/revoke_group`: Revocar autorización.
  - `/set_group_welcome <slug>`: Definir mensaje de bienvenida desde los almacenados.


### Correcciones
- **Comando /help**: Se agregaron los comandos faltantes (`/sugerencia`) a la lista de ayuda visible.

### Cambios Importantes (Breaking Changes)
- **Base de Datos**: SQLite es ahora el motor por defecto. La integración con PostgreSQL se ha movido a un plugin opcional.
- **Configuración**: Nueva variable `ENABLE_POSTGRES_PLUGIN` (Default: False). Si tienías configurado PostgreSQL, debes establecer esto en `True` para mantener el comportamiento anterior, o dejarlo en `False` para migrar a SQLite.

### Funcionalidades
- **Plugin PostgreSQL**: `plugins/postgres_plugin.py` creado para gestionar la activación explícita de la base de datos externa.

### Correcciones
- **Comando /help**: Ahora muestra correctamente todas las categorías disponibles según el rol del usuario desde el inicio (antes requerían interacción para aparecer). Refactorización de lógica de teclado para consistencia.

### Funcionalidades
- **Plugin de Sugerencias**: Nuevo comando `/sugerencia` para enviar feedback a los administradores.
- **Refactorización Mini App**: La integración con la Web App ahora es un plugin independiente (`plugins/miniapp_plugin.py`) y la API se carga condicionalmente.
- **Configuración**: `ENABLE_MINI_APP` en `.env` para controlar la funcionalidad web.

## [2.3.0] - 2025-12-14

### Refactorización y Plugins
- **Arquitectura de Plugins**: Sistema modular activable mediante variables de entorno (`ENABLE_*`).
- **Plugin de Mensajes** (`ENABLE_CUSTOM_MESSAGES`):
    - Comandos: `/add_msge`, `/list_msge`, `/send_msge`.
    - Soporte para **Bienvenida Automática** (`/set_welcome`) y **Saludos Mejorados** (`/saludo`).
- **Plugin de Donaciones** (`ENABLE_DONATIONS`):
    - Comandos: `/donar`, `/niveles`, `/set_price`.
- **Plugin de Links** (`ENABLE_LINKS_MANAGER`):
    - Comandos: `/status_links`, `/link_list`, `/purge_link`.
- **Plugin de Mantenimiento** (`ENABLE_DB_MAINTENANCE`):
    - Herramientas de Backup/Restore y gestión de historial (`/backup_db`, `/export_history`, `/latest_books`, etc).



## [2.2.1] - 2025-12-12
### Correcciones
- **Notificaciones de Update**: Corregido bug donde la notificación de éxito se enviaba siempre al privado del usuario que lanzaba el comando. Ahora se envía correctamente al chat de origen (Grupo o Privado).

## [2.2.0] - 2025-12-12
### Resumen del Lanzamiento
Versión mayor que consolida todas las correcciones críticas del sistema de actualizaciones. Ahora Watchtower funciona correctamente gracias a la sincronización de la API de Docker y la política de reinicio. Se incluye el comando de actualización forzada y documentación actualizada.

### Funcionalidades
- **Nuevo Comando**: `⚠️ /update_system force` añadido al menú de ayuda (`/help` -> Admin). Permite forzar la reinstalación completa del contenedor incluso si no hay cambios en git.

### Correcciones Críticas (Recap)
- **Watchtower Race Condition**: Solucionado el fallo silencioso de actualizaciones cambiando `restart: always` por `restart: unless-stopped`.
- **Docker API**: Sincronizada versión de cliente (1.52) con el host para evitar rechazos de conexión.
- **Port Collision**: Movido puerto de Watchtower a 8081 para no chocar con Zitadel.

## [2.1.28] - 2025-12-12

### Configuración
- **Watchtower Fix Final**: Cambiado `restart: always` a `restart: unless-stopped` en el contenedor del bot. Esto resuelve la condición de carrera donde Docker reiniciaba el contenedor antes de que Watchtower pudiera recrearlo con la nueva imagen, causando que las actualizaciones fallaran silenciosamente a pesar de mostrar `Updated=1`.

## [2.1.27] - 2025-12-12

### Configuración
- **Watchtower Tuning**: Ajustado `DOCKER_API_VERSION=1.52` para coincidir exactamente con la versión del host. Se ha observado que versiones inferiores permitían la descarga de la imagen pero fallaban silenciosamente en la recreación del contenedor.

## [2.1.26] - 2025-12-12

### Funcionalidades
- **Force Update**: Añadido soporte para `/update_system force`. Permite reinstalar la versión actual o forzar el ciclo de actualización incluso si los commits coinciden (útil para cambios en Dockerfile o dependencias base).

## [2.1.25] - 2025-12-12

### Configuración
- **Watchtower Fix**: Restaurada la variable `DOCKER_API_VERSION` y actualizada a `1.45`. La eliminación anterior causó que Watchtower usara una versión cliente antigua (1.25) incompatible con el host moderno (min 1.44).

## [2.1.24] - 2025-12-12

### Configuración
- **Watchtower Port**: Cambiado el puerto expuesto de Watchtower a `8081` para evitar colisión con Zitadel (que usa el 8080). Internamente el bot sigue comunicándose por el puerto 8080 de la red Docker.

## [2.1.23] - 2025-12-12

### Configuración
- **Watchtower**: Eliminada la restricción `DOCKER_API_VERSION=1.44` para permitir la negociación automática con la API del host (v1.52). Esto debería solucionar el problema donde Watchtower descargaba la imagen pero no recreaba el contenedor.

## [2.1.22] - 2025-12-12

### Calidad de Código
- **Corrección Menor**: Eliminados espacios en blanco en líneas vacías (`W293`) para cumplir estrictamente con el linter.
- **Documentación**: Actualizado `README.md` con detalles sobre el sistema de actualizaciones robusto (filtrado de Watchtower y reinicio forzado).

## [2.1.21] - 2025-12-12

### Robustez
- **Update Fallback**: Implementado un mecanismo de "reinicio forzado" si Watchtower no detiene el contenedor automáticamente tras 10 segundos. Esto asegura que la actualización se aplique incluso si hubo problemas de permisos con Docker.

## [2.1.20] - 2025-12-12

### Calidad de Código
- **Linting**: Corregidos errores de espacios en blanco (`W293`, `E303`) reportados por `flake8` tras los últimos cambios.

## [2.1.19] - 2025-12-12

### Debug
- **Notificación de Update**: Añadido logging detallado en el arranque para diagnosticar por qué a veces no se envía el mensaje de éxito tras una actualización.
- **Robustez**: Asegurada la creación del directorio `data/` antes de guardar el estado de actualización.

## [2.1.18] - 2025-12-12

### Configuración
- **Watchtower Seleccionado**: Actualizada la configuración de Watchtower para que **solo** supervise y actualice el contenedor `zeepubs_bot`, ignorando otros servicios del VPS (como Zitadel, Postgres, etc.) para reducir ruido y evitar reinicios no deseados.
- **Docker Compose**: Se ha añadido `WATCHTOWER_LABEL_ENABLE=true` y la etiqueta correspondiente al servicio del bot.

## [2.1.17] - 2025-12-12

### Mejoras
- **Debug**: Comando `/status` ahora muestra explícitamente las descargas usadas vs totales (ej: "[Usadas: 3]") para facilitar el diagnóstico.
- **Estabilidad**: Reforzada la lógica interna del comando `/reset` para garantizar la consistencia en memoria.

## [2.1.16] - 2025-12-12

### Mejoras
- **Privacidad en Grupos**: Las descargas solicitadas en grupos públicos por usuarios normales ahora se envían forzosamente al **chat privado** del usuario, evitando spam y manteniendo la limpieza del grupo. Solo Admins/Staff pueden recibir archivos en el grupo (con auto-borrado).

## [2.1.15] - 2025-12-12

### Corregido
- **Regression**: Solucionado `NameError` en comando `/start` causado por eliminación accidental de variables durante un revert anterior.

## [2.1.14] - 2025-12-12

### Corregido
- **Comando Start en Grupos**: Se forza el envío de un nuevo mensaje en lugar de una respuesta (`reply_text`) para asegurar compatibilidad con temas (topics) y evitar fallos silenciosos en grupos.

## [2.1.13] - 2025-12-12

### Corregido
- **Comando Help**: Solucionado error lógico que impedía enviar el mensaje de ayuda a usuarios no administradores (Readers).

## [2.1.12] - 2025-12-12

### Changed
- **Infraestructura**: Desactivado PostgreSQL en `docker-compose.yml` por defecto para usar SQLite (`zeepub.db`), simplificando el despliegue y reduciendo el consumo de recursos.

## [2.1.11] - 2025-12-12

### Otros
- **Verificación**: Commit de prueba para validar que el sistema de actualizaciones funciona correctamente sin bucles.

## [2.1.10] - 2025-12-12

### Corregido
- **Update Loop**: Se ha forzado la invalidación de caché en el Dockerfile para asegurar que `version_hash.txt` se actualice correctamente en nuevas builds.

## [2.1.9] - 2025-12-12

### Corregido
- **Crash Loop**: Corregido `NameError: name 'Update' is not defined` en `services/telegram_service.py` causado por falta de importación en el parche anterior.

## [2.1.8] - 2025-12-12

### Corregido
- **Auto-borrado en Grupos**: Solucionada una importación circular (`core.bot` <-> `services.telegram_service`) que impedía la ejecución correcta del temporizador de borrado. La referencia a `job_queue` ahora se pasa explícitamente.

## [2.1.7] - 2025-12-12

### Corregido
- **Crash Loop**: Solucionado `ImportError` crítico causado por la falta de la clase `SettingsService`. Se ha implementado un wrapper asíncrono para mantener compatibilidad con los nuevos comandos.

## [2.1.6] - 2025-12-12

### Corregido
- **Comando `/set_auto_delete_time`**: Solucionado error interno al guardar la configuración (falta de inicialización del servicio) y corregida la inconsistencia de nombres de clave que impedía que el ajuste surtiera efecto.

## [2.1.5] - 2025-12-12

### Corregido
- **Generación de Slugs**: Restaurado el reemplazo explícito del carácter `×` por `x` (ej: "Hunter×Hunter" -> "HunterxHunter") que se había perdido en commits anteriores.

## [2.1.4] - 2025-12-12

### Corregido
- **Regresión UX en Grupos**: Solucionado bug crítico donde el mensaje de resumen se borraba incondicionalmente en grupos. Ahora persiste correctamente.
- **Aviso de Auto-borrado**: Restaurada la lógica que añade la advertencia "🗑️ Se borrará en X min" y programa la eliminación automática para descargas de administradores en grupos.

## [2.1.3] - 2025-12-12

### Cambiado
- **Mecanismo de Actualización**: Reemplazado uso de `git ls-remote` por API de GitHub (`httpx`) para verificar versiones, eliminado problemas de autenticación y dependencias de CLI.
- **Persistencia en Grupos**: El mensaje de información del libro (portada + metadatos) ahora persiste siempre en grupos para todos los usuarios, mejorando el contexto.
- **Notificación de Update**: Movida la lógica de guardado de estado *antes* del reinicio del contenedor para garantizar notificaciones de éxito resilientes.

### Corregido
- **Falta de Slug**: Restaurado el slug en los mensajes de archivo y resumen inicial que había desaparecido accidentalmente.
- **Formato de Slug**: Reemplazo automático del carácter `×` por `x` en la generación de slugs.
- **Race Condition**: Solucionado un problema donde el bot se reiniciaba antes de guardar el estado de actualización.

## [2.1.2] - 2025-12-12

### Agregado
- **Estadísticas Mejoradas**: Comando `/stats` con desglose detallado por roles (White, VIP, Premium).
- **Sistema de Baneos**: Soporte para rol `banned` con duración temporal. Accesible via `/add_user <id> banned <días>`.
- **Actualizaciones Automáticas**: Integración con Watchtower y nuevo comando `/update_system`.
- **Visualización de Versión**: Indicador de versión en `/status` y `/update_system`.

### Corregido
- **Estabilidad de Red**: Resolución DNS forzada (`8.8.8.8`) para mitigar errores de conexión.
- **Correcciones Técnicas**: Timeout extendido en Watchtower (60s), limpieza de linting (`flake8`) y arreglos de sintaxis.

## [2.1.0] - 2025-12-11

### Agregado
- **Integración ZITADEL**: Endpoint `/api/zitadel-action` para enriquecimiento de tokens con roles Kavita y validación de firma HMAC.
- **Gestión de Usuarios**: Nuevos comandos de admin (`/add_user`, `/remove_user`, `/set_price`, `/set_staff_status`) y roles de Staff.
- **Sistema de Donaciones**: Comando `/donar` con opciones de reporte y notificaciones, configuración de `DONATION_URL`.
- **Acceso Restringido**: Restricción de Mini App exclusiva para usuarios configurarbles (VIP+).
- **Configuración Dinámica**: Infraestructura para ajustes de beneficios y precios sin reinicio.
- **Documentación**: Actualización de `/help` y nueva variable `ZITADEL_SIGNING_KEY` en `README.md`.

### Corregido
- Eliminado texto hardcodeado "Semestral" en comando `/niveles`.
- Resueltas dependencias circulares y arreglados tests unitarios.
- Fix de espacios en blanco y linting general.

## [2.0.1] - 2025-12-05

### Agregado
- Lógica de reintento con backoff exponencial para descargas HTTP para manejar problemas con Cloudflare
- Logging detallado para diagnóstico de descargas y extracción de metadatos
- Sistema de releases automáticas con extracción de notas desde CHANGELOG
- Versionado semántico de imágenes Docker (major, major.minor, version)
- Documentación completa de versionado en `VERSIONING.md`
- `CHANGELOG.md` siguiendo estándar Keep a Changelog
- Registro de libros publicados en base de datos con historial completo
- Comando `/latest_books` para administradores con filtrado por chat
- Comando `/export_db` para exportar historial a CSV
- Sistema de importación de historial desde JSON de Telegram
- Comando `/clear_history` para limpiar historial de libros
- Informes semanales de validación de enlaces para editores
- Validación de enlaces en segundo plano con actualizaciones automáticas
- Comandos `/check_links` y `/status_links` para monitoreo de URLs
- Comando `/purge_link` para eliminar enlaces específicos

### Cambiado
- Mejorado formato de Vista Previa Facebook eliminando etiqueta duplicada
- Mejorado manejo de errores con mensajes más descriptivos sobre Cloudflare
- Optimizado parsing de metadatos EPUB con extracción centralizada
- Mejorado cálculo de tamaño de archivo para EPUBs grandes (>10MB)
- Mejorados labels de imágenes Docker con metadata del proyecto

### Corregido
- Error en formato de Vista Previa Facebook mostrando metadatos vacíos
- Problemas de descarga causados por bloqueos temporales de Cloudflare

## [2.0.0] - 2025-12-02

### Agregado
- Mini App de Telegram con interfaz web moderna
- API REST basada en FastAPI para integración con Mini App
- Soporte para publicación directa en Facebook desde Mini App
- Vista previa de posts de Facebook antes de publicar
- Modo administrador con destinos de publicación configurables
- Autenticación segura de usuarios con validación de `initData`
- Control de acceso basado en roles (Admin, Publisher, VIP)
- Integración con Cloudflare Tunnel para exposición segura de la API
- Validación persistente de URLs con PostgreSQL y SQLAlchemy
- URLs acortadas con hash SHA256 para compartir en Facebook
- Base de datos PostgreSQL para almacenamiento de URLs y metadatos
- Compilación multi-etapa de Docker para optimizar tamaño de imagen
- Workflow de CI para publicación automática de releases

### Cambiado
- Refactorizado núcleo del bot eliminando archivo monolítico
- Modularizados handlers en archivos separados por funcionalidad
- Mejorados mensajes de usuario con mejor UX y claridad
- Optimizado manejo de archivos con I/O asíncrono
- Mejorado parsing de metadatos EPUB con extracción de título interno
- Actualizado formato de mensajes de portada con mejor estructura

### Corregido
- Revertida configuración DNS manual que causaba lentitud
- Corregido cálculo de tamaño para archivos grandes
- Mejorado logging de errores en `fetch_bytes`
- Agregado manejo de errores para `query.answer()`

## [1.5.0] - 2025-11-28

### Agregado
- Comandos `/backup_db` y `/restore_db` para editores
- Soporte para copias de seguridad de SQLite y PostgreSQL
- Copias de seguridad diarias programadas automáticamente
- Extracción de URL del publisher desde HTML de EPUB
- Validación de credenciales de Facebook antes de publicar

### Cambiado
- Mejorada generación de slugs con limpieza extendida de caracteres
- Centralizado enriquecimiento de metadatos en función dedicada
- Optimizado formato de metadata para Facebook

### Corregido
- Manejo de `BadRequest` cuando thread de mensaje no existe
- Manejo elegante de IDs de thread inválidos en grupos

## [1.4.0] - 2025-11-27

### Agregado
- Soporte para chats grupales con respuestas en threads
- Comando `/debug_state` para debugging de estado de usuario
- Botones "Volver" en navegación de libros
- Opción de destino para editores al iniciar publicación

### Cambiado
- Mejorada detección de comandos específicos del bot en grupos
- Optimizada limpieza de estado temporal
- Pasado `message_thread_id` a todos los mensajes del bot
- Mejorado formato de mensajes con sinopsis en blockquote

### Corregido
- Resultados de búsqueda ahora aparecen en chat actual
- IDs de destino y origen correctamente establecidos

## [1.3.0] - 2025-11-26

### Agregado
- Extracción de título interno de archivos EPUB
- Análisis mejorado de series y volúmenes para mensajes
- Soporte para mostrar versión EPUB y fechas de publicación
- Comando `/export_db` para exportar base de datos a CSV
- Informes semanales de enlaces para editores

### Cambiado
- Mejorada extracción de metadatos EPUB con parsing OPF completo
- Optimizada generación de nombres de archivo EPUB
- Mejorado cálculo de tamaño para bytes y rutas de archivo

## [1.2.0] - 2025-11-21

### Agregado
- Soporte completo para chats grupales con topics de Telegram
- Búsqueda directa con `/search <término>`
- Logging de debug para consultas y resultados de búsqueda
- Almacenamiento de `message_thread_id` en estado de sesión

### Cambiado
- Eliminada restricción de solo chat privado
- Mejorada lógica de inicio de búsqueda para privado vs grupos
- Optimizada navegación eliminando mensajes antiguos

### Corregido
- Detección de comandos específicos del bot en grupos
- Thread ID correctamente pasado a mensajes

## [1.1.0] - 2025-11-20

### Agregado
- Soporte completo para Docker con Docker Compose
- Workflow de GitHub Actions para publicación de imágenes
- `DOCKER_README.md` con instrucciones de despliegue
- Script `publish.sh` para automatizar publicaciones

### Cambiado
- Actualizado README con instrucciones de Docker
- Mejorada estructura de archivos del proyecto
- Bot no envía respuestas predeterminadas en grupos

### Corregido
- Ignorados archivos de prueba de Python en `.gitignore`

## [1.0.0] - 2025-10-18

### Agregado
- Bot de Telegram funcional para descargas de EPUB
- Integración con servidor OPDS
- Sistema de navegación de libros por series y volúmenes
- Extracción de portadas de archivos EPUB
- Sistema de límite de descargas diarias
- Listas VIP y Premium con descargas ilimitadas
- Comandos básicos: `/start`, `/help`, `/status`, `/search`, `/cancel`

### Cambiado
- Priorizada portada del EPUB sobre la del servidor OPDS para mejor calidad

### Corregido
- Navegación dentro del bot al descargar EPUB
- Redirección del comando "volver a la página anterior"

[No Publicado]: https://github.com/devil1210/zeepub-bot/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/devil1210/zeepub-bot/compare/v2.0.1...v2.1.0
[2.0.1]: https://github.com/devil1210/zeepub-bot/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/devil1210/zeepub-bot/compare/v1.5.0...v2.0.0
[1.5.0]: https://github.com/devil1210/zeepub-bot/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/devil1210/zeepub-bot/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/devil1210/zeepub-bot/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/devil1210/zeepub-bot/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/devil1210/zeepub-bot/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/devil1210/zeepub-bot/releases/tag/v1.0.0
