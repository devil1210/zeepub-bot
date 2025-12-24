# Changelog

Todas las versiones notables de este proyecto serán documentadas en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

## [v4.6.0] - 2024-12-24

### Changed
- **Rollback del Backend a v4.4.1**: Revertidos todos los archivos del backend (api, core, services, repositories, utils) a su estado en v4.4.1 para restaurar la funcionalidad estable del Panel de Administración
- **Mantenida la UI de v0**: Se conserva el diseño visual moderno de v0 en el frontend (zeepub-web)
- **Estrategia Híbrida**: Combina la estabilidad del backend v4.4.1 con la estética mejorada de v0

### Fixed
- Restaurado el acceso completo al Panel de Control de Niveles de Usuario
- Corregidos todos los problemas de autenticación y permisos de administrador
- Eliminados bugs introducidos en las versiones v4.5.x

## [v4.5.4] - 2024-12-24

### Fixed
- Corregido bug crítico en `get_effective_user` donde `elif` impedía verificar `config.ADMIN_USERS` si el usuario existía en la base de datos
- Cambiado `elif` por `if` para que los administradores del config siempre tengan prioridad

## [v4.5.3] - 2024-12-24

### Added
- Logs de depuración detallados en `verify_admin` y `get_levels` para diagnosticar problemas de acceso

### Fixed
- Correcciones de linting (flake8): eliminados espacios en blanco, líneas vacías excesivas, y variable indefinida

## [v4.5.2] - 2024-12-24

### Added
- Restaurado el botón "Catálogo" en la barra de navegación inferior

### Fixed
- Silenciamiento profundo de logs de `httpcore`, `httpx`, `telegram` y `apscheduler` incluyendo sub-módulos
- Logs de depuración para administradores en el backend

## [v4.5.1] - 2024-12-24

### Fixed
- Restauradas las cabeceras de seguridad `x-telegram-init-data` en el Panel de Administración
- Deshabilitada la confirmación de cierre de la Mini App para mejor UX
- Silenciados logs ruidosos de bibliotecas de terceros

## [v4.5.0] - 2024-12-21

### Added
- **Rediseño Total de la Interfaz (v0)**: Nueva experiencia de usuario moderna con navegación unificada
- Barra de navegación inferior con acceso rápido a todas las secciones
- Diseño visual mejorado con mejor contraste y legibilidad
- Nuevas páginas: Home, Catalog, Search, Downloads, Links, Status, Settings, Help, Donate

### Changed
- Migración completa del frontend a la nueva arquitectura v0
- Rutas dinámicas convertidas a rutas basadas en consultas para compatibilidad con exportación estática
- Estandarización de rutas de admin: `/access-control` → `/admin/levels`

## [v4.4.1] - 2024-12-21

### Fixed
- Mejoras de autenticación en el panel de administración
- Limpieza de logs del sistema

## [v4.4.0] - 2024-12-21

### Fixed
- Corrección crítica de acceso para administradores
- Sincronización de roles entre sistema legacy y sistema de niveles

## [v4.3.9] - 2024-12-21

### Changed
- Rediseño de control de accesos e integración en Ajustes

## [v4.3.8] - 2024-12-21

### Added
- Interfaz de gestión de accesos para administradores

## [v4.3.7] - 2024-12-21

### Added
- Página de acceso denegado para usuarios sin permisos

## [v4.3.6] - 2024-12-21

### Added
- Sistema de Control de Acceso por Niveles (Tiered Access Control)
- Niveles predefinidos: Admin, Staff, VIP, Patrocinador, Whitelist, Lector
- API de seguridad con validación de Telegram
- Integración de `get_effective_user` para resolución de roles
