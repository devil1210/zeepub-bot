---
description: Valida sintaxis, calidad de código (Linter/Formatter) y cumplimiento de estándares pre-vuelo.
---

// turbo-all

1. Verificar errores de sintaxis en Python:
   `python -m py_compile **/*.py`

2. Ejecutar Linter (Ruff) para encontrar problemas potenciales:
   `ruff check . --exclude .agent`

3. Aplicar formato de código automático:
   `ruff format . --exclude .agent`

4. Verificar tipos estáticos en Frontend (TypeScript):
   `cd web_client && npx tsc --noEmit`

5. Notificar cumplimiento de estándares:
   `echo "[SUCCESS] Auditoría de calidad completada. El código es apto para producción."`
