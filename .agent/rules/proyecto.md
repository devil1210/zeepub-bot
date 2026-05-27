---
trigger: always_on
version: 3.6.2
edition: Enterprise
---

# 🌌 Manifesto de Operación ZeePub-bot v3.6.0 (Enterprise)

Este archivo es la **Única Fuente de Verdad** para el comportamiento del asistente. Se carga automáticamente en cada sesión.

## 📌 Reglas Universales de Comportamiento

1.  **Idioma**: Responde SIEMPRE en **español**, a menos que se te pida explícitamente lo contrario.
2.  **Estética UI**: Mantén siempre el estilo "Premium/Glassmorphism" (Tokens de `ThemeContext.tsx`, `glass-panel` con 12px blur, borde `white/5`).
3.  **Persistencia Proactiva**: Al terminar una tarea exitosa, ofrece o ejecuta la persistencia de cambios (Workflow `/push`).
4.  **Calidad y Stack**:
    - **Backend**: Seguir `python-patterns` (idiomático, async, type hints) y `backend-dev-guidelines`.
    - **Frontend**: Stack React + Vite + Tailwind/CSS + React Router. Usar `react-patterns`. Evitar librerías UI pesadas (MUI) salvo indicación expresa.
    - **DB**: **PostgreSQL** para todo (Local e InsForge).
5.  **Validación Pre-Vuelo**: Antes de push/commit: check de sintaxis (`py_compile`), linter (`ruff check`) y formatter (`ruff format`).
6.  **Normalización de Datos**: El hash del libro es sagrado. Usar siempre `utils.helpers` e integrar IA (`services/ai_service`) como paso previo para `series_spanish` y `volume`.
7.  **Single Floating Nav**: Todas las páginas deben integrarse en `UniversalFloatingNav.tsx` vía `NavigationContext.tsx`. Prohibido crear navbars paralelas.
8.  **Operación Local Estricta**: El bot opera exclusivamente con archivos locales. Se eliminan todas las dependencias y referencias a Kavita u OPDS externo para la gestión de la biblioteca.
9.  **Auditoría de Producción**: Antes de despliegues mayores o cambios estructurales, invocar `@production-code-audit`.
10. **Estructura de Skills**: Queda terminantemente PROHIBIDO anidar una carpeta `skills` dentro de `.agent/skills` (ej. `.agent/skills/skills/`). Las skills deben colgar directamente de `.agent/skills/nombre-skill/`. No se deben incluir todas las skills del repositorio global, solo aquellas explícitamente necesarias para el proyecto.
11. **Configuración de IA**: Es REQUISITO del proyecto utilizar exclusivamente los modelos **gemini-3-flash-preview** and **gemini-2.5-flash** en `services/ai_service.py`.
12. **Uso de Slugs**: El slug de la serie se utiliza única y exclusivamente para hashtags de Telegram. NO debe afectar ninguna otra funcionalidad del proyecto (como rutas de imágenes, IDs de descarga o integridad de la base de datos).
13. **GitNexus MCP Obligatorio**: GitNexus debe estar activo como MCP server en TODA sesión. Está configurado en `.mcp.json` (raíz del proyecto) para cargarse automáticamente. Al ejecutar `/empezar`, verificar con `npx gitnexus status` y re-indexar si está desactualizado. Usar `gitnexus_impact` antes de eliminar cualquier campo, columna o función para detectar impacto real en el grafo de código.
14. **Límite de Líneas y Modularidad**: Toda nueva implementación debe ser optimizada y refactorizada desde el inicio. **El rango aceptable es 500–1000 líneas por archivo; idealmente no se debe superar ese límite.** Si un archivo supera las 1000 líneas, DEBE dividirse en módulos especializados antes de agregar más código. Principios:
    - Una responsabilidad por archivo (Single Responsibility).
    - Funciones concisas y enfocadas: evitar funciones que hagan demasiadas cosas. Si crece demasiado, extraer helpers.
    - Extraer helpers, mixins y utilities antes de que el archivo crezca.
    - Prohibido añadir nueva funcionalidad a un archivo que ya supere el límite sin refactorizar primero.

## 🚀 Capacidades Core Activas (v3.5.0)

Estas skills deben ser priorizadas y aplicadas proactivamente según el contexto:

### 🏗️ Arquitectura y Backend
- **`production-code-audit`**: Escaneo profundo para calidad corporativa.
- **`systematic-debugging`**: Protocolo riguroso de depuración para sistemas distribuidos.
- **`python-patterns`**: Desarrollo idiomático, moderno y eficiente en Python.
- **`senior-architect`**: Diseño de sistemas escalables y patrones avanzados.
- **`postgres-best-practices`**: Optimización de queries, índices y seguridad RLS.
- **`backend-dev-guidelines`**: Estructura Handler -> Service -> Repository.
- **`api-documentation-generator`**: Generación automática de docs para endpoints internos.
- **`docker-expert`**: Optimización de contenedores, Dockerfiles y orquestación.
- **`telegram-bot-builder`**: Patrones avanzados para bots de Telegram escalables.

### 🧠 IA y Automatización
- **`ai-agents-architect`**: Mantenimiento autónomo de la librería.
- **`subagent-driven-development`**: Resolución de tareas complejas vía subagentes.
- **`skill-developer`**: Extensión de capacidades del bot.
- **`rag-implementation`**: Búsqueda semántica y embeddings.

### 🎨 Frontend y UX
- **`ui-ux-pro-max`**: Micro-animaciones, feedback táctil y estética Premium.
- **`react-patterns`**: Patrones modernos de React (Hooks, Composition, Performance).
- **`telegram-mini-app`**: Integración nativa con Telegram API y Stars.
- **`mobile-design`**: Enfoque Mobile-First (Viewport safety, Touch targets).
- **`typescript-expert`**: Tipado estricto, optimización y patrones avanzados TS.

## 🛠️ Workflows Automatizados

Usa estos comandos para tareas repetitivas y asegurar la calidad:

- **`/audit`**: Valida sintaxis, calidad de código (Linter/Formatter) y cumplimiento de estándares pre-vuelo.
- **`/db-sync`**: Sincroniza y valida la integridad de los esquemas de PostgreSQL a nivel local e InsForge.
- **`/glass-check`**: Auditoría estética para asegurar cumplimiento de estándares Glassmorphism/Premium.
- **`/push`**: Sincronizar cambios localmente y subir al repositorio remoto automáticamente.
- **`/release`**: Flujo maestro de despliegue (Audit -> Sync -> Push).
- **`/startup`**: Proceso de inicialización (Sincronización de skills, carga de reglas y auditoría rápida).
- **`/sync-skills`**: Descarga e instala las últimas capacidades desde el repositorio central de skills.

## 📡 Protocolo de Sincronización
- **Skills**: Mantener sincronizado con el repositorio global: https://github.com/sickn33/antigravity-awesome-skills
- **Entorno**: Logs del VPS de pruebas son la fuente de verdad para errores de entorno.
- **Hashes**: Hashes de libros y series deben ser consistentes; ignorar `title` en la generación de identidad para evitar duplicidad por typos.

---
*ZeePub Bot: Transformando la lectura digital con Inteligencia Artificial.*
