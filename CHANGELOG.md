# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [v4.7.5] - 2025-12-27
### Fixed
- Fixed loading spinner alignment across all Mini App pages (Catalog, Book Details, Admin).

## [v4.7.4] - 2025-12-27

## [v4.7.3] - 2025-12-27

## [v4.7.2] - 2025-12-27

## [v4.7.1] - 2025-12-27

## [v4.7.0] - 2025-12-27

## [v4.6.9] - 2025-12-27

## [v4.6.8] - 2025-12-26
- Reverted networking and HTTP request behavior to match the stable v4.5.1 baseline.
- Reduced strictness on OPDS authentication (now ignored for placeholder credentials).
- Fixed downloads for setups that don't expect custom User-Agents or invalid Auth headers.

## [v4.6.7] - 2025-12-26

## [v4.6.6] - 2025-12-26
### Fixed
- (Internal) Added debug logging for authentication status.

## [v4.6.4] - 2025-12-26
### Fixed
- Fixed authenticated downloads in Mini App: `fetch_bytes` now uses `OPDS_AUTH` credentials (resolves issues with Kavita and other private servers).

## [v4.6.3] - 2025-12-26
### Added
- New `/set_version <tag>` command in `SystemManagerPlugin` for administrators to dynamically change the bot's image version in `docker-compose.yml`.

## [v4.6.2] - 2025-12-26
## [v4.6.1] - 2025-12-26

## [v4.5.7] - 2025-12-26
**Maintenance:**
- **Versioning:** Synchronized bot internal version reporting with the actual release tag (`v4.5.7`).
- **Fixes:** Consolidated fixes from v4.5.6 (Catalog Access), v4.5.5 (Download History, Security).

## [v4.5.6] - 2025-12-26

**Critical Fixes:**
- **Catalog Access:** Fixed a regression where the root catalog URL (`/`) was not correctly resolving to the configured Start Catalog, causing loading failures for all users. Default behavior now correctly handles root requests.

## [v4.5.5] - 2025-12-26

**Fixes:**
- **Navigation:** Fixed "Subir Nivel" button in Catalog to correctly use OPDS hierarchy (`rel="up"`) when local history is empty.
- **Download History:** Fixed a backend crash in `DownloadRepository` that prevented downloads from being recorded and displayed.
- **Security:** Reinforced OPDS access control. Non-admins are now strictly blocked from the "Evil" catalog, and admins/staff must explicitly request it. All users default to the "Start" catalog.

## [v4.5.2] - 2025-12-26

### Added
- **Performance - Tunneling**: Implementado "Modo Túnel" para navegación OPDS. Nuevo endpoint `/api/tunnel/opds` que streamea XML directamente evitando el procesamiento pesado del bot.
- **Frontend - Cliente OPDS**: Integrado parser XML ligero (`fast-xml-parser`) en la Mini App para consumo directo del túnel.

### Fixed
- **Acceso - New Users**: Corregida lógica crítica en `user_service` que impedía el acceso al catálogo a usuarios nuevos (no registrados en DB). Ahora tienen acceso "Lector" por defecto.
- **API - Feed**: Corregido bug en la lógica de renombrado de "Todas las bibliotecas" donde el título modificado no se reflejaba en la respuesta final.
- **Acceso - Mini App**: Modificada la API `/feed` para permitir acceso a usuarios con `has_mini_app_access` (User Level).
- **UI - Mini App**: Centrado correcto de los indicadores de carga (Spinners) en Catálogo, Búsqueda y Detalle de Libro.
- **UI - Admin Mode**: Corregida fuga de estado donde usuarios no administradores podían quedar atrapados en "Admin Mode".

## [v4.5.1] - 2025-12-26 (Internal)
- *Release consolidado en v4.5.2 debido a mejoras inmediatas de rendimiento.*

## [v4.5.0] - 2025-12-25

### Added
- **Mini App - Navegación Nativa**: Implementado botón de retroceso nativo de Telegram que se muestra automáticamente en páginas secundarias.
- **Mini App - Nivel de Usuario**: Nuevo badge que muestra el nivel del usuario (Lector, Premium, Admin, etc.) con colores personalizados en la página principal.
- **Mini App - Configuración de Interfaz**: Nueva página `/interface-config` con controles completos de personalización:
  - Selector de tema (modo claro/oscuro)
  - Paleta de 6 colores predefinidos para tema principal
  - Slider de escala UI (80% - 120%) para ajustar tamaño de fuente y elementos
  - Todas las configuraciones persisten en localStorage
- **Mini App - Menú Estado**: Agregado acceso directo a "Estado" en el menú principal de funciones.
- **API - User Level**: Nueva función `getUserLevel()` para obtener información del nivel de usuario desde el endpoint `/api/user/access`.
- **Componente - UserLevelBadge**: Componente reutilizable para mostrar nivel de usuario con ícono Shield y estilos color-coded.

### Changed
- **Mini App - Navegación**: Eliminada la barra de navegación inferior (BottomNav). La navegación ahora se realiza mediante el botón nativo de Telegram y enlaces directos.
- **Mini App - Layout**: Reducido padding inferior de `pb-20` a `pb-4` al eliminar la barra de navegación.

### Technical
- Agregadas variables CSS `--font-scale` y `--spacing-scale` en `globals.css` para soporte de escalado dinámico.
- Configuración del botón BackButton nativo con show/hide automático según la ruta actual.
- Todo el código y comentarios en español.
- Commits separados para cada funcionalidad permitiendo reversión puntual.

## [v4.4.12] - 2025-12-24

### Added
- Per-user download history tracking: New `download_history` table stores each download.
- Download history display on Downloads page showing last 10 downloads with title, author, date, and file size.
- `DownloadRepository` for managing download history records.
- `user_downloads_history` API endpoint to retrieve download history.

### Changed
- Downloads page now displays actual download history instead of being empty.
- Download logic automatically records each successful download in the history.

## [v4.4.11] - 2025-12-24

### Added
- Real user status data display: Status page now shows actual user level and download information from the database.
- New `user_status` API action that returns user level, downloads used/remaining, and time until reset.
- 5-minute cache expiration for access control data: Level changes now automatically reflect within 5 minutes.
- Debug logging for user status data flow.

### Changed
- Status page now fetches real data from the backend instead of using static values.
- Downloads page now displays real user download statistics from the database.
- Added support for unlimited downloads display for premium users.
- Access control cache now expires after 5 minutes, ensuring fresh data on level changes.

## [v4.4.10] - 2025-12-24

### Changed
- Moved "Mis Enlaces" from the main functions menu to the Admin Panel for better organization.
- All link management tools are now centralized in the Admin Panel alongside other administrative features.

## [v4.4.9] - 2025-12-24

### Changed
- Moved "Gestión Accesos" from the main functions menu to the top of the Admin Panel for better organization.
- All administrative tools are now centralized in the Admin Panel when Admin Mode is enabled.

## [v4.4.8] - 2025-12-24

### Changed
- Refined Home Page layout: Moved "Panel Administrador" to the bottom of the page to prioritize functional menu items.

## [v4.4.7] - 2025-12-24

### Added
- New "Admin Mode" switch in Home Page for administrators.
- Instant access verification using local caching (`localStorage`).
- Integrated essential bot settings (Business Mode, Privacy) into the Admin Mode view.

### Changed
- Removed the separate Settings page to simplify navigation.
- Removed "Ajustes" from the bottom navigation bar.

## [v4.4.6] - 2025-12-24

### Changed
- Restricted access to the Settings page to admin users only.
- Hidden the "Ajustes" navigation item for non-admin users in the bottom navigation.

## [v4.4.5] - 2025-12-24

### Added
- Integrated new `v0` interface update across the entire Mini App.
- Implemented `AccessGuard` component for unified access control on all pages.
- Added smooth theme-aware loading states during access verification.

### Fixed
- Improved Telegram WebApp initialization (expand and background colors).
- Optimized navigation by switching to Next.js `Link` components.

### Changed
- Refined Home Page design with a modern card-based menu.
- Updated `BottomNav` with refreshed icons and styling.
- Preserved and unified "Mi Catálogo" and "Gestión Accesos" into the new design.

## [v4.4.4] - 2025-12-24
### Fixed
- **Pruebas - Estabilidad**: Refactorización profunda de la suite de pruebas para eliminar la contaminación de estado global y errores de tipo (`TypeError`).
- **Pruebas - Aislamiento**: Migración de mocks a nivel de módulo a fixtures aislados de pytest, garantizando un entorno limpio para cada prueba.
- **Backend - Seguridad**: Corregida precedencia en `get_effective_user` para asegurar que los administradores definidos en `config.ADMIN_USERS` tengan prioridad sobre la base de datos.
- **Core - Estabilidad**: Implementado sistema de limpieza automática de `sys.modules` en la suite de pruebas para evitar conflictos entre mocks de diferentes archivos.
- **Core - Versión**: Corregido desajuste de versión (v4.4.4) y formato del mensaje de inicio (eliminado "v" duplicado).
- **CI/CD**: Resueltas advertencias de deprecación (`utcnow`, `load_module`) y añadida dependencia `python-multipart`.

## [v4.4.3] - 2025-12-24
### Fixed
- **Código - Calidad**: Corregidos numerosos errores de linting y estilo (E302, W293, E303, E261) para cumplir con PEP 8.
- **Backend - Bug**: Corregido error `F821` (undefined name 'action') en el controlador de la Mini App que podía causar fallos en la verificación de acceso.
- **Core**: Limpieza de espacios en blanco y optimización de inicialización en `core/bot.py`.

## [v4.4.2] - 2025-12-24
### Fixed
- **Infraestructura**: Detenida instancia duplicada del bot en el host que causaba conflictos (error 409) con la instancia de Docker. Desactivado el servicio `zeepub-bot.service`.
- **Frontend - Seguridad**: Solucionada condición de carrera en `useAccessControl` que causaba redirecciones inapropiadas o cuelgues al cargar la página de "Control de Acceso".
- **Backend - Logging**: Agregados logs diagnósticos en los endpoints de verificación de acceso para mejor trazabilidad.

## [v4.4.1] - 2025-12-24
### Fixed
- **Admin - UX**: Corregido fallo que impedía listar niveles en el Panel de Administración debido a falta de cabeceras de autenticación.
- **Frontend - Core**: Expuesto el estado `isAdmin` en el contexto global de la Mini App para verificaciones de permisos más seguras.
- **Backend - Logging**: Silenciados logs excesivamente ruidosos de `aiosqlite` y `httpcore` en modo debug.

## [v4.4.0] - 2025-12-24
### Fixed
- **Seguridad - Core**: Corregido fallo que bloqueaba el acceso a administradores definidos vía `/add_user` o `config.ADMIN_USERS`.
- **DB - Sincronización**: Ahora el comando `/add_user admin` sincroniza automáticamente el nivel de usuario (`level_id`) y la tabla de administradores corporativa.
- **API - Acceso**: Unificada la lógica de privilegios entre el bot y la Mini App mediante `get_effective_user`.
- **Servicio**: Asegurado que todos los roles de sistema (Admin, Staff, Premium) tengan acceso por defecto a la Mini App.

## [v4.3.9] - 2025-12-24
### Added
- **Mini App - UX**: Rediseño de la página de "Acceso Restringido" con mejores opciones de contacto.
- **Admin - UX**: El "Control de Acceso" ahora está integrado dentro de la página de **Ajustes** para mayor coherencia.
- **Admin - Funcionalidad**: Nueva interfaz de control de niveles con indicadores visuales de estado (Activo/Inactivo).
- **Backend**: Agregados alias de rutas para compatibilidad con el nuevo sistema de guardado de niveles.

## [v4.3.8] - 2025-12-24
### Added
- **Admin - UX**: Nueva página de "Gestión de Accesos" (`/admin/levels`) exclusiva para administradores.
- **Admin - Funcionalidad**: Interfaz para activar/desactivar permisos del Mini App por nivel de usuario con guardado persistente.
- **Home**: Agregado acceso directo a la gestión de niveles en el menú principal para administradores.

## [v4.3.7] - 2025-12-24
### Added
- **Mini App - Seguridad**: Implementada página de "Acceso Denegado" (`/no-access`) para usuarios sin permisos.
- **Mini App - UX**: Guard de acceso global que detecta automáticamente si el usuario tiene permiso y redirige según corresponda.
- **Frontend**: Reconstrucción total de la Mini App con las últimas protecciones de seguridad.

## [v4.3.6] - 2025-12-24
### Added
- **Acceso - Niveles**: Implementado sistema de control de acceso por niveles (Tiered Access Control) en base de datos.
- **Niveles Predefinidos**: Administrador, Staff, Premium, VIP, Patrocinador y Lector (con prioridades y permisos específicos).
- **API - Seguridad**: Nuevos endpoints `/api/user/access` y `/api/admin/levels` (GET/PUT) para gestión remota de permisos.
- **Seguridad**: Decorador `require_mini_app_access` y validación automática en cada petición según el nivel del usuario.
### Fixed
- **Mini App - Roles**: Integrado `get_effective_user` para leer roles directamente de la base de datos (resolviendo el problema de acceso para Admins/Staff manuales).
- **Código - Calidad**: Corregidos numerosos errores de linting (bare excepts, undefined names, blank lines) en `api/` y `core/`.

## [v4.3.4] - 2025-12-21
### Fixed
- **Mini App - Roles**: Corregida la definición de Staff para incluir `WHITELIST` y `FACEBOOK_PUBLISHERS`, resolviendo el error de carga de catálogo para estos usuarios.
- **Backend - Logging**: Agregados logs diagnósticos exhaustivos en `/api/feed` para trazar el origen de errores de acceso.

## [v4.3.3] - 2025-12-21
### Added
- **Mini App - Roles**: Implementado acceso dinámico al catálogo basado en roles (Admin -> Evil, Staff -> Start, Otros -> Denegado).
- **Mini App - UX**: Restaurados los botones de descarga inline en los resultados de Búsqueda y Catálogo.
- **Pruebas**: Suite de pruebas `tests/test_refinement.py` para validar lógica de roles y detalle de libros.
### Changed
- **Mini App - Detalle**: Mejorada la robustez del parseo OPDS para la página de detalle, soportando feeds de una sola entrada y diferentes tipos de metadatos.

## [v4.3.2] - 2025-12-21
### Added
- Nueva página de detalle de libro con información ampliada (Editorial, Idioma, ISBN, Año, Tamaño).
- Acción de backend `book-detail` para obtener metadatos completos de un libro.
### Changed
- Actualizada la búsqueda y el catálogo para navegar a la nueva página de detalle.
- Eliminado botón de descarga inline en búsqueda y catálogo para una interfaz más limpia.
- Optimizada la navegación para compatibilidad con exportación estática de Next.js.

## [v4.3.1] - 2025-12-21
### Añadido
- **Mini App - UX**: Implementado el modo de pantalla completa mediante `requestFullscreen` y desactivación de gestos verticales para evitar el cierre accidental al deslizar hacia abajo.

## [v4.3.0] - 2025-12-21
### Añadido
- **Mini App - Paginación**: Restaurada la funcionalidad de paginación en Búsqueda y Catálogo (basada en v3.13.8).
- **Mini App - Diseño**: Implementado un nuevo componente de paginación con diseño premium (v0 style) que incluye información de página actual y total de páginas.
- **Mini App - UX**: Autoscroll al inicio de la página al cambiar de página para una mejor experiencia de usuario.

## [v4.2.4] - 2025-12-20
### Cambiado
- **Mini App - Limpieza de Catálogo**: Eliminadas las secciones innecesarias ("En el puente", "Listas de lectura", "Deseo leer", "Todas las colecciones") del feed principal del catálogo.
- **Mini App - Diseño**: Ajustado el espaciado entre elementos del catálogo para ser más compacto y coherente con la página de inicio.

## [v4.2.3] - 2025-12-20
### Añadido
- **Mini App - Portadas de Series**: Ahora las series y carpetas muestran la portada del primer libro de su colección si la carpeta no tiene una imagen propia. Aplicado tanto en Búsqueda como en Catálogo.

## [v4.2.2] - 2025-12-20
### Corregido
- **Mini App - Búsqueda de Series**: Ahora los resultados de búsqueda identifican correctamente las series/colecciones. Al pulsar en una serie, se abre la vista de catálogo para ver los libros de esa serie (comportamiento similar a v3.13.8).

## [v4.2.1] - 2025-12-20
### Añadido
- **Mini App - Navegación OPDS Dinámica**: Implementada navegación completa por carpetas y bibliotecas OPDS dentro de la Mini App.
- **Mini App - Botón Retroceder**: Soporte para historial de navegación ("Subir nivel") en el catálogo.
- **Mini App - Bottom Nav**: Agregado acceso directo a "Catálogo" en la barra de navegación inferior.

## [v4.2.0] - 2025-12-20
### Añadido
- **Mini App - Mi Catálogo**: Nueva página para acceder a bibliotecas OPDS (Biblioteca Principal, Novedades, Más Descargados). Agregado botón en el menú principal entre "Buscar Libros" y "Mis Descargas".

## [v4.1.5] - 2025-12-20
### Corregido
- **CRÍTICO - Mini App Routing**: Corregido FastAPI para servir archivos HTML individuales generados por Next.js static export (`search.html`, `donate.html`, etc.) en lugar de siempre servir `index.html`. Esto permite que la navegación funcione correctamente.

## [v4.1.4] - 2025-12-20
### Corregido
- **Mini App - Navegación Completa**: Reemplazados TODOS los Next.js Link con anchor tags estándar en main page, status page, y BottomNav para garantizar navegación funcional en modo export estático dentro de Telegram WebApp.

## [v4.1.3] - 2025-12-20
### Corregido
- **Mini App - Navegación**: Corregida navegación en BottomNav usando enlaces HTML estándar en lugar de Next.js Link para mejor compatibilidad con export estático en Telegram WebApp.

## [v4.1.2] - 2025-12-20
### Corregido
- **CRÍTICO - Database Migration**: Agregada migración automática para añadir columna `nickname` a tablas `users` existentes. Resuelve error "no such column: nickname" que impedía comandos.

## [v4.1.1] - 2025-12-20
### Corregido
- **CRÍTICO - Bot Polling**: Corregida verificación de inicialización de ExtBot que impedía que el bot iniciara el polling y respondiera a comandos. Ahora se verifica que `bot.id` sea accesible antes de marcar el bot como inicializado.

## [v4.1.0] - 2025-12-20

### Añadido
- **Mini App - Navegación Completa (v0.dev)**: Integrada actualización de v0.dev con 4 nuevas páginas:
  - `/donate` - Sistema de donaciones con tiers y detalles
  - `/downloads` - Historial de descargas del usuario
  - `/help` - Centro de ayuda y FAQ
  - `/links` - Enlaces útiles y recursos
- **Componente BottomNav**: Barra de navegación inferior fija con acceso rápido a las 4 secciones principales
- **Safe Area Support**: Soporte para notch en dispositivos iOS

### Corregido
- **Configuración crítica**: Restaurado `output: 'export'` y `distDir: 'dist'` en `next.config.mjs` que fueron eliminados por v0.dev (necesarios para integración con FastAPI)
- **UX**: Eliminada la confirmación de cierre (`enableClosingConfirmation()`) que v0.dev re-agregó

### Mejorado
- **UI Consistente**: Headers unificados en todas las páginas con diseño coherente
- **Navegación**: Experiencia de usuario mejorada con navegación bottom responsive

## [v4.0.3] - 2025-12-20
### Corregido
- **Mini App**: Eliminada la confirmación de cierre que mostraba el mensaje "Changes that you made may not be saved" al cerrar la aplicación, mejorando la experiencia de usuario.

## [v4.0.2] - 2025-12-20
### Corregido
- **Inicialización**: Corregida condición de carrera donde `start_async()` se llamaba incluso si la inicialización del bot fallaba parcialmente, causando `RuntimeError: ExtBot is not properly initialized`.
- **Resiliencia**: Añadido flag `_initialized` para rastrear el estado de inicialización y prevenir llamadas a métodos del bot cuando no está listo.

## [v4.0.1] - 2025-12-20
### Corregido
- **Base de Datos**: Implementada la creación automática de la tabla `users` en el arranque. Corrige el error `no such table: users` en instalaciones limpias.
- **Resiliencia**: Refuerzo de la inicialización de la base de datos antes de registrar el bot.

## [v4.0.0] - 2025-12-20
### Added
- **Nuevo Diseño Premium (V0.dev):** Interfaz completamente rediseñada desde cero utilizando un sistema de diseño moderno basado en tarjetas, colores profundos (`oklch`) y glassmorphism.
- **Header Stick:** Encabezado con efecto de desenfoque y navegación persistente.
- **Perfil Hero:** Nueva sección de presentación del bot más prominente y centrada.

### Changed
- **Renovación Visual Total:** Se abandona la imitación estricta de BotFather en favor de una identidad visual propia, más moderna y pulida.
- **Optimización de Componentes:** Migración a una arquitectura de componentes visuales simplificada y directa en `App.jsx`.

## [v3.13.8] - 2025-12-19

### Añadido
- **Variables de Plantilla**: Sistema de variables expandido y categorizado.
  - Nuevas variables automáticas para el Bot: `[BotNombre]`, `[BotAlias]`.
  - Nuevas variables contextuales para el Chat: `[ChatID]`, `[ChatTitulo]`.
  - Categorización en el comando `/vars`: Usuario, Estado, Sistema y Chat para una mejor gestión.
- **Documentación**: Mejora en las descripciones de todas las variables globales y dinámicas.

### Cambiado
- **Versiones**: Plugin `custom_messages` actualizado a v1.4.2.

## [v3.13.7] - 2025-12-19

### Añadido
- **Mensajes**: Unificada la lógica de menciones. Ahora el placeholder `[Nombre]` es clickeable por defecto en todas las plantillas (Status, Ayuda, Bienvenida, etc.) usando `mention_html()`.

### Cambiado
- **Refactorización**: Eliminadas conversiones manuales a HTML en los controladores de comandos y callbacks, centralizando la lógica en el plugin de mensajes.
- **Versiones**: Plugin `custom_messages` actualizado a v1.4.1.

## [v3.13.6] - 2025-12-19

### Corregido
- **Pruebas**: Corregido `TypeError` en `tests/test_publish_temp.py` al mockear incorrectamente el plugin `custom_messages`.
- **Pruebas**: Corregida definición de `context` en pruebas unitarias para evitar `NameError`.

## [v3.13.5] - 2025-12-19

### Añadido
- **Menú de Comandos**: Soporte para reordenar comandos dinámicamente.
  - Nuevo comando `/move_menu_cmd <comando> <posición>` para admins.
  - Documentación detallada de comandos de gestión en el registro interno (`/help` y `/menu`).
  - Refuerzo de validaciones para posiciones de comandos.

## [v3.13.4] - 2025-12-18

### Añadido
- **Menú de Comandos**: Gestión dinámica del menú de comandos (Admin).
  - Comandos para añadir/quitar comandos del menú público sin reiniciar.
  - Persistencia de configuración en base de datos.
  - Refuerzo de validación y limpieza del registro de ayuda.

## [v3.13.3] - 2025-12-18

### Corregido
- **Menú de Comandos**: Registro exhaustivo de scopes para menú de comandos en grupos y tópicos globales (`Default`, `AllGroupChats`, `AllChatAdministrators`).

## [v3.13.2] - 2025-12-18

### Corregido
- **Menú de Comandos**: Eliminada la elevación automática de comandos para administradores de grupo. Ahora solo ven los comandos por defecto, respetando estrictamente su nivel de usuario configurado.

## [v3.13.1] - 2025-12-18

### Corregido
- **Menú de Comandos**: Corregida la visibilidad del menú `/`. Ahora es visible para todos los usuarios en chats privados y grupos mediante el uso de ámbitos (scopes) explícitos (`AllPrivateChats`, `AllGroupChats`, `AllChatAdministrators`).

## [v3.13.0] - 2025-12-18

### Añadido
- **Menú de Comandos**: Implementada la sincronización automática de comandos en el menú nativo de Telegram (`/`).
- **Ayuda**: Los administradores ahora pueden ver todos los comandos de gestión, incluso si no están definidos en el `.env`, gracias a la integración con el sistema de roles en base de datos.
- **Ayuda**: Categoría de "Mensajes" (🧩) ahora visible por defecto si el plugin está activo.

### Corregido
- **Ayuda**: Eliminados comandos duplicados en el registro.

## [v3.12.3] - 2025-12-18

### Corregido
- **Linter**: Corrección de errores de espacios en blanco (W293) en `callback_handlers.py` y `telegram_service.py`.

## [v3.12.2] - 2025-12-18

### Corregido
- **Donaciones**: Se ha añadido el botón **"❌ Cancelar Registro"** y el sistema de **timeout** al flujo de reporte cuando se inicia desde un grupo (mensaje proactivo en privado).

## [v3.12.1] - 2025-12-18

### Corregido
- **Donaciones**: Se ha corregido el error donde la variable `[Tiempo]` no se reemplazaba correctamente al iniciar el reporte de donación desde un grupo.
- **Plantillas**: Se ha restaurado la plantilla `donation_proof_received` que se eliminó accidentalmente en la versión anterior.

## [v3.12.0] - 2025-12-18

### Añadido
- **Mejoras en Donaciones**:
    - Se ha añadido un botón de **"❌ Cancelar Registro"** al solicitar el comprobante de donación.
    - Se ha implementado un sistema de **tiempo de espera (timeout)** de 10 minutos. Si no se recibe el comprobante en ese tiempo, el registro se cancela automáticamente.
    - Nuevas plantillas de mensajes para cancelación manual y por tiempo de espera.

### Cambiado
- **Flujo de Recepción**: El bot ahora detiene correctamente el cronómetro de espera cuando se recibe un comprobante válido.

## [v3.11.0] - 2025-12-18

### Añadido
- **Publicación en Grupos**: Todos los miembros del **Staff** (Admins y Publicadores) ahora pueden publicar libros directamente en grupos, temas (topics) y canales.
- **Auto-borrado**: Los mensajes publicados por el Staff en grupos se eliminan automáticamente tras el tiempo configurado (`auto_delete_time`).

### Cambiado
- **Seguridad de Publicación**: Los usuarios no Staff (Free, VIP, Premium, etc.) seguirán recibiendo los libros exclusivamente en su chat privado para mantener el orden en los grupos.
- **Lógica Interna**: Migración de la verificación de privilegios al sistema de roles asíncrono en `telegram_service.py`.

## [v3.10.1] - 2025-12-17

### Arreglado
- **Linting**: Corregidos errores W293 (whitespace) y E303 (blank lines)
- **Documentación**: Añadidos `/menu` y `/view_msge` al sistema de ayuda

### Cambiado
- **Versiones de Plugins**: user_manager (1.2.0), suggestions (2.0.0), custom_messages (1.4.0), help (2.2.0)

## [v3.10.0] - 2025-12-17

### Añadido
- **Flujo de Donaciones Mejorado**: Eliminado parámetro de deep link, el bot envía instrucciones proactivamente al chat privado
- **Notificaciones de Donaciones**: Comandos `/approve_donation` y `/reject_donation` para gestión de verificaciones
- **Sistema de Sugerencias Interactivo**: Botones de Aceptar/Rechazar/Respuesta Personalizada en mensajes de sugerencias

### Cambiado
- **Donaciones**: URL del botón ahora es simple (`https://t.me/bot`) sin mostrar `/start` en el chat
- **Mensajes**: 5 nuevos templates añadidos al sistema de plantillas

### Arreglado
- **Respuestas Personalizadas**: Handler movido a `recibir_texto()` para que funcionen correctamente
- **Notificación de Actualización**: El bot ahora envía correctamente el mensaje después de `/update_system`

## [v3.9.5] - 2025-12-17

### Arreglado
- **Notificación de Actualización**: El bot ahora envía correctamente el mensaje de "Actualización Completada" después de `/update_system`
- **Inicialización**: Métodos `initialize_schedulers()` y `check_update_state()` ahora se ejecutan en el método `start()` tradicional
- **Tests**: Corregido `test_start_publisher_does_not_show_collections_immediately` usando `AsyncMock` para `reply_text`

## [v3.9.4] - 2025-12-17

### Añadido
- **Sistema de Templates Completo:**
  - Añadidos 12 nuevos templates editables vía `/set_msge`:
    - `donation_link_unauthorized` - Enlace de donación no autorizado
    - `webapp_auth_invalid` - Autenticación webapp inválida
    - `download_preparing` - Preparando descarga
    - `donation_proof_invalid_format` - Formato de comprobante inválido
    - `destination_selected` - Destino seleccionado
    - `no_pending_publication` - No hay publicación pendiente
    - `invalid_option` - Opción inválida
    - `no_more_pages` - No hay más páginas
    - `fb_preview_discarded` - Vista previa FB descartada
    - `button_unauthorized` - Botón/mensaje no autorizado
    - `donation_request_registered` - Solicitud de donación registrada
    - `request_processing_error` - Error procesando solicitud
  - Nuevo comando `/view_msge <slug>` para previsualizar templates con HTML renderizado
  - Todos los mensajes ahora usan fallback a defaults si no hay personalización

### Cambiado
- **Variable `[Nombre]`**: Ahora usa `mention_html()` en todos los templates para nombres clicables
- **Mensaje de redirección de donación**: Migrado a template `donation_redirect_prompt`

### Arreglado
- **Linting**: Corregidos errores de formato (W293, E261, E303, W391) en handlers
- **Restricción de comprobantes**: Solo se aceptan en chat privado

## [v3.9.3] - 2025-12-17

### Added
- **Mejora Flujo Donaciones:**
    - Botón "Ya realicé la donación" ahora redirige directamente al chat privado con instrucciones.
    - Soporte para Topics en grupos (el bot responde en el hilo correcto).
    - Auto-borrado de mensajes de donación tras 2 minutos o al interactuar.
    - Restricción de uso de botones: solo el usuario que solicitó el comando puede interactuar.

### Fixed
- **Deep Links:** Corregido error `Url_invalid` usando deep links con parámetros.
- **Linting:** Limpieza general de código (indentación, espacios).
## [3.9.2] - 2025-12-17

### Arreglado
- **Persistencia de Status**: Solucionado el problema donde los comandos `/set_rol` y `/set_apodo` no guardaban cambios si el usuario (ej. Admin) no estaba en la base de datos. Ahora se crea el usuario automáticamente.
- **Dependencias**: Resuelta dependencia circular en `download_limiter.py` que causaba errores en tiempo de ejecución.
- **Estilo**: Corrección de espacios en blanco en `handlers/command_handlers.py` (W293).

## [3.9.1] - 2025-12-16

### Añadido
- **Topics**: Soporte para Telegram Topics en el comando `/saludo` (argumento opcional `thread_id`).
- **Comandos**: Actualizada ayuda de `/saludo` indicando cómo enviar mensajes a topics.

### Actualizado
- **Plugins**: Custom Messages v1.3.0, UserManager v1.1.0, GroupManager v1.0.1.
- **Config**: `GroupManagerPlugin` habilitado por defecto (`ENABLE_GROUP_MANAGER=True`).
- **UserManager**: Ahora soporta asignar roles, niveles y apodos respondiendo a mensajes (`/add_user`, `/set_rol`, `/set_apodo`). Renombrado `/set_staff_status` a `/set_rol`.
- **GroupManager**: Corrección en detección de nuevos usuarios (soporte para mensajes de servicio). Ahora la bienvenida responde al mensaje de ingreso.

## [3.9.1] - 2025-12-16

### Añadido
- **Reset Message**: Nuevo comando `/reset_msge` para revertir personalizaciones de plantillas y volver al valor por defecto.
- **Help Update**: Documentación automática del comando de reset en el menú de ayuda.

### Corregido
- **Templates**: Refactorización del comando `/templates` para usar un menú interactivo y evitar mensajes excesivamente largos.
- **Linting**: Corrección de errores menores de estilo (W293) en handlers.
- **Test**: Corrección de tests unitarios para adaptarse a la nueva lógica de roles (Publisher).

## [3.9.0] - 2025-12-16

### Añadido
- **Plantillas de Ayuda**: Todos los textos de ayuda son personalizables vía `help_cmd_*`.
- **Publisher**: Lógica estricta para rol "Publisher" (Nivel Staff + Rol Custom "Publicador").
- **Gestión de Usuarios**: Nueva categoría en Ayuda para administración de usuarios.
- **Apodos**: Nuevo comando `/set_apodo <id> <apodo>` y variable `[Apodo]` en plantillas.
- **Base de Datos**: Migración para soportar nicknames en tabla `users`.

### Cambiado
- **Ayuda**: Reestucturación del sistema de ayuda:
    - `/help`: Lista simple de texto (filtrada por permisos).
    - `/menu`: Menú interactivo con botones.
- **Variables de Plantilla**: Redefinición estricta de variables:
    - `[Nivel]`: Mapeo directo de rol de sistema (Free -> "Lector", White -> "Patrocinador", etc.).
    - `[Rol]`: Muestra **exclusivamente** el estado personalizado (Custom Status).
- **Visibilidad**: Comandos `/stats` y `/evil` documentados en ayuda para administradores.

### Corregido
- **Status**: Error `NameError` al acceder a `expires_at` en el comando `/status`.

## [3.8.5] - 2025-12-16

### Añadido
- **Custom Messages**: Se añadió la variable `[Rol]` para plantillas, que muestra el rol interno del sistema (Admin, Vip, Staff, Free) de forma capitalizada, diferenciándola de `[Nivel]` que muestra la etiqueta personalizada.

## [3.8.4] - 2025-12-16

### Corregido
- **Mini App**: Se corrigió un error donde el contador de descargas restantes aparecía como objeto corrutina en lugar del número (`await` faltante en `enviar_libro_directo`).

## [3.8.3] - 2025-12-16

### Corregido
- **Bug Crítico**: Eliminación de `import re` anidado en `handlers/callback_handlers.py` que oscurecía la importación global y causaba `UnboundLocalError` en tiempo de ejecución.

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
