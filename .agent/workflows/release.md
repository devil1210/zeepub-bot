---
description: Flujo completo de producción: Auditoría + DB Sync + Push.
---

// turbo-all

1. Ejecutar Auditoría de Calidad:
   `npx antigravity-run /audit`

2. Ejecutar Sincronización de Base de Datos:
   `npx antigravity-run /db-sync`

3. Ejecutar Auditoría Estética:
   `npx antigravity-run /glass-check`

4. Empujar cambios a producción:
   `npx antigravity-run /push`

5. Notificar fin de ciclo de vida:
   `echo "[RELEASE] Ciclo de vida v3.6.6 completado con éxito. Sistema en producción."`
