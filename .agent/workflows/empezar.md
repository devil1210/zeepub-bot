---
description: Active las reglas (imprimiéndolas en contexto), actualice las skills y haga resumen.
---

// turbo-all

1. Refrescar memoria (Leer Manifesto):
   `Get-Content .agent\rules\proyecto.md`

2. Verificar y arrancar GitNexus MCP (fuente de verdad del grafo de código):
   `npx gitnexus status 2>&1 | Select-Object -First 5; npx gitnexus analyze`
   > GitNexus debe quedar activo como MCP server (configurado en `.mcp.json`). Si el índice está desactualizado, `analyze` lo regenera. El MCP se inicia automáticamente en cada sesión gracias a `.mcp.json`.

3. Actualizar skills seleccionadas:
   `if (Test-Path temp_skills) { Remove-Item -Recurse -Force temp_skills }; git clone https://github.com/sickn33/antigravity-awesome-skills.git temp_skills; $skillsToKeep = @("production-code-audit", "systematic-debugging", "python-patterns", "senior-architect", "postgres-best-practices", "backend-dev-guidelines", "api-documentation-generator", "docker-expert", "telegram-bot-builder", "ai-agents-architect", "subagent-driven-development", "skill-developer", "rag-implementation", "ui-ux-pro-max", "react-patterns", "telegram-mini-app", "mobile-design", "typescript-expert", "lint-and-validate", "bash-linux", "frontend-dev-guidelines", "fastapi-pro", "security-audit", "clean-code", "prompt-engineering-patterns", "git-pushing"); foreach ($skill in $skillsToKeep) { if (Test-Path "temp_skills/skills/$skill") { Copy-Item -Recurse -Force "temp_skills/skills/$skill" ".agent/skills/" } }; echo "[SUCCESS] Skills actualizadas."`

4. Analizar Novedades y Proponer Skills:
   `git -C temp_skills log -n 25 --oneline; Remove-Item -Recurse -Force temp_skills`
   Revisa el historial reciente arrojado por el comando para identificar skills nuevas o actualizadas (releases 6.4.0, 6.4.1, 6.5.0, etc). Evalúa cuáles son útiles para el proyecto y sugiere agregarlas a la lista `$skillsToKeep`.

5. Resumen de lo hecho:
   `echo "[SUMMARY] Manifesto cargado. GitNexus MCP activo. Skills sincronizadas. Novedades analizadas. Listo bajo normativa."`
