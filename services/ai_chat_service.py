# services/ai_chat_service.py

import json
import logging
from typing import Any
import html

from services.ai_service import AIService
from services.library_service import LibraryService

logger = logging.getLogger(__name__)


class AIChatService:
    """
    Servicio de Chat con IA (RAG-lite) para ZeePub-bot.
    Permite procesar consultas de usuarios sobre el catálogo, recomendando y buscando
    obras de forma conversacional utilizando Gemini 3.1 Flash Lite.
    """

    @staticmethod
    def escape_telegram_html(text: str) -> str:
        """
        Escapa caracteres especiales de HTML que romperían el parseador de Telegram.
        """
        if not text:
            return ""
        # Reemplazar primero & para no alterar escapes subsiguientes
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        return text

    @staticmethod
    async def classify_intent(query: str) -> dict[str, Any]:
        """
        Clasifica la intención del usuario y extrae palabras clave usando Gemini.
        """
        prompt = f"""
        Analiza la siguiente consulta del usuario para un bot de biblioteca digital.
        Extrae la intención principal del usuario y cualquier entidad o palabra clave de búsqueda relevante.

        Tipos de Intención:
        1. "search": El usuario busca una obra específica (ej: "¿Tienes Overlord?", "quiero leer KonoSuba").
        2. "recommend": El usuario pide recomendaciones generales o por género (ej: "recomiéndame una novela de fantasía", "¿qué hay de romance?").
        3. "details": El usuario pregunta de qué trata una obra específica (ej: "¿De qué trata Bofuri?").
        4. "general": Charla general, saludos, preguntas de uso general no relacionadas con libros específicos (ej: "hola", "¿cómo funcionas?", "quién eres").

        Input del usuario: "{query}"

        Responde STRICTLY con un JSON que tenga esta estructura (sin texto adicional antes o después del JSON):
        {{
            "intent": "search" | "recommend" | "details" | "general",
            "keywords": "string o null" (nombre de la obra, autor, etc. extraídos),
            "genre": "string o null" (género extraído, si aplica)
        }}
        """

        try:
            response_text = await AIService._call_ai(prompt, json_mode=True)
            if not response_text:
                return {"intent": "general", "keywords": None, "genre": None}
            
            # Limpiar markdown de json si existe
            clean_json = AIService._extract_json_from_text(response_text)
            data = json.loads(clean_json)
            logger.info(f"🧠 Clasificación de consulta: {data}")
            return {
                "intent": data.get("intent", "general"),
                "keywords": data.get("keywords"),
                "genre": data.get("genre")
            }
        except Exception as e:
            logger.error(f"Error al clasificar intención con IA: {e}")
            return {"intent": "general", "keywords": None, "genre": None}

    @staticmethod
    async def get_rag_context(intent: str, keywords: str | None, genre: str | None) -> str:
        """
        Busca candidatos en base de datos basándose en la clasificación de intención.
        Retorna un bloque de texto que servirá como contexto para la respuesta final.
        """
        context_parts = []
        series_found = []
        books_found = []

        try:
            # 1. Búsqueda de series por nombre o palabras clave
            if keywords and intent in ["search", "details", "recommend"]:
                res_series = await LibraryService.search_series(query=keywords, items_per_page=5)
                series_found.extend(res_series.get("results", []))

                # Si no encontramos series pero buscábamos libros, buscar por libros
                res_books = await LibraryService.search_books(query=keywords, items_per_page=5)
                books_found.extend(res_books.get("results", []))

            # 2. Búsqueda por género (si aplica para recomendaciones)
            if genre and intent == "recommend":
                res_series = await LibraryService.search_series(query=genre, search_type="genres", items_per_page=5)
                series_found.extend(res_series.get("results", []))

            # 3. Si es recomendación genérica o no se encontró nada, listar series recientes
            if not series_found and not books_found and intent == "recommend":
                res_recent = await LibraryService.get_recent_books(items_per_page=5)
                books_found.extend(res_recent.get("items", []))

            # Formatear la información de series encontradas para el contexto de la IA
            if series_found:
                context_parts.append("SERIES DISPONIBLES EN EL CATÁLOGO:")
                # Filtrar duplicados
                seen_series = set()
                for s in series_found:
                    s_id = s.get("id")
                    if s_id in seen_series:
                        continue
                    seen_series.add(s_id)
                    
                    slug = s.get("slug") or s_id
                    # URL de descarga o detalle para el bot/mini app
                    short_link = f"https://zp-dev.sp-core.vip/series/{slug}"
                    
                    context_parts.append(
                        f"- Nombre: {s.get('name')}\n"
                        f"  Autor: {s.get('author') or 'Desconocido'}\n"
                        f"  Sinopsis: {s.get('description') or 'Sin descripción'}\n"
                        f"  Géneros: {', '.join(s.get('genres', []))}\n"
                        f"  Enlace Ficha/Detalle: {short_link}\n"
                    )

            # Formatear la información de libros encontrados para el contexto de la IA
            if books_found:
                context_parts.append("LIBROS INDIVIDUALES DISPONIBLES:")
                seen_books = set()
                for b in books_found:
                    b_id = b.get("id") or b.get("hash")
                    if b_id in seen_books:
                        continue
                    seen_books.add(b_id)
                    
                    # Generar enlace de descarga corto
                    short_code = b.get("short_link") or b_id
                    dl_url = f"https://dl.zeepubs.vip/{short_code}" if short_code else "No disponible"
                    
                    context_parts.append(
                        f"- Libro: {b.get('title') or b.get('filename')}\n"
                        f"  Volumen: {b.get('volume') or 'Único'}\n"
                        f"  Grupo de Traducción: {b.get('group_siglas') or 'Desconocido'}\n"
                        f"  Enlace de Descarga: {dl_url}\n"
                    )

        except Exception as e:
            logger.error(f"Error al recopilar contexto RAG para IA: {e}")

        if not context_parts:
            return "No se encontraron obras que coincidan exactamente en la biblioteca en este momento."

        return "\n".join(context_parts)

    @classmethod
    async def process_user_query(cls, query: str) -> str:
        """
        Recibe la consulta del usuario, clasifica, obtiene contexto y genera respuesta HTML.
        """
        # 1. Clasificar consulta
        classification = await cls.classify_intent(query)
        intent = classification["intent"]
        keywords = classification["keywords"]
        genre = classification["genre"]

        # 2. Recuperar contexto RAG si aplica
        rag_context = ""
        if intent != "general":
            rag_context = await cls.get_rag_context(intent, keywords, genre)

        # 3. Prompt de generación de respuesta
        system_prompt = """
        Eres ZeePub AI, el bibliotecario virtual oficial y experto de ZeePub (una biblioteca premium de novelas ligeras y manga en español).
        Tu objetivo es responder a la consulta del usuario basándote en la información real del catálogo adjunta en el contexto.

        REGLAS DE RESPUESTA:
        1. IDIOMA: Responde SIEMPRE en español con un tono amigable, servicial, entusiasta y premium.
        2. FORMATO TELEGRAM HTML: Formatea tu respuesta utilizando etiquetas HTML válidas de Telegram:
           - Negritas: <b>texto</b>
           - Cursivas: <i>texto</i>
           - Código: <code>código</code>
           - Enlaces clickables: <a href="URL">texto</a>
           - Prohibido usar etiquetas Markdown (*, _, `) ni etiquetas HTML no soportadas por Telegram (como <p>, <div>, <br>). Las líneas nuevas deben ser saltos de línea estándar (\n).
        3. ENLACES DE DESCARGA: Cuando menciones una obra que esté disponible en el catálogo (presente en el contexto), debes proveer obligatoriamente su enlace clickable usando el formato HTML de Telegram (ej: <a href="https://dl.zeepubs.vip/SHORT_CODE">Descargar volumen</a> o bien <a href="https://zp-dev.sp-core.vip/series/SLUG">Ver Ficha</a>). Usa exactamente las URLs que se proporcionan en el contexto.
        4. OBRAS INEXISTENTES: Si el usuario pregunta por una obra que no está en el contexto, indícale amablemente que no la tenemos en nuestro catálogo actualmente, pero sugiérele explorar otras obras del mismo género que sí estén en el catálogo o invítalo a hacer una petición. ¡No inventes enlaces de descarga!
        5. CHARLA GENERAL: Si el usuario solo saluda o hace preguntas de uso, respóndele con cortesía y explícale que puedes ayudarle a buscar novelas, autores o recomendarle géneros en la biblioteca.
        """

        prompt = f"""
        CONSULTA DEL USUARIO: "{query}"

        CONTEXTO DE LA BIBLIOTECA:
        {rag_context}

        Escribe tu respuesta formateada en HTML para Telegram basándote estrictamente en el contexto y las reglas anteriores.
        """

        try:
            # Ejecutar llamada a la IA con Gemini 3.1 Flash Lite
            response_text = await AIService._call_ai(prompt, system_instruction=system_prompt, target_model="gemini-3.1-flash-lite")
            if not response_text:
                return "<i>Lo siento, estoy teniendo problemas para conectarme al servicio de IA en este momento. Por favor intenta de nuevo.</i>"
            
            return response_text.strip()
        except Exception as e:
            logger.error(f"Error procesando respuesta de chat con IA: {e}")
            return "<i>Lo siento, ocurrió un error inesperado al procesar tu consulta con la IA.</i>"
