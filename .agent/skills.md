# Zeepub-bot Active Skills & Implementation Manifesto

Este archivo consolida las capacidades activas del proyecto y las reglas mandatorias de implementación, siguiendo los estándares globales de **v3.1.0**.

## 🏗️ Protocolos de Mantenimiento y Drift
1. **CI Drift Fix**: Ante discrepancias entre el código generado y el estado real del sistema (especialmente en bases de datos), seguir el protocolo de `docs/CI_DRIFT_FIX.md`.
2. **Generated Files**: Mantener una política estricta de no contaminación. Todo archivo generado debe residir en sus carpetas correspondientes (`scripts/`, `data/`, `logs/`).
3. **Versatilidad de Skills**: Solo se mantienen instaladas las skills que aportan valor directo al proyecto.

---

## 🚀 Capacidades Core Activas

### Backend & Arquitectura
- **python-patterns**: Código limpio, tipado y eficiente para FastAPI.
- **backend-dev-guidelines**: Arquitectura en capas (Handler -> Service -> Repository).
- **clean-code**: Prevención de deuda técnica.
- **software-architecture**: Integridad estructural y patrones de diseño.
- **postgres-best-practices**: Optimización para PostgreSQL 17 (JSONB, Indexing, ILIKE).

### IA & Automatización
- **ai-agents-architect**: Flujos de trabajo de agentes autónomos para el mantenimiento de la librería.
- **subagent-driven-development**: Implementación de features complejas mediante subagentes especializados.
- **rag-implementation**: Búsqueda semántica usando Gemini embeddings.
- **epub-metadata-mastery**: Normalización de hashes y metadatos de libros.

### Frontend & UI/UX
- **telegram-mini-app**: Integración nativa con la API de Telegram.
- **ui-ux-pro-max**: Estética Premium con Glassmorphism y micro-animaciones.
- **react-patterns**: Componentes reutilizables y manejo de estado eficiente.
- **mobile-design**: Enfoque Mobile-First para la Mini App.
- **scroll-experience**: Scrolling fluido y optimizado para móviles.

---

## 🛠️ Reglas Mandatorias de Implementación

### 🎨 Diseño y UX (`ui-ux-pro-max`, `mobile-design`)
1. **Línea de Base**: Todo componente React debe usar los tokens definidos en `ThemeContext.tsx`.
2. **Glassmorphism**: Usar `glass-panel` con desenfoque de 12px y borde `white/5`.
3. **Mobile-First**: Diseñar primero para pantallas de celular dentro de Telegram.
4. **Touch Feedback**: Los elementos clickeables deben tener `cursor-pointer` y feedback visual (opacidad/escala).
5. **Scroll**: Implementar `overflow-y: auto` con `overscroll-behavior: contain`.

### 🐍 Desarrollo Backend (`python-patterns`, `fastapi`)
1. **Validación**: Usar Pydantic y Type Hints en todos los nuevos métodos.
2. **Async**: Todo I/O (DB, Telegram, Archivos) DEBE ser `async/await`.
3. **Manejo de Errores**: Debug sistemático antes de cualquier corrección. No "parchear" sin entender la Causa Raíz.
4. **Linter**: Respetar `.flake8` y `.ruff.toml`. Prohibido el uso indiscriminado de `# noqa`.

### 🐘 Base de Datos & Datos (`postgres-best-practices`)
1. **Seguridad**: Consultas parametrizadas siempre (SQLAlchemy).
2. **Performance**: Índices obligatorios en `series_hash` y `book_hash`.
3. **Identidad**: El hash del libro es sagrado. Usar siempre `process_book_identity_comprehensive`.
4. **Normalización**: Priorizar IA (`services/ai_service`) para `series_spanish` y `volume`.

### 🐙 Workflow & GitHub (`git-pushing`)
1. **Commits**: Usar [Conventional Commits](https://www.conventionalcommits.org/).
2. **Push**: El resumen del push debe ser técnico y detallado.
3. **Sincronización**: Verificar rama activa (`GIT_BRANCH`) antes de cambios masivos.

### 🌐 Telegram Stars & Mini App
1. **Stars (XTR)**: Todo flujo de monetización o niveles premium DEBE usar Telegram Stars.
2. **Ready Event**: Llamar siempre a `tg.ready()` al montar la aplicación.
