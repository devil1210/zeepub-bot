---
description: Auditoría estética para asegurar cumplimiento de estándares Glassmorphism/Premium.
---

// turbo-all

1. Buscar componentes que no implementen ThemeContext (estética manual):
   `grep -rL "ThemeContext" web_client/src/components web_client/pages`

2. Verificar el uso de la clase 'glass-panel' en los nuevos componentes:
   `grep -r "glass-panel" web_client/src/components web_client/pages`

3. Validar consistencia de colores primarios y bordes:
   `grep -r "border-white/5" web_client/src/components web_client/pages`

4. Notificar hallazgos estéticos:
   `echo "[UI-AUDIT] Revisión estética completada. Verificar logs para componentes sin ThemeContext."`
