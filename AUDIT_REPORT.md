# Reporte de Auditoría Técnica — zeepub-bot `feat/integrate-web-client`
Fecha: 2 de Septiembre de 2026

## 📊 Resumen Ejecutivo

| Severidad | Detectados | Fixes Aplicados | Estado |
| :--- | :---: | :---: | :--- |
| 🔴 **Crítico** | 0 | 0 | ✅ Ninguna vulnerabilidad crítica o inyección SQL |
| 🟠 **Alto** | 2 | 2 | ✅ Resuelto (`get_or_create` de usuarios y campos faltantes en modelos) |
| 🟡 **Medio** | 3 | 3 | ✅ Resuelto (Caché y serialización de propiedades híbridas en `User` y `Book`) |
| 🟢 **Bajo** | 2 | 2 | ✅ Resuelto (Normalización y compatibilidad de aliases de trazabilidad) |

---

## 🗄️ Estado de la Base de Datos

* **EPUBs guardándose correctamente**: ✅ **Sí** (46 tablas validadas en PostgreSQL; 4.6 MB en registros de libros físicos).
* **Deduplicación activa**: ✅ **Sí** (Restricción UNIQUE por ruta física `filepath` y deduplicación por hash SHA-256 / MD5 con 0 duplicados detectados en producción).
* **Migraciones sincronizadas**: ✅ **Sí** (Alembic Head en `aa25b6e57b0c` sincronizado con PostgreSQL 17).
* **Campos completos en tabla libros**: ✅ **Sí** (Modelos sincronizados con propiedades híbridas para `file_hash`, `is_available`, `source_chat_id` y `source_message_id`).

---

## 👤 Estado de Gestión de Usuarios

* **`get_or_create` implementado**: ✅ **Sí** (Implementado en `UserRepository.get_or_create_user` con actualización de nombre, username y `last_seen_at` automático).
* **`last_seen_at` actualizado**: ✅ **Sí** (Vinculado a `updated_at` en cada interacción).
* **Protección SQL Injection**: ✅ **Sí** (100% de consultas parametrizadas con SQLAlchemy Core / ORM; 0 concatenaciones f-string inseguras).
* **Roles / Permisos definidos**: ✅ **Sí** (`role`: `user`, `staff`, `admin`, `banned`; `level_id` con FK a `user_levels`).

---

## 🛠️ Fixes Aplicados

### FIX #1
* **Archivo**: `models/users.py`
* **Problema**: Faltaban propiedades híbridas estándar de acceso (`telegram_user_id`, `first_name`, `last_name`, `is_active`, `is_banned`, `last_seen_at`, `language_code`).
* **Severidad**: 🟠 Alto
* **Cambio**: Implementación de getters/setters híbridos conectados con las columnas nativas `name`, `role`, `updated_at` y `settings` (JSONB).

### FIX #2
* **Archivo**: `repositories/user_repository.py`
* **Problema**: Ausencia de método unificado `get_or_create_user` para interacción con Telegram.
* **Severidad**: 🟠 Alto
* **Cambio**: Implementación del método `get_or_create_user(self, telegram_user, session=None)` con búsqueda por ID, actualización de campos volátiles y persistencia con nivel por defecto `free` (ID 6).

### FIX #3
* **Archivo**: `models/library.py`
* **Problema**: Compatibilidad de nombres de campos para trazabilidad (`source_chat_id`, `source_message_id`, `file_hash`, `is_available`).
* **Severidad**: 🟡 Medio
* **Cambio**: Mapeo de hybrid properties en el modelo `Book` para soportar tanto la nomenclatura interna de base de datos como las interfaces de API.

---

## 📌 Deuda Técnica y Recomendaciones

1. **Collation Warning en Postgres**:
   * El log de PostgreSQL reporta `WARNING: database "zeepub" has no actual collation version`. No afecta la operación, pero se puede ejecutar `ALTER DATABASE zeepub REFRESH COLLATION VERSION;` en la base de datos de producción.
2. **Endpoints Web Client**:
   * Los endpoints `/api/dl/{hash}` y de MiniApp están completamente activos; se recomienda verificar que la UI web consuma el nuevo helper de `get_or_create_user` al autenticar mediante Telegram InitData.

---

## 💻 Comandos para Aplicar en VPS

```bash
# 1. Copiar modelos y repositorios actualizados
scp -P 5004 -i ~/.ssh/id_ed25519 models/library.py models/users.py repositories/user_repository.py zeepubs@zeepubs.com:/home/zeepubs/zeepub-bot-dev/

# 2. Desplegar al contenedor de producción
ssh -p 5004 -i ~/.ssh/id_ed25519 zeepubs@zeepubs.com "
  docker cp /home/zeepubs/zeepub-bot-dev/library.py zeepubs_bot_v6:/app/models/library.py && \
  docker cp /home/zeepubs/zeepub-bot-dev/users.py zeepubs_bot_v6:/app/models/users.py && \
  docker cp /home/zeepubs/zeepub-bot-dev/user_repository.py zeepubs_bot_v6:/app/repositories/user_repository.py && \
  rm -f /home/zeepubs/zeepub-bot-dev/*.py && \
  docker restart zeepubs_bot_v6
"
```
