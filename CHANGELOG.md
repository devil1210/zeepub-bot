# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [No Publicado]

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
