---
description: Active las reglas (imprimiéndolas en contexto), actualice las skills y haga resumen.
---

// turbo-all

1. Refrescar memoria (Leer Manifesto):
   `Get-Content .agent\rules\proyecto.md`

2. Actualizar skills seleccionadas:
   `if (Test-Path temp_skills) { Remove-Item -Recurse -Force temp_skills }; git clone https://github.com/sickn33/antigravity-awesome-skills.git temp_skills; $skillsToKeep = @("production-code-audit", "systematic-debugging", "python-patterns", "senior-architect", "postgres-best-practices", "backend-dev-guidelines", "api-documentation-generator", "docker-expert", "telegram-bot-builder", "ai-agents-architect", "subagent-driven-development", "skill-developer", "rag-implementation", "ui-ux-pro-max", "react-patterns", "telegram-mini-app", "mobile-design", "typescript-expert", "lint-and-validate", "bash-linux"); foreach ($skill in $skillsToKeep) { if (Test-Path "temp_skills/skills/$skill") { Copy-Item -Recurse -Force "temp_skills/skills/$skill" ".agent/skills/" } }; Remove-Item -Recurse -Force temp_skills; echo "[SUCCESS] Skills actualizadas."`

3. Resumen de lo hecho:
   `echo "[SUMMARY] Manifesto cargado en contexto. Skills sincronizadas. Listo para trabajar bajo normativa."`
