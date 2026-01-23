# Reglas Universales del Proyecto Zeepub-bot

Como asistente de este proyecto, debes seguir estas reglas en cada interacción:

1.  **Idioma**: Responde SIEMPRE en **español**, a menos que se te pida explícitamente lo contrario.
2.  **Estética UI**: Mantén siempre el estilo "Premium/Glassmorphism" definido en las guías anteriores para cualquier cambio en el frontend.
3.  **Hacia adelante**: Siempre que termines una tarea exitosa de código, ofrece (o ejecuta si hay workflow) la persistencia de los cambios.
4.  **Calidad**: Sigue estrictamente los patrones de `python-patterns` y `backend-dev-guidelines`.
5.  **Resumen de Operación**: Al finalizar cada tarea significativa, genera un resumen estructurado con: Lo que hice, Lo que está pendiente, y Mejoras/Próximos pasos.
6.  **Validación Técnica Pre-Vuelo**: ANTES de reportar una tarea como completada o hacer push, debes:
    *   Para archivos Python: Ejecutar un check de sintaxis (`python -m py_compile [archivo]`). Por ejemplo, para evitar errores de `NameError` por imports faltantes.
    *   Para archivos TS/React: Verificar que no haya errores de importación evidentes.
7.  **Uso de Skills**: Prioriza las skills de `.agent/skills.md` y expande con globales si es necesario, siguiendo el nuevo formato de "Lecciones Aprendidas".
