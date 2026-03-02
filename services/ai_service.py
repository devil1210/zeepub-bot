import asyncio
import json
import logging
import time
from typing import Any

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

from config.config_settings import config

logger = logging.getLogger(__name__)


class AIService:
    """
    Servicio unificado de IA.
    Soporta Google Gemini (SDK v0.3+).
    """

    _client: Any | None = None
    _exhausted_until: dict[str, float] = {}

    @classmethod
    def _get_client(cls):
        """Devuelve el cliente de Google GenAI."""
        if not config.GEMINI_API_KEY:
            return None
        if cls._client is None and genai:
            cls._client = genai.Client(api_key=config.GEMINI_API_KEY)
        return cls._client

    @classmethod
    async def _call_ai(
        cls,
        prompt: str,
        system_instruction: str | None = None,
        max_retries: int = 3,
        json_mode: bool = False,
        target_model: str | None = None,
    ) -> str | None:
        """Llamada a servicios de IA (Gemini o Perplexity)."""
        # 1. Perplexity Routing
        if target_model == "perplexity":
            return await cls._call_perplexity(prompt, system_instruction, max_retries, json_mode)

        # 2. Gemini Routing (Default)
        client = cls._get_client()
        if not client:
            return None

        # Modelos: gemini-2.5-flash (estable/por defecto según usuario), gemini-3-flash-preview
        models_to_try = [target_model] if target_model else ["gemini-2.5-flash", "gemini-3-flash-preview"]
        now = time.time()

        for model_name in models_to_try:
            if model_name in cls._exhausted_until and now < cls._exhausted_until[model_name]:
                continue

            for attempt in range(max_retries):
                try:
                    config_args = types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json" if json_mode else "text/plain",
                    )

                    response = client.models.generate_content(model=model_name, contents=prompt, config=config_args)
                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        usage = response.usage_metadata
                        logger.info(
                            f"🧠 [{model_name}] Tokens -> In: {usage.prompt_token_count} | Out: {usage.candidates_token_count} | Total: {usage.total_token_count}"
                        )
                    return response.text
                except Exception as e:
                    error_str = str(e).upper()
                    if "429" in error_str or "QUOTA" in error_str:
                        logger.warning(f"⚠️ Cuota de {model_name} agotada. Reintentando...")
                        if attempt == max_retries - 1:
                            cls._exhausted_until[model_name] = now + 600
                        await asyncio.sleep(2**attempt)
                    else:
                        logger.error(f"❌ Error en {model_name}: {e}")
        return None

    @classmethod
    async def _call_perplexity(
        cls,
        prompt: str,
        system_instruction: str | None = None,
        max_retries: int = 3,
        json_mode: bool = False,
    ) -> str | None:
        """Llamada a Perplexity API (compatible con OpenAI)."""
        key = config.PERPLEXITY_API_KEY
        if not key:
            logger.error("❌ Perplexity API Key no configurada en el .env")
            return None

        import aiohttp

        url = "https://api.perplexity.ai/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

        # Perplexity models: sonar, sonar-reasoning, etc. Default to sonar
        payload = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": system_instruction or "Eres un bibliotecario experto."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"} if json_mode else None,
        }

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload, timeout=60) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            content = data["choices"][0]["message"]["content"]
                            logger.info("🧠 [perplexity/sonar] Success")
                            return content
                        elif resp.status == 429:
                            logger.warning("⚠️ Perplexity Quota reached. Retrying...")
                        else:
                            error_text = await resp.text()
                            logger.error(f"❌ Perplexity Error {resp.status}: {error_text}")
            except Exception as e:
                logger.error(f"❌ Exception in _call_perplexity: {e}")

            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)

        return None

    @staticmethod
    async def normalize_book_metadata(filename: str, raw_meta: dict[str, Any]) -> dict[str, Any] | None:
        """
        Analiza un libro y devuelve metadatos normalizados, priorizando la extracción de volumen desde metadatos internos.
        """
        prompt = f"""
        Actúa como un bibliotecario experto en novelas ligeras y manga. Tu tarea es normalizar los metadatos de un archivo de libro.

        REGLAS DE IDIOMA:
        - Todas las EXPLICACIONES y campos de texto libre deben estar SIEMPRE en ESPAÑOL.
        - **Series (English)**: El nombre de la serie oficial en INGLÉS.
        - **Series (Spanish)**: El nombre oficial o más común en ESPAÑOL.

        Reglas de Extracción:
        1. **Volume (CRÍTICO)**: Extrae el número de volumen con total precisión.
           - Si el archivo no especifica volumen, es un tomo único, o el volumen es 0, pon 0.0.
        2. **Group & Siglas (REGLAS ESTRICTAS)**:
           - **IMPORTANTE**: Usa el campo 'publisher' de los metadatos para identificar al grupo.
           - Si el 'publisher' coincide con uno de los nombres en la 'LISTA DE GRUPOS' proporcionada, DEBES usar la sigla correspondiente de esa lista.
           - Si no hay coincidencia, sigue estas reglas:
             - Longitud Máxima: Las siglas NO deben superar los 6 caracteres.
             - Unicidad: Cada grupo debe tener una sigla única.
             - Claridad Identificable: Si hay conflicto (mismas siglas), no uses números. Expande la sigla usando letras del nombre para que sea descriptiva (ej. Dark Translations = DARKT, Dragoon Translations = DRAGT).
             - Nombres como Siglas: Si el nombre del grupo tiene una sola palabra de 6 letras o menos (ej. "MiraiK"), la sigla puede ser el mismo nombre.
             - Consistencia: Si el nombre del grupo es casi idéntico (variaciones de espacios o mayúsculas), asígnales la misma sigla.
        3. **Suggested Filename**: Genera el nombre EXACTO: "{{Prefix}}{{Series Spanish}} - {{Volumen}} [{{Siglas}}].epub".
           - **Prefix (CRÍTICO)**:
             - Si el libro tiene "Ilustraciones a Color" en sus géneros: usa `[Color]`.
             - Si el libro tiene "Sin Censura" en sus géneros: usa `[SC]`.
             - Si tiene AMBOS: usa `[Color-SC]`.
             - De lo contrario, no pongas nada delante.
           - Si el volumen es 0.0, usa "Volumen Único" para la parte de {{Volumen}}.
           - Si el volumen es > 0, usa "V{{XX}}" (ej: V01, V08.5).

        SEGURIDAD DE ARCHIVOS:
        - El campo `suggested_filename` NUNCA debe incluir caracteres Prohibidos: \\ / : * ? " < > |
        - Los campos de metadata (`series_english`, `series_spanish`) SÍ pueden incluirlos (ej: "Serie: Subtítulo").

        Datos de Entrada:
        - Filename Original: "{filename}"
        - Metadata Cruda (Contiene 'publisher'): {json.dumps(raw_meta, default=str)}

        REGLAS DE CATEGORIZACIÓN:
        - **Book Type**: Identifica si es "Novela Ligera" (Publicada por editorial), "Novela Web" (Publicada en sitios como Syosetu), "Manga" u otro.
        - **Genres**: Devuelve una lista de etiquetas estándar (ej: Fantasía, Romance, Acción, Isekai, RPG).
        - **Demography**: Identifica Seinen, Shonen, Shoujo, Josei.
        - **Description**: Si la descripción actual es nula o está muy sucia (con código HTML o metadatos técnicos), genera una versión limpia y atractiva de máximo 500 caracteres.

        {{group_context}}

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
            "book_type": "string",
            "genres": ["string"],
            "demographics": ["string"],
            "cleaned_description": "string",
            "confidence": float
        }}
        """

        try:
            # Inject context if possible
            group_context = await AIService._get_group_context()
            full_prompt = prompt.replace("{group_context}", group_context)

            # Ejecutar con reintentos y fallback automático
            response_text = await AIService._call_ai(full_prompt, json_mode=True)
            if not response_text:
                return None
            txt = AIService._extract_json_from_text(response_text)
            data = json.loads(txt)
            if data.get("suggested_filename"):
                data["suggested_filename"] = AIService.sanitize_filename(data["suggested_filename"])
            return data
        except Exception as e:
            logger.error(f"Error en normalize_book_metadata: {e}")
            return None

    @staticmethod
    async def suggest_series_rename(current_name: str) -> str:
        """Sugiere un nombre de serie limpio/estándar."""
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
            response_text = await AIService._call_ai(prompt, json_mode=True)
            if not response_text:
                return {
                    "proposed_english": current_name,
                    "proposed_spanish": current_name,
                }
            txt = AIService._extract_json_from_text(response_text)
            return json.loads(txt)
        except Exception:
            return {"proposed_english": current_name, "proposed_spanish": current_name}

    @staticmethod
    async def analyze_series_for_updates(
        series_hash: str,
        current_series_name: str,
        books: list[dict[str, Any]],
        current_spanish_name: str = None,
        target_model: str | None = None,
    ) -> dict[str, Any]:
        """
        Analiza un grupo de libros y propone estandarización.
        Retorna un objeto 'proposal' con los cambios sugeridos.
        """
        # 1. Preparar contexto para la IA
        # Preferimos mostrar el filename o el nombre en español para que la IA entienda el estado actual
        prompt = f"""
        Actúa como un bibliotecario experto. Analiza este grupo de libros y propón una estandarización coherente.

        REGLAS DE IDIOMA:
        - El campo 'reason' (explicación) debe estar SIEMPRE en ESPAÑOL.

        Nombre Actual en DB (English): "{current_series_name}"
        Nombre Actual en DB (Spanish): "{current_spanish_name or "No establecido"}"

        Datos de libros (filename y publisher): {json.dumps([{"f": b.get("filename"), "p": b.get("publisher")} for b in books[:15]], indent=2)}

        Tareas:
        1. **Proposed English Name**: El nombre canónico en INGLÉS/ROMAJI.
        2. **Proposed Spanish Name**: El nombre oficial en ESPAÑOL.
        3. **Proposed Slug**: Un identificador único para la URL. Debe ser 'series_name' en minúsculas con guiones bajos, sin caracteres especiales ni tildes. Ej: 'the_pet_girl_of_sakurasou'.
        4. **Group Siglas & Name (PROPRIEDAD CRÍTICA)**:
           - **IMPORTANTE**: Usa el campo 'publisher' de cada libro para identificar al grupo.
           - Si el 'publisher' coincide con uno de los nombres en la 'LISTA DE GRUPOS' proporcionada, DEBES usar la sigla correspondiente de esa lista.
           - Si no hay coincidencia, sigue estas reglas:
             - **Group Full Name**: El nombre completo descriptivo del grupo.
             - **Group Siglas**: Siglas de <= 6 caracteres. No uses números si hay conflicto. Expande usando letras descriptivas del nombre (ej: 'DARKT', 'DRAGT').
             - Nombres como Siglas: Si es una palabra de <= 6 letras, úsala tal cual.
             - Consistencia: Nombres casi idénticos = misma sigla.
        5. **Volumes**: Para cada archivo, confirma su volumen real. Usa 0.0 si es Volumen Único.

        SEGURIDAD DE ARCHIVOS:
        - La restricción de caracteres (\\ / : * ? " < > |) SOLO aplica a nombres de archivo en disco.
        - Los campos `proposed_english`, `proposed_spanish` y `proposed_slug` PUEDEN contener ":" (ej: "Serie: Subtitulo").

        Responde SOLO con este JSON:
        {{
            "proposed_english": "string",
            "proposed_spanish": "string",
            "proposed_slug": "string",
            "group_full": "string",
            "group_siglas": "string",
            "detected_tags": ["tag1", "tag2"],
            "is_uncensored_series": boolean,
            "confidence": float,
            "reason": "string",
            "volumes": {{
                "filename_original": {{
                    "volume": float,
                    "siglas": "string"
                }}
            }}
        }}

        NOTA: Si detectas que los libros de la serie han sido traducidos por diferentes grupos, especifica la 'sigla' correcta para cada archivo dentro del objeto 'volumes'. Si no estás seguro o todos son iguales, usa el 'group_siglas' general de la serie como fallback.

        {{group_context}}
        """

        # 0. Get Learning Context (RAG-lite) and Current Series Info
        learning_context = ""
        current_s = None
        try:
            from sqlalchemy import text

            from models.library_models import SeriesMetadata
            from utils.library_db import get_session

            with get_session() as session:
                # Get current series metadata for slug context
                current_s = session.query(SeriesMetadata).filter_by(series_hash=series_hash).first()

                # Get valid siglas
                res_siglas = session.execute(
                    text("SELECT siglas FROM translators_groups WHERE siglas IS NOT NULL LIMIT 100")
                )
                valid_siglas = [r[0] for r in res_siglas]

                # Get similar historical corrections
                res_learning = session.execute(
                    text("SELECT proposed_name, final_name FROM ai_learning_feedback WHERE status='edited' LIMIT 5")
                )
                corrections = [f"IA propuso '{r[0]}' pero el usuario corrigió a '{r[1]}'" for r in res_learning]

                if valid_siglas:
                    learning_context += f"\nSIGLAS VÁLIDAS CONOCIDAS (Úsalas si encajan): {', '.join(valid_siglas)}"
                if corrections:
                    learning_context += "\nAPRENDIZAJE DE CORRECCIONES PASADAS:\n" + "\n".join(corrections)
        except Exception as e:
            logger.warning(f"Failed to load learning context or series info: {e}")

        try:
            group_context = await AIService._get_group_context()
            full_prompt = (
                prompt.replace("{group_context}", group_context)
                + f"\n\nCONTEXTO ADICIONAL DE APRENDIZAJE:\n{learning_context}"
            )
            response_text = await AIService._call_ai(full_prompt, json_mode=True, target_model=target_model)
            if not response_text:
                return {"error": "AI failed or quota exceeded"}
            txt = AIService._extract_json_from_text(response_text)
            analysis = json.loads(txt)

            # Construir propuesta detallada
            proposal = {
                "series_hash": series_hash,
                "current_series": current_series_name,
                "current_spanish": current_spanish_name,
                "current_slug": current_s.slug if current_s else None,
                "proposed_series": analysis.get("proposed_english"),
                "proposed_spanish": analysis.get("proposed_spanish"),
                "proposed_slug": analysis.get("proposed_slug"),
                "group_full": analysis.get("group_full", "Unknown"),
                "group_siglas": analysis.get("group_siglas", "Unknown"),
                "reason": analysis.get("reason"),
                "confidence": analysis.get("confidence"),
                "global_tags": analysis.get("detected_tags", []),
                "changes": [],
            }

            # Generar cambios individuales (Renombrado de archivos)
            ai_volumes = analysis.get("volumes", {})

            for book in books:
                orig_name = book.get("filename") or book.get("title", "")

                # Get specific data for this volume from IA response
                vol_info = ai_volumes.get(orig_name)

                # Use IA volume if it's a dict or a plain number (backward compatibility)
                if isinstance(vol_info, dict):
                    current_vol = vol_info.get("volume", book.get("volume", 0))
                    book_siglas = vol_info.get("siglas") or proposal["group_siglas"] or "Unknown"
                else:
                    current_vol = vol_info if vol_info is not None else book.get("volume", 0)
                    book_siglas = proposal["group_siglas"] or "Unknown"

                # Handling volume string
                if current_vol is None or float(current_vol) == 0:
                    vol_part = "Volumen Único"
                else:
                    vol_val = float(current_vol)
                    vol_str = f"{int(vol_val):02d}"
                    if vol_val % 1 != 0:
                        vol_str += f".{str(vol_val).split('.')[1]}"
                    vol_part = f"V{vol_str}"

                # Determinar prefijos por rasgos (Color/SC)
                tags = book.get("tags") or []
                is_color = any("Color" in str(t) for t in tags)
                is_sc = any("Sin Censura" in str(t) or "Uncensored" in str(t) for t in tags) or book.get(
                    "is_uncensored"
                )

                prefix = ""
                if is_color and is_sc:
                    prefix = "[Color-SC]"
                elif is_color:
                    prefix = "[Color]"
                elif is_sc:
                    prefix = "[SC]"

                # Generar nuevo nombre de archivo usando el nombre en ESPAÑOL y las SIGLAS INDIVIDUALES
                spanish_name = proposal["proposed_spanish"] or proposal["proposed_series"]
                raw_filename = f"{prefix}{spanish_name} - {vol_part} [{book_siglas}].epub"
                new_filename = AIService.sanitize_filename(raw_filename)

                if book.get("filename") != new_filename:
                    proposal["changes"].append(
                        {
                            "book_id": book.get("id"),
                            "current_filename": book.get("filename") or book.get("filepath") or book.get("title"),
                            "proposed_filename": new_filename,
                            "volume": current_vol,
                            "siglas": book_siglas,
                        }
                    )

            # Check if there is NO CHANGE at all (Series matches AND no files renamed)
            # IMPORTANT: We compare both English and Spanish names
            names_match = proposal["proposed_series"] == current_series_name and (
                not current_spanish_name or proposal["proposed_spanish"] == current_spanish_name
            )

            if names_match and not proposal["changes"]:
                # Series is already perfect - keep the names as-is, just add a note
                proposal["reason"] = (
                    "✨ El estado actual coincide plenamente con los registros de la base de datos y el título canónico en ambos idiomas. "
                    "No se requieren cambios de nombre ni metadatos."
                )
                # Add a flag to indicate no action needed
                proposal["no_changes_needed"] = True
                proposal["is_perfect_match"] = True
                proposal["confidence"] = 1.0  # Perfect match = 100% confidence
            elif names_match:
                proposal["reason"] = (
                    "✅ Los nombres de la serie ya son correctos, pero algunos archivos pueden beneficiarse de una normalización "
                    "en su formato de nombre (VXX [Grupo])."
                )

            return proposal

        except Exception as e:
            logger.error(f"Error analyzing series: {e}")
            return {"error": str(e)}

    @staticmethod
    async def _get_group_context() -> str:
        """Obtiene el mapeo de grupos y siglas para inyectar en el prompt."""
        context = ""
        try:
            from sqlalchemy import text

            from utils.library_db import get_session

            with get_session() as session:
                res = session.execute(
                    text("SELECT name, siglas FROM translators_groups WHERE siglas IS NOT NULL LIMIT 200")
                )
                mappings = [f"'{r[0]}' -> sigla: '{r[1]}'" for r in res]
                if mappings:
                    context = "\nLISTA DE GRUPOS VÁLIDOS (Nombre -> Sigla):\n" + "\n".join(mappings)
        except Exception as e:
            logger.warning(f"Error fetching group context: {e}")
        return context

    @staticmethod
    async def analyze_potential_merge(series_a: dict, series_b: dict) -> dict | None:
        """
        Analiza dos registros de serie y determina si son la misma obra.
        """
        prompt = f"""
        Actúa como un experto en catalogación. Determina si estas dos entradas corresponden a la misma serie/obra.
        A veces se crean duplicados por pequeñas diferencias en el nombre o autor.

        SERIE A:
        - Nombre: "{series_a.get("series_name")}"
        - Autor: "{series_a.get("author")}"
        - Libros: {series_a.get("book_count")}

        SERIE B:
        - Nombre: "{series_b.get("series_name")}"
        - Autor: "{series_b.get("author")}"
        - Libros: {series_b.get("book_count")}

        REGLAS:
        1. Responde solo si la probabilidad de que sean la misma es > 85%.
        2. Si son la misma, indica cuál nombre es el más "limpio" o correcto para consolidar.
        3. Explica BREVEMENTE en ESPAÑOL por qué crees que son la misma (ej: "Diferencia solo en el signo de exclamación al final").

        Responde SOLO con un JSON (o nulo si no estás seguro):
        {{
            "is_same": boolean,
            "confidence": float,
            "reason": "string",
            "suggested_main_name": "string",
            "verify_details": ["dato1", "dato2"]
        }}
        """

        try:
            response_text = await AIService._call_ai(prompt, json_mode=True)
            if not response_text:
                return None
            txt = AIService._extract_json_from_text(response_text)
            res = json.loads(txt)
            if res and isinstance(res, dict) and res.get("is_same") and res.get("confidence", 0) > 0.8:
                # Normalizar booleano si llegó como string
                if isinstance(res["is_same"], str):
                    res["is_same"] = res["is_same"].lower() == "true"
                return res
            return None
        except Exception as e:
            logger.error(f"Error detectando merge: {e}")
            return None

    @staticmethod
    async def log_feedback(
        series_hash: str,
        original: str,
        proposed: str,
        final: str,
        proposed_spanish: str = None,
        final_spanish: str = None,
        status: str = "accepted",
        ai_reason: str = None,
    ):
        """Guarda retroalimentación para el aprendizaje de la IA."""
        try:
            from sqlalchemy import text

            from config.config_settings import config
            from utils.library_db import get_session

            with get_session() as session:
                query = text("""
                    INSERT INTO ai_learning_feedback (series_hash, original_name, proposed_name, final_name, proposed_spanish, final_spanish, status, ai_reason)
                    VALUES (:h, :o, :p, :f, :ps, :fs, :s, :r)
                """)
                params = {
                    "h": series_hash,
                    "o": original or "Unknown",
                    "p": proposed or final or original or "Unknown",
                    "f": final or proposed or original or "Unknown",
                    "ps": proposed_spanish,
                    "fs": final_spanish,
                    "s": status,
                    "r": ai_reason,
                }
                session.execute(query, params)
                session.commit()

            # Simple Cloud Push
            if config.ENABLE_SUPABASE:
                try:
                    from core.supabase_manager import supabase_manager

                    client = supabase_manager.get_client()
                    # Supabase needs full column names, not abbreviated params
                    supabase_params = {
                        "series_hash": series_hash,
                        "original_name": original or "Unknown",
                        "proposed_name": proposed or final or original or "Unknown",
                        "final_name": final or proposed or original or "Unknown",
                        "proposed_spanish": proposed_spanish,
                        "final_spanish": final_spanish,
                        "status": status,
                        "ai_reason": ai_reason,
                    }
                    client.table("ai_learning_feedback").insert(supabase_params).execute()
                except Exception as cloud_e:
                    logger.warning(f"Failed to push feedback to cloud: {cloud_e}")

        except Exception as e:
            logger.error(f"Error logging AI feedback: {e}")

    @staticmethod
    async def generate_synopsis(title: str, description: str) -> str | None:
        """Genera una sinopsis corta y atractiva para el libro."""
        prompt = f"""
        Actúa como un redactor creativo de una editorial de novelas ligeras. Tu tarea es escribir una sinopsis corta y atractiva para el siguiente libro.

        Título: "{title}"
        Descripción Original: "{description[:2000] if description else "Sin descripción"}"

        Reglas:
        1. Idioma: Español.
        2. Longitud: Máximo 300 caracteres.
        3. Tono: Intrigante y emocionante.
        4. Evita: Spoilers innecesarios y listas de capítulos. Solo el núcleo de la trama.
        5. Formato: Solo el texto de la sinopsis, sin comillas ni intros.
        """

        try:
            # Use automatic fallback for synopsis too
            response_text = await AIService._call_ai(prompt)
            if not response_text:
                return None
            return response_text.strip()
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

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Elimina caracteres prohibidos para sistemas de archivos (\\ / : * ? " < > |)."""
        if not name:
            return ""
        import re

        # Reemplazar caracteres prohibidos por guiones
        forbidden = r'[\\/:*?"<>|]'
        clean = re.sub(forbidden, "-", name)
        # Limpiar espacios extra y puntos al final (prohibidos en Windows)
        return clean.strip().strip(".")
