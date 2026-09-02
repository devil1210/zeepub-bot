# 📊 Resumen Ejecutivo del Rediseño de la WebApp — Consola Editorial v2

## 🎯 Objetivos del Rediseño
1. **Transformación Funcional**: Convertir la WebApp en una **Consola Editorial Profesional** para catalogación, auditoría de metadatos, gestión de series, volúmenes y programación de publicaciones en canales sociales (Telegram y Facebook).
2. **Cero Pérdida de Funcionalidades**: Preservar íntegramente la interfaz clásica (`v1`) y todas sus capacidades (lector EPUB, visor de detalles, DataGrid, hub de IA, auditorías, etc.).
3. **Aislamiento en Rama y Rutas Dedicadas**: Operar en la rama `feature/editorial-webapp-redesign` y bajo el prefijo `/app-v2/*` con conmutador bidireccional entre versiones.
4. **Diseño Premium y Modularidad**: Respetar el límite de < 500 líneas por archivo y los tokens Glassmorphism.

---

## 🛠️ Resumen de Cambios Principales

### 1. Nuevo Shell y Arquitectura de Navegación v2 (`/app-v2`)
- Creado `EditorialLayout.tsx` con barra lateral oscura con efecto Glassmorphism, buscador global interactivo (`Cmd+K`), accesos rápidos y perfil de editor.
- Creado `GlobalSearchModal.tsx` para búsqueda federada instantánea entre series, volúmenes y archivos EPUB.

### 2. Tablero de Control Editorial (`/app-v2`)
- Métricas dinámicas centradas en **Trabajo Editorial Pendiente**:
  - EPUBs sin metadatos en español o sin volumen.
  - Propuestas de IA pendientes de aprobación.
  - Publicaciones agendadas en cola.
  - Conteo global de series y accesos a pipelines de ingesta.

### 3. Biblioteca de EPUBs con Filtros de Integridad (`/app-v2/library`)
- Tabla completa de archivos con badges editoriales (*Listo*, *Sin Serie*, *Sin Volumen*, *Sin Español*).
- Panel lateral deslizante de edición rápida (`EditorialQuickEditDrawer.tsx`) con auto-completado asistido por IA.

### 4. Gestión Dedicada de Series y Volúmenes (`/app-v2/series` & `/app-v2/volumes`)
- Visualización de nombres canónicos en inglés, romaji y español, con conteo de tomos y enlaces directos a volúmenes asociados.
- Matriz de volúmenes por serie con registro de descargas y vinculación de archivos.

### 5. Calendario y Agenda de Publicaciones (`/app-v2/calendar` & `/app-v2/posts`)
- Vista de cronograma de publicaciones programadas para Telegram y Facebook con estados (*Programado*, *Publicado*, *Fallido*) y acciones de reintento/cancelación.
- Historial de publicaciones con enlaces directos a canales y fechas.

### 6. Biblioteca y Editor de Plantillas (`/app-v2/templates`)
- Editor de copys con paleta de etiquetas dinámicas (`{serie}`, `{volumen}`, `{titulo}`, `{autor}`, `{sinopsis}`, `{hashtags}`, `{link}`, `{cta}`).
- Previsualización simulada en tiempo real y función de copiado rápido al portapapeles para publicaciones en Facebook.

### 7. Administración de Usuarios y Herramientas Legacy (`/app-v2/users` & `/app-v2/legacy`)
- Panel de asignación de niveles y roles de usuario.
- Catálogo de herramientas técnicas previas (DataGrid Excel, Gestor de Duplicados, Auditoría de Géneros, AI Hub) para asegurar continuidad total.

---

## 📋 Comparativa de Funcionalidades

### 🟢 Funciones Mantenidas Tal Cual
- Lector Web de EPUBs (`/reader`).
- Ficha de detalles y visor interactivo de libro (`/book/:bookId`).
- Solicitud de libros por usuarios (`/requests`).
- Historial de descargas (`/downloads`).
- DataGrid masivo tipo Excel (`/admin/series-manager`).
- Sistema de IA con Gemini (`/ai`).
- Visor de logs y observatorio del sistema.

### ⚡ Funciones Significativamente Mejoradas
- **Dashboard**: De estadísticas estáticas a un panel de tareas accionables con acceso directo a resolver anomalías.
- **Edición de Metadatos**: Ahora se puede editar cualquier EPUB o serie mediante un drawer lateral sin perder la posición ni el filtro en la lista.
- **Programación de Publicaciones**: Módulo unificado con selección de canal, plantilla y fecha/hora con vista previa.
- **Copys de Redes Sociales**: Constructor dinámico de plantillas con vista previa y copia rápida para Facebook.
- **Búsqueda Global**: Atajo `Cmd+K` para saltar a cualquier serie o volumen desde cualquier vista.

---

## 🔮 Pendientes y Próximos Pasos (Opcionales para v2.1)
- [ ] Automatización de API Graph de Facebook para publicación directa desatendida (actualmente genera el copy completo con preview y exportación).
- [ ] Soporte para arrastrar y soltar (Drag & Drop) en la reordenación de volúmenes dentro de una serie.
