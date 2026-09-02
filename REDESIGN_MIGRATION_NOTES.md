# 📑 Notas de Migración y Mapeo Funcional — Rediseño WebApp v2 (Consola Editorial)

Este documento registra la matriz de paridad funcional entre la interfaz actual (`v1` / rutas raíz) y la nueva **Consola Editorial de Biblioteca de EPUBs** (`v2` bajo `/app-v2`). Ninguna funcionalidad previa ha sido eliminada.

---

## 🗺️ Matriz de Mapeo y Paridad Funcional

| Función Actual | Ruta / Vista Actual | Nueva Ruta / Vista (v2) | Estado | Descripción y Mejoras en v2 |
| :--- | :--- | :--- | :---: | :--- |
| **Dashboard de Lectura / Estadísticas** | `/` (Dashboard) | `/app-v2` (Dashboard Editorial) | ⚡ **Mejorada** | Transforma las métricas pasivas en un tablero de **Trabajo Editorial Pendiente** (EPUBs sin metadatos, series incompletas, publicaciones en cola, accesos rápidos). |
| **Catálogo General y Búsqueda de Series** | `/search` | `/app-v2/series` | ⚡ **Mejorada** | Vista dedicada a series con vista en cuadrícula/tabla, filtros por estado editorial, autor, géneros, conteo de volúmenes y panel lateral de edición rápida. |
| **Biblioteca de EPUBs y Archivos** | `/library` | `/app-v2/library` | ⚡ **Mejorada** | Listado integral de archivos EPUB físicos indexados con badges de estado (Sin revisar, Sin serie, Sin volumen, Sin portada, Listo, Publicado), filtros específicos y editor drawer. |
| **Gestión Editorial de Volúmenes** | `/admin/series-manager` (Grid) | `/app-v2/volumes` | ⚡ **Mejorada** | Vista dedicada de volúmenes por serie con número, subtítulo, EPUB asociado, estado editorial, fechas, plantilla sugerida y acciones de publicación directa. |
| **Programación / Calendario de Publicaciones** | `/admin` (Pestaña Publicador) | `/app-v2/calendar` & `/app-v2/posts` | ⚡ **Mejorada** | Agenda interactiva tipo calendario para programar posts en Telegram/Facebook, estados (Borrador, Programado, Publicado, Fallido), reprogramación y previsualización de mensajes. |
| **Biblioteca y Editor de Plantillas** | `/admin/templates/new` & `/:id` | `/app-v2/templates` | ⚡ **Mejorada** | Biblioteca de plantillas con variables dinámicas (`{serie}`, `{volumen}`, `{titulo}`, `{autor}`, `{sinopsis}`, `{hashtags}`, `{link}`, `{cta}`), editor con preview en vivo y copy exportable para Facebook y Telegram. |
| **Gestión de Series y Volúmenes (DataGrid)** | `/admin/series-manager` | `/app-v2/series` & `/app-v2/legacy/datagrid` | 🟢 **Igual / Integrada** | Se mantiene el DataGrid tipo Excel como herramienta de edición masiva avanzada accesible desde herramientas editoriales. |
| **Detalle de Serie y Edición Profunda** | `/admin/series/:id` | `/app-v2/series/:id` | ⚡ **Mejorada** | Edición de metadatos canónicos, aliases, fusión de series duplicadas, re-asignación de volúmenes y recálculo de slugs. |
| **Detalle de Volumen / Libro** | `/book/:bookId` / `/read/...` | `/book/:bookId` & Drawer v2 | 🟢 **Igual** | Mantiene la ficha interactiva original para lectura, visor y descarga, complementada con el drawer de edición editorial. |
| **Subida de EPUBs (Individual y Masiva)** | `/upload` | `/app-v2/upload` | ⚡ **Mejorada** | Flujo de ingesta con análisis preliminar por IA, asignación automática de serie y estado editorial "Por revisar". |
| **Hub de Inteligencia Artificial** | `/ai` | `/app-v2/ai` | 🟢 **Igual** | Escaneo asistido con Gemini (2.5-flash / 3-flash-preview), propuestas de normalización, merge inteligente y re-etiquetado. |
| **Gestión de Usuarios y Permisos** | `/admin` (Pestaña Usuarios) | `/app-v2/users` | ⚡ **Mejorada** | Panel dedicado de usuarios, roles (`admin`, `staff`, `user`, `banned`), asignación de niveles y auditoría de descargas. |
| **Auditoría de Géneros y Demografías** | `/admin` (Pestaña Géneros) | `/app-v2/legacy/genres` | 🟢 **Igual** | Validador y resolución de discrepancias en géneros y demografías. |
| **Gestor de Duplicados** | `/admin` (Pestaña Duplicados) | `/app-v2/legacy/duplicates` | 🟢 **Igual** | Detección de duplicados MD5 / SHA-256 y herramientas de purga. |
| **Observatorio del Sistema y Logs** | `/admin` (Pestaña Logs/Observatorio) | `/app-v2/settings` (Pestaña Logs) | 🟢 **Igual** | Monitoreo de ejecuciones en background, salud de contenedores y visor de logs con exportación a Telegram. |
| **Ajustes de Interfaz y Glassmorphism** | `/settings` | `/app-v2/settings` | ⚡ **Mejorada** | Personalización de temas, escala tipográfica, calidad de portadas, y selección de idioma de títulos (`Inglés`, `Romaji`, `Español`). |
| **Lector Web de EPUBs** | `/reader` | `/reader` | 🟢 **Igual** | Lector in-browser preservado sin alteraciones. |
| **Solicitud de Libros por Usuarios** | `/requests` | `/requests` & Drawer v2 | 🟢 **Igual** | Buzón de peticiones de la comunidad. |
| **Historial de Descargas de Usuario** | `/downloads` | `/downloads` | 🟢 **Igual** | Registro de descargas personales del lector. |

---

## 🔒 Garantía de Convivencia y Acceso Paralelo

1. **Rutas v1 (Vigentes)**: El usuario puede seguir accediendo a todas las rutas originales (`/`, `/search`, `/library`, `/admin`, etc.) sin sufrir ningún cambio visual forzado ni pérdida de datos.
2. **Rutas v2 (Consola Editorial)**: La nueva interfaz opera bajo el prefijo `/app-v2/*` con su propio layout de barra lateral profesional, navegación unificada y modales/drawers optimizados.
3. **Selector Rápido de Versión**: Ambas interfaces incluyen un conmutador bidireccional:
   - En v1: Banner superior *"✨ Probar Nueva Consola Editorial (v2 Beta)"* ➔ `/app-v2`.
   - En v2: Botón de cabecera *"🔙 Volver a Vista Clásica (v1)"* ➔ `/`.
