---
description: Proceso de inicialización automática del proyecto (Sincronización de skills y auditoría).
---

// turbo-all

1. Sincronizar Skills desde el repositorio global:
   `if (Test-Path temp_skills) { Remove-Item -Recurse -Force temp_skills }; git clone https://github.com/sickn33/antigravity-awesome-skills.git temp_skills; if (!(Test-Path .agent/skills)) { New-Item -ItemType Directory -Path .agent/skills }; Copy-Item -Recurse -Force temp_skills/* .agent/skills/; Remove-Item -Recurse -Force temp_skills; echo "[SUCCESS] Skills sincronizadas."`

2. Cargar reglas y configuración:
   `echo "[INFO] Cargando reglas desde proyecto.md..."`

3. Realizar una auditoría rápida de pre-vuelo:
   `echo "[INFO] Ejecutando auditoría de calidad..."`
   `ruff check .`

4. Notificar finalización:
   `echo "[READY] ZeePub-bot Enterprise está listo para operar."`
