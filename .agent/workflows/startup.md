---
description: Proceso de inicialización automática del proyecto (Sincronización de skills y auditoría).
---

// turbo-all

1. Sincronizar Skills seleccionadas:
   `if (Test-Path temp_skills) { Remove-Item -Recurse -Force temp_skills }; git clone https://github.com/sickn33/antigravity-awesome-skills.git temp_skills; if (!(Test-Path .agent/skills)) { New-Item -ItemType Directory -Path .agent/skills }; $skillsToKeep = @("production-code-audit", "systematic-debugging", "python-patterns", "senior-architect", "postgres-best-practices", "backend-dev-guidelines", "api-documentation-generator", "docker-expert", "telegram-bot-builder", "ai-agents-architect", "subagent-driven-development", "skill-developer", "rag-implementation", "ui-ux-pro-max", "react-patterns", "telegram-mini-app", "mobile-design", "typescript-expert", "lint-and-validate", "bash-linux"); foreach ($skill in $skillsToKeep) { if (Test-Path "temp_skills/skills/$skill") { Copy-Item -Recurse -Force "temp_skills/skills/$skill" ".agent/skills/" } }; Remove-Item -Recurse -Force temp_skills; echo "[SUCCESS] Skills seleccionadas sincronizadas sin anidamiento."`

2. Cargar reglas y configuración:
   `echo "[INFO] Cargando reglas desde proyecto.md..."`

3. Realizar una auditoría rápida de pre-vuelo:
   `echo "[INFO] Ejecutando auditoría de calidad..."`
   `ruff check .`

4. Notificar finalización:
   `echo "[READY] ZeePub-bot Enterprise está listo para operar."`
