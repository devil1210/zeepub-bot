---
description: Descarga e instala las últimas capacidades desde el repositorio central de skills.
---

// turbo-all

1. Limpiar directorio temporal previo (si existe):
   `if (Test-Path temp_skills) { Remove-Item -Recurse -Force temp_skills }`

2. Clonar repositorio de skills:
   `git clone https://github.com/sickn33/antigravity-awesome-skills.git temp_skills`

3. Copiar skills al directorio del agente:
   `Copy-Item -Recurse -Force temp_skills/* .agent/skills/`

4. Limpiar directorio temporal:
   `Remove-Item -Recurse -Force temp_skills`

5. Notificar éxito:
   `echo "[SUCCESS] Skills sincronizadas correctamente desde el repositorio global."`
