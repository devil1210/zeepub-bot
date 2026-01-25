
import json
import logging
from typing import Any, Dict, Optional

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
    async def normalize_book_metadata(filename: str, raw_meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analiza un libro y devuelve metadatos normalizados, priorizando la extracción de volumen desde metadatos internos.
        """
        model = AIService._get_model()
        if not model:
            return None

        prompt = f"""
        Actúa como un bibliotecario experto en novelas ligeras y manga. Tu tarea es normalizar los metadatos de un archivo de libro, extrayendo información precisa especialmente del número de volumen.

        Reglas de Normalización:
        1. **Series (Spanish)**: El nombre de la serie limpio. Elimina "Volumen X", tags, etc. 
           **REGLA DE ORO**: PRIORIZA SIEMPRE EL IDIOMA ESPAÑOL. Aunque la serie sea más conocida por su nombre en Inglés o Romaji, debes usar el título oficial en español (ej: "El calabozo oculto en el que solo yo puedo entrar" en lugar de "The Hidden Dungeon..." u "Ore dake Haireru...").
        2. **Volume (EXTREMANTE IMPORTANTE)**: Debes extraer el número de volumen con total precisión.
           - **Prioridad 1 (Metadata)**: Busca en la 'Metadata Cruda'. Busca campos como 'volume_index', 'calibre:series_index', o menciones dentro de 'titulo_volumen', 'title', o 'sinopsis'. 
           - **Prioridad 2 (Filename)**: Si no hay metadata clara, usa el nombre del archivo.
           - **Formato**: Devuelve un número (float). Ej: 1.0, 8.5.
        3. **Group**: El grupo de traducción o editorial (ej. 'Athena', 'Traduxiones', 'Athena Scanlation'). Si no hay, usa "Unknown".
        4. **Suggested Filename**: Genera el nombre de archivo EXACTO con este formato: "{{Series Clean}} - V{{XX}} [{{Group}}].epub".
           - **REGLAS DE FORMATO V{{XX}}**:
             - Si el volumen es entero (1, 9, 10): Usa 2 dígitos PAD. Ej: **V01, V09, V10**.
             - Si el volumen es decimal (8.5): Usa 2 dígitos para la parte entera. Ej: **V08.5, V10.5**.
             - **CRÍTICO**: NUNCA uses V01.0, V02.0, etc. Si es un número entero, no debe llevar decimales.
        5. **Censura/Tipo**: Detecta si el libro es "Sin Censura" (Uncensored) o "A Color" basándote en la metadata cruda o el nombre.

        Datos de Entrada:
        - Filename Original: "{filename}"
        - Metadata Cruda (Contenido del EPUB): {json.dumps(raw_meta, default=str)}

        Devuelve SOLO un JSON con esta estructura:
        {{
            "series_spanish": "string",
            "volume": float,
            "group": "string",
            "suggested_filename": "string",
            "is_uncensored": boolean,
            "color_mode": "color" | "bw" | "mixed",
            "confidence": float (0.0 to 1.0)
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
        Normaliza el siguiente nombre de una serie de novela ligera.
        
        REGLAS:
        1. Elimina volúmenes, "Novela Ligera", etiquetas de formato.
        2. PRIORIZA SIEMPRE EL IDIOMA ESPAÑOL. Si el input está en Inglés o Romaji y conoces el título oficial en Español, usa el de Español.
        
        Input: "{current_name}"
        
        Responde SOLO con el string del nombre limpio en ESPAÑOL. Nada más.
        """
        
        try:
            # For this simple query we don't strictly need JSON, but let's keep it consistent or just get text
            # Override config for simple text
            simple_model = genai.GenerativeModel("gemini-3-flash-preview") 
            response = await simple_model.generate_content_async(prompt)
            return response.text.strip()
        except Exception:
            return current_name

    @staticmethod
    async def analyze_series_for_updates(series_hash: str, current_series_name: str, books: list[Dict[str, Any]]) -> Dict[str, Any]:
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
        Actúa como un bibliotecario experto. Analiza esta serie de novelas ligeras/manga y propón una estandarización.
        
        Nombre Actual de la Serie: "{current_series_name}"
        Ejemplos de archivos en el grupo:
        {json.dumps(sample_titles, indent=2)}
        
        Tareas:
        1. **Series Name**: Determina el nombre canónico y limpio en ESPAÑOL. 
           - **REGLA CRÍTICA**: Ignora nombres en Inglés o Romaji si existe un título en Español. Preferimos "El calabozo oculto..." sobre "The Hidden Dungeon..." u "Ore dake Haireru...".
           - Los archivos actuales pueden estar ya en español; úsalos como referencia.
        2. **Tags**: Detecta tags globales basados en los títulos (ej: "Uncensored", "Color").
        3. **Confidence**: Qué tan seguro estás de que estos libros pertenecen a la misma serie (0.0 a 1.0).
        
        Responde SOLO con este JSON:
        {{
            "proposed_series": "string",
            "reason": "string (breve explicación)",
            "detected_tags": ["tag1", "tag2"],
            "is_uncensored_series": boolean,
            "confidence": float
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
                "proposed_series": analysis.get("proposed_series"),
                "reason": analysis.get("reason"),
                "confidence": analysis.get("confidence"),
                "global_tags": analysis.get("detected_tags", []),
                "changes": []
            }
            
            # Generar cambios individuales (Renombrado de archivos)
            # Esto se hace en código Python para garantizar consistencia con la Regla 8, 
            # usando el nombre de serie propuesto por la IA.
            for book in books:
                current_vol = book.get("volume", 0)
                # Pad volume with leading zero if needed (supporting floats like 8.5 -> 08.5)
                vol_val = float(current_vol)
                vol_str = f"{int(vol_val):02d}"
                if vol_val % 1 != 0:
                    vol_str += f".{str(vol_val).split('.')[1]}"
                
                new_filename = f"{analysis.get('proposed_series')} - V{vol_str}.epub"
                
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
    async def generate_synopsis(title: str, description: str) -> Optional[str]:
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
