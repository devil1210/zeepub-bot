# Zeepub-bot Active Skills Configuration

This file defines the prioritized skills that should be active for the Zeepub-bot project context.

## Estándar de Formato para Skills
Cada skill en este proyecto debe seguir esta estructura:
- **Nombre**: Título de la skill.
- **Propósito**: Por qué es importante para Zeepub-bot.
- **Lecciones Aprendidas**: Errores pasados evitados mediante esta skill.
- **Reglas de Oro**: Pasos mandatorios al usarla.

---

## Core & Backend
- skill: python-patterns
  reason: Ensure clean, efficient, and typed Python code for FastAPI backend.
  lecciones: Error de importación de `List` en `miniapp_handlers.py`. Siempre verificar tipos básicos.
- skill: backend-dev-guidelines
  reason: Maintain layered architecture (Handlers -> Services -> Repositories).
- skill: clean-code
  reason: Prevent technical debt in a growing codebase.

## Calidad y Validación (CRITICAL)
- **skill: code-validation**
  **reason**: Evitar errores de sintaxis o imports faltantes antes de reportar éxito.
  **lecciones**: El bot reportó éxito pero el código falló por un NameError.
  **Reglas de Oro**: 
    1. Ejecutar siempre un check de sintaxis (`python -m py_compile`) tras editar un archivo .py.
    2. Verificar que todos los tipos (typing) usados estén importados.
- **skill: systematic-debugging**
  **reason**: Logical isolation of bugs in a distributed system.

## Datos & Infraestructura
- skill: postgres-best-practices
  reason: Optimize complex queries and indexing for library data.
- skill: database-design
  reason: Structure schema changes safely (SQLAlchemy/Supabase).
- skill: supabase-retry-logic
  reason: Handle transient 500/502 errors from cloud provider.

## Frontend & Telegram Integration
- skill: telegram-mini-app
- skill: ui-ux-pro-max
  reason: Enforce "Premium/Glassmorphism" design aesthetic.
- skill: react-patterns

---

## Próximos Pasos (Pendiente)
- Configurar Linter automático en GitHub Actions.
- Implementar reintentos en el cliente de Supabase.
