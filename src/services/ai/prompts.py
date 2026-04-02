# src/services/ai/prompts.py

METADATA_NORMALIZATION_PROMPT = """
Actúa como un bibliotecario experto en novelas ligeras y manga. Tu tarea es normalizar los metadatos de un archivo.

REGLAS DE IDIOMA:
- Todas las EXPLICACIONES y campos de texto libre deben estar en ESPAÑOL.
- **Series Name**: El nombre canónico de la serie (Inglés o Romaji).

Reglas de Extracción:
1. **Volume**: Extrae el número de volumen. Tomo único o volumen 0 = 0.0.
2. **Group Siglas**: Máximo 6 caracteres (ej: Dark Translations = DARKT).
3. **Suggested Filename**: Formato "[Prefix]Series Name - VXX [Siglas].epub".
   - Prefix: `[Color]`, `[SC]` o `[Color-SC]` si aplica.

Devuelve SOLO un JSON:
{
    "series_name": "string",
    "volume": float,
    "group_full": "string",
    "group_siglas": "string",
    "suggested_filename": "string",
    "is_uncensored": boolean,
    "color_mode": "color" | "bw" | "mixed",
    "book_type": "string",
    "genres": ["string"],
    "description": "string (máx 500 caracteres)",
    "confidence": float
}
"""

SERIES_ANALYZE_PROMPT = """
Analiza este grupo de libros y propón una estandarización coherente.
Tareas:
1. **Proposed Series Name**: Nombre oficial (Inglés/Romaji).
2. **Proposed Slug**: Identificador único (minúsculas, guiones bajos).
3. **Group & Siglas**: Identifica al traductor principal de los archivos.

Responde SOLO JSON con:
{
    "proposed_series": "string",
    "proposed_slug": "string",
    "group_full": "string",
    "group_siglas": "string",
    "reason": "Explicación en español",
    "confidence": float
}
"""
