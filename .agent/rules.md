# Reglas Universales del Proyecto Zeepub-bot

Como asistente de este proyecto, debes seguir estas reglas en cada interacción:

1.  **Idioma**: Responde SIEMPRE en **español**, a menos que se te pida explícitamente lo contrario.
2.  **Estética UI**: Mantén siempre el estilo "Premium/Glassmorphism" definido en las guías anteriores para cualquier cambio en el frontend.
3.  **Hacia adelante**: Siempre que termines una tarea exitosa de código, ofrece (o ejecuta si hay workflow) la persistencia de los cambios.
4.  **Calidad y Stack**: Sigue estrictamente los patrones de `python-patterns` y `backend-dev-guidelines`. Asume SIEMPRE que estamos operando sobre un stack de **PostgreSQL** para persistencia local y lógica de datos.
5.  **Resumen de Operación**: Al finalizar cada tarea significativa, genera un resumen estructurado con: Lo que hice, Lo que está pendiente, y Mejoras/Próximos pasos.
6.  **Validación Técnica Pre-Vuelo**: ANTES de reportar una tarea como completada o hacer push, debes:
    *   Para archivos Python: Ejecutar un check de sintaxis (`python -m py_compile [archivo]`).
    *   **Linter & Formatter**: Asegurar que el código pase `ruff check` y esté formateado (preferiblemente con `ruff format` o `black`).
    *   Para archivos TS/React: Verificar que no haya errores de importación evidentes.
7.  **Uso de Skills**: Prioriza las skills de `.agent/skills.md` y expande con globales si es necesario, siguiendo el nuevo formato de "Lecciones Aprendidas".
8.  **Normalización de Datos**: Al procesar libros o autores, utiliza siempre las funciones de `utils.helpers` (`normalize_author_name`, `process_book_identity_comprehensive`) para garantizar la integridad de los hashes. **Integra la IA (`services/ai_service`) como paso previo de normalización** siempre que sea posible, priorizando sus sugerencias de `series_spanish` y `volume` sobre las Regex crudas.
9.  **PostgreSQL First**: Toda consulta SQL o definición de modelo debe optimizarse para PostgreSQL (uso de JSONB, ILIKE, funciones de agregación específicas, etc.).
10. **Logs del VPS**: Asume SIEMPRE que los logs recibidos provienen del **VPS de pruebas** a menos que se indique explícitamente lo contrario. Actúa de forma proactiva para corregir errores de entorno (como falta de columnas en DB o permisos de archivo) mediante scripts de migración o correcciones en el código de inicialización.
11. **Gestión de Skills**: Mantener el proyecto sincronizado con el repositorio global (https://github.com/sickn33/antigravity-awesome-skills/). **Todas las definiciones de capacidades activas y sus reglas de comportamiento específicas deben residir ÚNICAMENTE en `.agent/skills.md`** para garantizar una única fuente de verdad y evitar redundancias.
12. **Barra de Navegación Única (Floating Nav)**: Existe una ÚNICA arquitectura de navegación flotante para toda la aplicación. Se gestiona centralizadamente a través de `NavigationContext.tsx` y se implementa en `UniversalFloatingNav.tsx` (estilo glassmorphism, redondeado y flotante). Cada página (Search, SeriesDetail, Admin, Dashboard) debe configurar su `contextType` para adaptar el contenido de la barra. Se prohíbe terminantemente crear nuevas barras de navegación standalone; todas las navegaciones contextuales deben integrarse en este componente único.
13. **Unificación de Series**: Ante problemas de series duplicadas, asume que la causa principal es la inconsistencia en el `book_type` (p. ej. "Novela ligera" vs "Novela Ligera") o hashes stale. Utiliza siempre el escaneo completo con sincronización de conteos para forzar la limpieza de series vacías. Siempre usa `utils.helpers` para normalización.
14. **Auditoría de Producción (`production-code-audit`)**: Antes de cualquier despliegue mayor, PR crítico o cambio estructural en el backend/frontend, ejecutar una auditoría completa guiada por el skill para asegurar el cumplimiento de estándares corporativos de seguridad y performance.
