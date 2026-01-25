
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
                model_name="gemini-1.5-flash",
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
            return json.loads(response.text)
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
            simple_model = genai.GenerativeModel("gemini-1.5-flash") 
            response = await simple_model.generate_content_async(prompt)
            return response.text.strip()
        except Exception:
            return current_name
