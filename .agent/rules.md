# Reglas Universales del Proyecto Zeepub-bot

Como asistente de este proyecto, debes seguir estas reglas en cada interacción:

1.  **Idioma**: Responde SIEMPRE en **español**, a menos que se te pida explícitamente lo contrario.
2.  **Estética UI**: Mantén siempre el estilo "Premium/Glassmorphism" definido en las guías anteriores para cualquier cambio en el frontend.
3.  **Hacia adelante**: Siempre que termines una tarea exitosa de código, ofrece (o ejecuta si hay workflow) la persistencia de los cambios.
4.  **Calidad y Stack**: Sigue estrictamente los patrones de `python-patterns` y `backend-dev-guidelines`. Asume SIEMPRE que estamos operando sobre un stack de **PostgreSQL** para persistencia local y lógica de datos.
5.  **Resumen de Operación**: Al finalizar cada tarea significativa, genera un resumen estructurado con: Lo que hice, Lo que está pendiente, y Mejoras/Próximos pasos.
6.  **Validación Técnica Pre-Vuelo**: ANTES de reportar una tarea como completada o hacer push, debes:
    *   Para archivos Python: Ejecutar un check de sintaxis (`python -m py_compile [archivo]`).
    *   **Linter & Formatter**: Asegurar que el código pase `flake8` y esté formateado con `black` (o equivalente).
    *   Para archivos TS/React: Verificar que no haya errores de importación evidentes.
7.  **Uso de Skills**: Prioriza las skills de `.agent/skills.md` y expande con globales si es necesario, siguiendo el nuevo formato de "Lecciones Aprendidas".
8.  **Normalización de Datos**: Al procesar libros o autores, utiliza siempre las funciones de `utils.helpers` (`normalize_author_name`, `process_book_identity_comprehensive`) para garantizar la integridad de los hashes.
9.  **PostgreSQL First**: Toda consulta SQL o definición de modelo debe optimizarse para PostgreSQL (uso de JSONB, ILIKE, funciones de agregación específicas, etc.).
10. **Logs del VPS**: Asume SIEMPRE que los logs recibidos provienen del **VPS de pruebas** a menos que se indique explícitamente lo contrario. Actúa de forma proactiva para corregir errores de entorno (como falta de columnas en DB o permisos de archivo) mediante scripts de migración o correcciones en el código de inicialización.
11. **Actualización de Skills**: Verificar periódicamente si existen actualizaciones en el repositorio de skills globales y reflejar las mejoras pertinentes en `.agent/skills.md`.
