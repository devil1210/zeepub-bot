---
name: notion-integration
description: Integration with Notion for logging readings, feedback, bugs, and book requests. Defines the schema and usage of the shared Notion database.
---

# Notion Integration Skill

This skill documents how Zeepub-bot integrates with Notion to maintain a log of activity, user feedback, and book requests.

## 1. Configuration

The integration relies on two environment variables defined in `config/config_settings.py`:
- `NOTION_TOKEN`: The integration token (secret).
- `NOTION_DATABASE_ID`: The ID of the master database.

## 2. Shared Database Schema

The system uses a **Single Master Database** strategy. Differentiation is done via the `Tipo` (Select) property.

### Common Properties
| Property Name | Type | Description |
| :--- | :--- | :--- |
| `Título` | Title | Main identifier (e.g., Book Title or "Feedback from User") |
| `Tipo` | Select | Event type: `Lectura`, `Sugerencia`, `Bug`, `Solicitud` |
| `Usuario` | Rich Text | Name/Username of the triggering user |
| `Fecha` | Date | ISO 8601 Timestamp of the event |

### Specific Properties by Type

**Type: `Lectura` (Reading Log)**
- `Serie` (Rich Text): Series name.
- `Volumen` (Number): Volume number.
- `Autor` (Rich Text): Author name.

**Type: `Sugerencia` / `Bug` (Feedback)**
- `Comentarios` (Rich Text): The feedback message content.
- Note: `Título` is formattted as `"{Category} de {User}"`.

**Type: `Solicitud` (Book Request)**
- `Serie` (Rich Text): Used to store the Requested Book Name (for sorting/filtering).
- `Comentarios` (Rich Text): Contains Author and extra notes.
- `Título` is formatted as `"Solicitud: {Book Name}"`.

## 3. Usage Pattern (Backend)

Use the singleton instance `notion_service` from `services.notion_service`.

```python
from services.notion_service import notion_service

# Log a download/reading
await notion_service.log_reading(user_name="User", book_title="Oregairu 14", series_name="Oregairu", volume="14")

# Log feedback
await notion_service.log_feedback(user_name="User", message="UI is broken", category="Bug")

# Log request
await notion_service.log_book_request(user_name="User", book_name="New Novel", author="Author")
```

## 4. MCP Tools Integration

The `notion-mcp-server` is available in the toolset but the Zeepub-bot project prefers using the `NotionService` wrapper for consistency with the domain logic. Direct MCP calls should be reserved for administrative tasks or ad-hoc queries not covered by the service.
