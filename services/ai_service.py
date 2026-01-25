
import json
import logging
from typing import Any

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory

from config.config_settings import config

logger = logging.getLogger(__name__)

class AIService:
    """
    Gestiona la interacción con Google Gemini para análisis inteligente de libros.
    """
    _model = None

    @classmethod
    def _get_model(cls):
        """Inicializa el modelo Gemini con la configuración."""
        if cls._model:
            return cls._model

        if not config.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY no configurada. Funciones de IA deshabilitadas.")
            return None

        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            
            # Configuración de seguridad permisiva para análisis de textos literarios
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            cls._model = genai.GenerativeModel(
                model_name="gemini-3-flash-preview",
                safety_settings=safety_settings,
                generation_config={"response_mime_type": "application/json"}
            )
            return cls._model
        except Exception as e:
            logger.error(f"Error inicializando Gemini: {e}")
            return None

    @staticmethod
    async def normalize_book_metadata(filename: str, raw_meta: dict[str, Any]) -> dict[str, Any] | None:
        """
        Analiza un libro y devuelve metadatos normalizados, priorizando la extracción de volumen desde metadatos internos.
        """
        model = AIService._get_model()
        if not model:
            return None

        prompt = f"""
        Actúa como un bibliotecario experto en novelas ligeras y manga. Tu tarea es normalizar los metadatos de un archivo de libro.

        Reglas de Idioma:
        1. **Series (English)**: El nombre de la serie oficial en INGLÉS. Este se usará para la base de datos.
        2. **Series (Spanish)**: El nombre oficial o más común en ESPAÑOL. **IMPORTANTE**: Este nombre se usará EXCLUSIVAMENTE para generar el 'Suggested Filename'.
           - Ejemplo: "The Hidden Dungeon Only I Can Enter" (English) vs "El calabozo oculto en el que solo yo puedo entrar" (Spanish).

        Reglas de Extracción:
        3. **Volume (CRÍTICO)**: Extrae el número de volumen con total precisión.
           - **Prioridad 1 (Metadata)**: Busca 'volume_index', 'calibre:series_index'.
           - **Prioridad 2 (Filename)**: Si el archivo dice "V08" o "Volumen 8", el volumen es 8.0.
           - **EVITA EL V00**: Si no encuentras el volumen, intenta inferirlo. No pongas 0 a menos que sea realmente un volumen 0, prólogo o extra.
        4. **Group & Siglas**:
           - **Group**: Nombre completo del grupo (ej. 'Athena Scanlation').
           - **Siglas**: La abreviatura del grupo que suele ir entre corchetes (ej. 'GET', 'Tdx', 'AS'). Búscalo en el nombre del archivo: lo que esté entre `[]` es la sigla.
        5. **Suggested Filename**: Genera el nombre EXACTO: "{{Series Spanish}} - V{{XX}} [{{Siglas}}].epub".
           - **Formato V{{XX}}**: Siempre 2 dígitos. Ej: V01, V09, V10. 
           - **Decimales**: Solo si existen. Ej: V08.5. NUNCA uses V01.0.

        Datos de Entrada:
        - Filename Original: "{filename}"
        - Metadata Cruda: {json.dumps(raw_meta, default=str)}

        Devuelve SOLO un JSON:
        {{
            "series_english": "string",
            "series_spanish": "string",
            "volume": float,
            "group_full": "string",
            "group_siglas": "string",
            "suggested_filename": "string",
            "is_uncensored": boolean,
            "color_mode": "color" | "bw" | "mixed",
            "confidence": float
        }}
        """

        try:
            # Ejecutar en threadpool para no bloquear el loop async
            response = await model.generate_content_async(prompt)
            txt = AIService._extract_json_from_text(response.text)
            return json.loads(txt)
        except Exception as e:
            logger.error(f"Error en consulta a Gemini: {e}")
            return None

    @staticmethod
    async def suggest_series_rename(current_name: str) -> str:
        """Sugiere un nombre de serie limpio/estándar."""
        model = AIService._get_model()
        if not model:
            return current_name

        prompt = f"""
        Normaliza el nombre de la serie.
        
        REGLAS:
        1. Elimina volúmenes, "Novela Ligera", etiquetas de formato.
        2. proposed_english: Nombre oficial en INGLÉS o ROMAJI.
        3. proposed_spanish: Nombre oficial en ESPAÑOL.
        
        Input: "{current_name}"
        
        Responde SOLO con un JSON:
        {{
            "proposed_english": "string",
            "proposed_spanish": "string"
        }}
        """
        
        try:
            response = await model.generate_content_async(prompt)
            txt = AIService._extract_json_from_text(response.text)
            return json.loads(txt)
        except Exception:
            return {"proposed_english": current_name, "proposed_spanish": current_name}

    @staticmethod
    async def analyze_series_for_updates(series_hash: str, current_series_name: str, books: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Analiza un grupo de libros y propone estandarización.
        Retorna un objeto 'proposal' con los cambios sugeridos.
        """
        model = AIService._get_model()
        if not model:
            return {"error": "AI not configured"}
            
        # 1. Preparar contexto para la IA
        # Preferimos mostrar el filename o el nombre en español para que la IA entienda el estado actual
        sample_titles = []
        for b in books[:10]:
            name = b.get("filename") or b.get("spanish_title") or b.get("title", "")
            sample_titles.append(name)
        
        prompt = f"""
        Actúa como un bibliotecario experto. Analiza este grupo de libros y propón una estandarización coherente.
        
        Nombre Actual en DB: "{current_series_name}"
        Archivos de muestra: {json.dumps(sample_titles, indent=2)}
        
        Tareas:
        1. **Proposed English Name**: El nombre canónico en INGLÉS/ROMAJI (para la base de datos).
        2. **Proposed Spanish Name**: El nombre oficial en ESPAÑOL (para los archivos).
        3. **Group Siglas**: Identifica la sigla del grupo (ej: 'GET', 'Tdx') de los archivos.
        4. **Volumes**: Para cada archivo, confirma su volumen real.
        
        REGLA DE ORO DE VOLUMEN:
        - NUNCA uses "V00" si el archivo tiene un número (ej: "Volumen 1" -> V01).
        - Si no estás seguro, usa el número que aparezca en el título o filename.
        
        Responde SOLO con este JSON:
        {{
            "proposed_english": "string",
            "proposed_spanish": "string",
            "group_siglas": "string",
            "detected_tags": ["tag1", "tag2"],
            "is_uncensored_series": boolean,
            "confidence": float,
            "reason": "string",
            "volumes": {{
                "filename_original": float_volumen
            }}
        }}
        """
        
        try:
            response = await model.generate_content_async(prompt)
            txt = AIService._extract_json_from_text(response.text)
            analysis = json.loads(txt)
            
            # Construir propuesta detallada
            proposal = {
                "series_hash": series_hash,
                "current_series": current_series_name,
                "proposed_series": analysis.get("proposed_english"),
                "proposed_spanish": analysis.get("proposed_spanish"),
                "group_siglas": analysis.get("group_siglas", "Unknown"),
                "reason": analysis.get("reason"),
                "confidence": analysis.get("confidence"),
                "global_tags": analysis.get("detected_tags", []),
                "changes": []
            }
            
            # Generar cambios individuales (Renombrado de archivos)
            ai_volumes = analysis.get("volumes", {})
            
            for book in books:
                orig_name = book.get("filename") or book.get("title", "")
                # Usar volumen detectado por IA si existe, sino el actual
                current_vol = ai_volumes.get(orig_name, book.get("volume", 0))
                
                # Pad volume with leading zero
                vol_val = float(current_vol)
                vol_str = f"{int(vol_val):02d}"
                if vol_val % 1 != 0:
                    vol_str += f".{str(vol_val).split('.')[1]}"
                
                # Generar nuevo nombre de archivo usando el nombre en ESPAÑOL y las SIGLAS
                spanish_name = proposal["proposed_spanish"] or proposal["proposed_series"]
                siglas = proposal["group_siglas"] or "Unknown"
                new_filename = f"{spanish_name} - V{vol_str} [{siglas}].epub"
                
                if book.get("filename") != new_filename:
                    proposal["changes"].append({
                        "book_id": book.get("id"),
                        "current_filename": book.get("filename") or book.get("filepath") or book.get("title"),
                        "proposed_filename": new_filename,
                        "volume": current_vol
                    })
            
            return proposal
            
        except Exception as e:
            logger.error(f"Error analyzing series: {e}")
            return {"error": str(e)}

    @staticmethod
    async def generate_synopsis(title: str, description: str) -> str | None:
        """Genera una sinopsis corta y atractiva para el libro."""
        model = AIService._get_model()
        if not model:
            return None

        prompt = f"""
        Actúa como un redactor creativo de una editorial de novelas ligeras. Tu tarea es escribir una sinopsis corta y atractiva para el siguiente libro.
        
        Título: "{title}"
        Descripción Original: "{description[:2000] if description else 'Sin descripción'}" 
        
        Reglas:
        1. Idioma: Español.
        2. Longitud: Máximo 300 caracteres.
        3. Tono: Intrigante y emocionante.
        4. Evita: Spoilers innecesarios y listas de capítulos. Solo el núcleo de la trama.
        5. Formato: Solo el texto de la sinopsis, sin comillas ni intros.
        """

        try:
            # Use basic model for text output
            simple_model = genai.GenerativeModel("gemini-3-flash-preview")
            response = await simple_model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generando sinopsis: {e}")
            return None

    @staticmethod
    def _extract_json_from_text(text: str) -> str:
        """Extrae el bloque JSON de una respuesta de Gemini (maneja markdown)."""
        txt = text.strip()
        if "```json" in txt:
            txt = txt.split("```json")[1].split("```")[0].strip()
        elif "```" in txt:
            # Buscar el primer bloque de código si no tiene etiqueta 'json'
            parts = txt.split("```")
            if len(parts) >= 3:
                txt = parts[1].strip()
            else:
                txt = txt.strip("`").strip()
        return txt
