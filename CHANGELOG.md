# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [3.8.2] - 2025-12-16

### Corregido
- **Core**: Corrección de `awaits` faltantes en `message_handlers.py` y `command_handlers.py`.
- **Tests**: Actualización de mocks en tests para soportar la naturaleza asíncrona de `get_text`.
- **Bug**: Fix `UnboundLocalError: re` en `callback_handlers.py`.

## [3.8.1] - 2025-12-16

### Corregido
- **Ayuda**: Se solucionó un error en `/help` al intentar ver detalles de los nuevos comandos de variables (`usage` key missing).
- **Plugins**: Help Plugin v2.1.1.

## [3.8.0] - 2025-12-16

### Añadido
- **Variables Globales**: Sistema completo de variables globales.
    - **Admin**: Comandos `/set_var`, `/del_var` y `/vars` para definir variables estáticas usables en cualquier plantilla.
    - **Sistema**: Inyección automática de `[Nivel]`, `[Descargas]`, `[ResetTime]`, `[Expires]` en todas las plantillas (ya no requieren soporte explícito por comando).
- **Core**: Refactorización mayor de `get_text` a asíncrono para soportar consultas de base de datos dinámicas.

### Actualizado
- **Plugins**: Custom Messages v1.2.0, Help v2.1.0.

## [3.7.6] - 2025-12-16

### Refactorizado
- **Mensajes**: Centralización de textos por defecto en `TEMPLATE_REGISTRY`.
- **Limpieza**: Eliminado argumento `default_text` obsoleto en todos los handlers y plugins.
- **Comandos**: `/list_msge` ahora distingue entre mensajes personalizados (BD) y por defecto (Registry).

### Actualizado
- **Plugins**: Custom Messages v1.1.0, Help v2.0.1, Donations v1.1.1.

## [3.7.5] - 2025-12-16

### Mejorado
- **Templates**: Se aplica lógica condicional a `banned_message` (para ocultar fecha si es indefinido) y `donation_admin_alert` (para ocultar alias si no tiene).

## [3.7.4] - 2025-12-16

### Añadido
- **Plantillas**: Soporte para **lógica condicional** `{{if Variable}}...{{endif}}`.
- **Status**: El mensaje de estado por defecto ahora usa lógica condicional para ocultar campos vacíos (Vencimiento, Reinicio).

## [3.7.3] - 2025-12-16

### Añadido
- **Plantillas**: Implementada plantilla `status_message` para el comando `/status`.
- **Variables**: `[VersionBot]` disponible globalmente y variables específicas `[Nivel]`, `[Descargas]`, `[ResetTime]`, `[Expires]` para el estado.

## [3.7.2] - 2025-12-16

### Añadido
- **Variables Globales**: Ahora `[Nombre]`, `[Alias]`, `[ID]`, `[Fecha]` y `[Hora]` funcionan en **todas** las plantillas automáticamente.
- **Comandos**: Nuevo comando `/template_vars` para listar estas variables globales.

### Arreglado
- **Refactor**: Estandarización interna en la inyección de variables de usuario.

## [3.7.1] - 2025-12-16

### Arreglado
- **Variables**: Solucionado el problema donde la variable `[Nombre]` no se reemplazaba en los mensajes de ayuda interactiva.

## [3.7.0] - 2025-12-16

### Añadido
- **Plantillas**: Nuevo comando `/templates` para listar mensajes personalizables y variables.
- **Sistema**: Expansión de plantillas a donaciones (`/donar`, `/niveles`), ayuda y mensajes de sistema.

### Arreglado
- **Stats**: Corregido error `AttributeError` por falta de `await` en `get_daily_stats`.
- **Formato**: hashtags de `/latest_books` ahora son clickeables (`#slug` en vez de `#️⃣ slug`).

## [3.6.4] - 2025-12-15

### Arreglado
- **Versión**: Corregido el número de versión interno (`CURRENT_VERSION`) que no se había actualizado en `utils/helpers.py`.
- **Docker**: Actualizada etiqueta de imagen en `docker-compose.yml`.

## [3.6.3] - 2025-12-15

### Arreglado
- **Style**: Corrección definitiva de espacios en blanco (`E303`) que fallaban en CI.

## [3.6.2] - 2025-12-15

### Añadido
- **Sistema**: Implementada tarea de chequeo automático de actualizaciones (cada 6 horas).
- **Estabilidad**: Modo Seguro ("Safety Net"); si los plugins fallan, el bot inicia en modo de emergencia permitiendo usar `/update_system`.

### Arreglado
- **Metadata**: Corregida extracción de títulos en EPUBs removiendo comentarios HTML y artefactos `-->`.
- **Descargas**: Solucionado bug que mostraba `<coroutine object>` en lugar del número de descargas restantes (falta de `await`).
- **Código**: Correcciones de estilo y espacios en blanco (`black`).

## [3.6.1] - 2025-12-15

### Arreglado
- **Red**: Aumentado el `connect_timeout` a 15s (default 5s es muy agresivo) para evitar `ConnectError` en redes con latencia o VPN, manteniendo el resto de parámetros balanceados.

## [3.6.0] - 2025-12-15

### Cambiado
- **Cache**: Eliminados bloqueos globales en lecturas de `AsyncTTLCache`. Ahora las lecturas son no-bloqueantes.
- **TTL**: Incrementado el TTL de caché de usuario de 5 min a 60 min.
- **Moderación**: Optimizada la verificación de baneos para ejecutarse solo en chats privados.

## [3.5.10] - 2025-12-15

### Arreglado
- **Descargas**: Corregido error que abortaba descargas grandes (EPUBs) si tardaban más de 15 segundos. Ahora usa "smart timeout".

## [3.5.9] - 2025-12-15

### Cambiado
- **Dependencias**: Desbloqueada la versión de `httpcore` para mejorar rendimiento.

## [3.5.8] - 2025-12-15

### Cambiado
- **Red**: Restaurados los timeouts optimizados (Conexión 15s, Lectura 30s) tras descartar problemas internos.

## [3.5.7] - 2025-12-15

### Cambiado
- **Red**: Aumentados temporalmente los timeouts de red a 60s (luego revertido en v3.5.8).

## [3.5.6] - 2025-12-15

### Arreglado
- **Base de Datos**: Restaurado el decorador `@asynccontextmanager` en `DatabaseManager.connection`.

## [3.5.5] - 2025-12-15

### Arreglado
- **Dependencias**: Downgrade de `httpx` a `0.27.2` y `httpcore` a `1.0.5` para arreglar errores SSL.

## [3.5.4] - 2025-12-15

### Arreglado
- **Core**: Eliminada importación residual de `Unauthorized` que causaba cierres inesperados.

## [3.5.3] - 2025-12-15

### Cambiado
- **Base de Datos**: Optimización del pool de conexiones.
- **Caché**: Implementada caché TTL para roles de usuario.

## [3.5.2] - 2025-12-15

### Arreglado
- **Handlers**: Solucionado error `AttributeError` en menús de callback por falta de `await`.

## [3.5.1] - 2025-12-15

### Arreglado
- **Inicialización**: Solucionado `NameError: name 'config' is not defined`.

## [3.5.0] - 2025-12-15

### Añadido
- **Métricas**: Implementado servidor Prometheus y configuración de puerto.

### Cambiado
- **Base de Datos**: Implementado pooling robusto en `DatabaseManager`.
- **Rendimiento**: Extendido el uso de caché a todos los endpoints OPDS.

## [3.4.4] - 2025-12-15

### Arreglado
- **Red**: Cambiado puerto de Prometheus a 9090 para evitar conflictos.

## [3.4.3] - 2025-12-15

### Arreglado
- **Plugins**: Añadido import faltante de `asyncio` en `plugin_manager.py`.

## [3.4.2] - 2025-12-15

### Arreglado
- **Errores**: Eliminada importación obsoleta de `Unauthorized`.

## [3.4.1] - 2025-12-15

### Arreglado
- **Código**: Corregidos errores de estilo (`black`) y referencias indefinidas.

## [3.4.0] - 2025-12-15

### Añadido
- **Arquitectura**: Implementado `MetricsManager` y `Repository Pattern` (Fase 3).
- **Plugins**: Carga diferida e inicialización concurrente.

### Cambiado
- **Servicios**: Migración total a asíncrono (`user_service`, `telegram_service`).

## [3.3.0] - 2025-12-15

### Añadido
- **Caché**: Implementado `cache_service` con TTL.
- **Base de Datos**: Implementado `DatabaseManager` con pooling para SQLite.

### Cambiado
- **Código**: Refactorización de espacios y estilos (Clean Code).

## [3.2.0] - 2025-12-15

### Añadido
- **Notificaciones**: Inclusión del mensaje del commit en notificaciones de actualización.

### Arreglado
- **Telegram Service**: Corregido bug de eliminación de archivos en canales.

## [3.1.2] - 2025-12-15

### Cambiado
- **Código**: Correcciones de estilo automático (`black`).

## [3.1.1] - 2025-12-15

### Arreglado
- **Comandos**: Arreglado `/setlog` y restaurada UI de `/help`.
- **Sistema**: Corregidos fallos en `SystemManagerPlugin`.

### Añadido
- **Dependencias**: Agregado `python-dateutil`.

## [3.1.0] - 2025-12-14

### Cambiado
- **Refactor**: Ayuda (`/help`) y Sistema (`/setlog`) movidos a plugins independientes.
- **Limpieza**: Migración de lógica fuera de handlers.

## [3.0.0] - 2025-12-14

### Añadido
- **Plugins**: Arquitectura de plugins modular (`User`, `Stats`, `System`).
- **Comandos**: `/reglas`, `/niveles` con variables dinámicas.
- **Gestión**: Soporte para variables en mensajes de bienvenida.

### Cambiado
- **Base de Datos**: SQLite es ahora el motor por defecto. PostgreSQL movido a plugin.
- **Infraestructura**: Re-arquitectura de gestión del sistema.

### Arreglado
- **Topics**: Comandos responden correctamente en hilos de foros.
- **Ayuda**: Mostrados comandos faltantes en `/help`.

## [2.3.0] - 2025-12-14

### Añadido
- **Plugins**: Sistema modular de plugins activables (`ENABLE_*`).
- **Mensajes**: Plugin de mensajes personalizados y bienvenidas.
- **Donaciones**: Sistema de donaciones y niveles.
- **Mantenimiento**: Herramientas de backup y gestión de base de datos.

## [2.2.0] - 2025-12-12

### Añadido
- **Actualización**: Nuevo comando `/update_system force` para forzar reinstalación.

### Arreglado
- **Infraestructura**: Solucionada condición de carrera en Watchtower y colisiones de puerto.
- **Docker**: Sincronizada versión de API Docker.

## [2.1.0] - 2025-12-11

### Añadido
- **Integración**: Endpoint `/api/zitadel-action` para ZITADEL.
- **Usuarios**: Comandos de gestión de roles de staff y precios.
- **Acceso**: Restricción de Mini App por roles.

## [2.0.0] - 2025-12-02

### Añadido
- **Mini App**: Aplicación web integrada en Telegram.
- **API**: API REST con FastAPI.
- **Social**: Publicación en Facebook y validación de URLs.
- **Infraestructura**: Cloudflare Tunnel y Base de Datos PostgreSQL.

### Cambiado
- **Core**: Refactorización modular de handlers.
- **UX**: Mejorados mensajes y navegación.

## [1.5.0] - 2025-11-28

### Añadido
- **Backup**: Comandos `/backup_db` y `/restore_db`.
- **Metadata**: Extracción de URL de publisher.

### Arreglado
- **Grupos**: Manejo de errores en threads inexistentes.

## [1.0.0] - 2025-10-18

### Añadido
- **Lanzamiento Inicial**: Bot de descargas EPUB con integración OPDS.
- **Core**: Navegación, búsqueda, descargas limitadas y roles.
