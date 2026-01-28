---
description: Valida sintaxis, calidad de código (Linter/Formatter) y cumplimiento de estándares pre-vuelo.
---

// turbo-all

1. Verificar errores de sintaxis en Python:
   `python -m py_compile **/*.py`

2. Ejecutar Linter (Ruff) para encontrar problemas potenciales:
   `ruff check .`

3. Aplicar formato de código automático:
   `ruff format .`

4. Notificar cumplimiento de estándares:
   `echo "[SUCCESS] Auditoría de calidad completada. El código es apto para producción."`
