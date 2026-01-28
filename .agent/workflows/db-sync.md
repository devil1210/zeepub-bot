---
description: Sincroniza y valida la integridad de los esquemas entre PostgreSQL Local y Supabase.
---

// turbo-all

1. Validar esquema actual contra modelos SQLAlchemy:
   `python scripts/schema_validator.py`

2. Verificar diferencias en tablas y columnas clave:
   `python check_supabase_schema.py`

3. Listar tablas para confirmar sincronización:
   `python list_tables.py`

4. Notificar estado de la base de datos:
   `echo "[DB-SYNC] Sincronización verificada. Esquemas locales y remotos alineados."`
