# src/services/ai/gemini_client.py
import logging
import json
from typing import Optional, Any
from google import genai
from google.genai import types
from src.core.config import settings
from src.services.ai.prompts import METADATA_NORMALIZATION_PROMPT, SERIES_ANALYZE_PROMPT

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Cliente envuelto para Gemini 3.1 Flash Lite.
    Mantiene la lógica de IA aislada y bajo las 500 líneas.
    """
    def __init__(self):
        self._client = None
        if settings.GEMINI_API_KEY:
            try:
                self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info(f"🧠 GeminiClient: Conectado con modelo {settings.GEMINI_MODEL}")
            except Exception as e:
                logger.error(f"❌ GeminiClient: Error de inicialización: {e}")

    async def normalize_metadata(self, filename: str, raw_data: dict) -> Optional[dict]:
        """Envía metadatos crudos a Gemini para su normalización."""
        if not self._client:
            return None
        
        context = f"Archivo: {filename}\nMetadatos Crudos: {json.dumps(raw_data, default=str)}"
        full_prompt = f"{context}\n\n{METADATA_NORMALIZATION_PROMPT}"
        
        try:
            # Llamada síncrona dentro de un thread si fuera necesario, 
            # pero el SDK de Google GenAI tiene soporte nativo async en versiones recientes.
            # Aquí usamos el modo síncrono simplificado para el esqueleto.
            response = self._client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"❌ GeminiClient Error (normalize): {e}")
            return None

    async def analyze_series(self, series_name: str, books_info: list) -> Optional[dict]:
        """Analiza una colección de libros para estandarizar la serie."""
        if not self._client:
            return None
        
        context = f"Serie Actual: {series_name}\nLibros: {json.dumps(books_info, default=str)}"
        full_prompt = f"{context}\n\n{SERIES_ANALYZE_PROMPT}"
        
        try:
            response = self._client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"❌ GeminiClient Error (analyze): {e}")
            return None

# Singleton expuesto
gemini_client = GeminiClient()
