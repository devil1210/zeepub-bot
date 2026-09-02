# 📋 Notas de Migración y Paridad Funcional — Consola Editorial v2

Este documento detalla la correspondencia exacta entre la interfaz clásica (v1) y la nueva **Consola Editorial v2** (`/app-v2`).

## 🔄 Tabla de Paridad y Módulos Integrados

| Módulo / Funcionalidad Clásica | Nueva Ubicación en Consola v2 | Mejoras Incorporadas |
|---|---|---|
| **Biblioteca / Catálogo de EPUBs** | `/app-v2/library` | Tabla con badges de estado, portadas con resolución resiliente, filtros de consistencia y drawer lateral de edición rápida. |
| **Explorador y Detalle de Series** | `/app-v2/series` | Tarjetas con portadas automáticas, conteo dinámico de volúmenes, títulos en inglés/romaji/español. |
| **Volúmenes por Serie** | `/app-v2/volumes` | Matriz de volúmenes por serie con botón directo para programar publicaciones. |
| **Editor DataGrid (Excel)** | `/app-v2/datagrid` | Edición masiva estilo hoja de cálculo, recálculo de slugs y guardado en lote. |
| **Agenda y Cola de Publicación** | `/app-v2/calendar` | Cronograma de posts para Telegram/Facebook con botones para **Editar/Reprogramar**, Reintentar y Cancelar. |
| **Historial de Publicaciones** | `/app-v2/posts` | Registro cronológico de lanzamientos con estados enriquecidos (`sent`, `published`). |
| **Editor de Plantillas de Copys** | `/app-v2/templates` | Constructor visual con paleta de tags dinámicos, simulador en tiempo real y copiado para Facebook. |
| **Hub de IA (Gemini)** | `/app-v2/ai` | Normalización inteligente con modelos Gemini, propuestas automáticas y aprobación/rechazo. |
| **Fansubs y Canales** | `/app-v2/channels` | Configuración de canales de destino, grupos de traducción y enlaces de contacto. |
| **Gestor de Duplicados & Merges** | `/app-v2/duplicates` | Detección de duplicados por hash SHA-256, fusión asistida por IA y purga de archivos. |
| **Auditoría de Géneros & Demografías** | `/app-v2/genres` | Auditoría de taxonomía, corrección de inconsistencias y asignación masiva de etiquetas. |
| **Observatorio del Sistema** | `/app-v2/observatory` | Monitoreo en vivo de tareas en segundo plano, métricas de rendimiento y logs del servidor. |
| **Gestión de Usuarios y Roles** | `/app-v2/users` | Panel de usuarios, asignación de tiers de descarga y control de accesos. |
| **Ajustes y Configuración** | `/app-v2/settings` | Preferencias de idioma de títulos, monitor de logs y reinicio de servicios. |
