
import json
import logging
import os
from typing import Any, Dict, Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

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
        Analiza un libro y devuelve metadatos normalizados.
        """
        model = AIService._get_model()
        if not model:
            return None

        prompt = f"""
        Actúa como un bibliotecario experto en novelas ligeras y manga. Tu tarea es normalizar los metadatos de un archivo de libro.
        
        Reglas de Normalización:
        1. **Series (Spanish)**: El nombre de la serie limpio. Si es "Kono Subarashii...", usa "KonoSuba". Si es en inglés, usa el nombre común en español si existe o mantenlo en inglés pero limpio. Elimina "Volumen X", tags, etc.
        2. **Volume**: Número del volumen. Si es 8, usa 8.0. Si es 8.5, usa 8.5.
        3. **Group**: El grupo de traducción o editorial. Si no hay, usa "Unknown".
        4. **Filename**: Genera el nombre de archivo EXACTO con este formato: "{{Series Name}} - V{{XX}} [{{Group}}].epub".
           - XX debe ser siempre 2 dígitos (01, 09, 10).
           - Si el volumen es float (8.5), usa (08.5).
        5. **Censura**: Detecta si el libro es "Sin Censura" (Uncensored) o "A Color" extraído del nombre o tags.

        Datos de Entrada:
        - Filename: "{filename}"
        - Metadata Cruda: {json.dumps(raw_meta, default=str)}

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
            txt = response.text.strip()
            if txt.startswith("```"):
                txt = txt.strip("```").strip("json").strip()
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
        Normaliza el siguiene nombre de una serie de novela ligera. Elimina volúmenes, "Novela Ligera", etiquetas de formato, y déjalo lo más limpio posible (Título Principal).
        
        Input: "{current_name}"
        
        Responde SOLO con el string del nombre limpio. Nada más.
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
        # Tomamos hasta 5 títulos de muestra para que la IA entienda el patrón
        sample_titles = [b.get("title", "") for b in books[:5]]
        
        prompt = f"""
        Actúa como un bibliotecario experto. Analiza esta serie de novelas ligeras/manga y propón una estandarización.
        
        Nombre Actual de la Serie: "{current_series_name}"
        Ejemplos de archivos en el grupo:
        {json.dumps(sample_titles, indent=2)}
        
        Tareas:
        1. **Series Name**: Determina el nombre canónico y limpio en Español (o Inglés si es el original). Elimina "Volumen X", "Novel", tags irrelevantes.
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
            txt = response.text.strip()
            if txt.startswith("```"):
                txt = txt.strip("```").strip("json").strip()
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
                # Pad volume with leading zero if needed (supporting floats like 8.5 -> 08.5)
                vol_val = float(current_vol)
                vol_str = f"{int(vol_val):02d}"
                if vol_val % 1 != 0:
                    vol_str += f".{str(vol_val).split('.')[1]}"
                
                new_filename = f"{analysis.get('proposed_series')} - V{vol_str}.epub"
                
                if book.get("filename") != new_filename:
                    proposal["changes"].append({
                        "book_id": book.get("id"),
                        "current_filename": book.get("filename") or book.get("title"),
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
