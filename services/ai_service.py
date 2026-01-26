
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

        REGLAS DE IDIOMA:
        - Todas las EXPLICACIONES y campos de texto libre deben estar SIEMPRE en ESPAÑOL.
        - **Series (English)**: El nombre de la serie oficial en INGLÉS.
        - **Series (Spanish)**: El nombre oficial o más común en ESPAÑOL.

        Reglas de Extracción:
        1. **Volume (CRÍTICO)**: Extrae el número de volumen con total precisión.
           - Si el archivo no especifica volumen, es un tomo único, o el volumen es 0, pon 0.0.
        2. **Group & Siglas**: Identifica el grupo y su sigla (ej. [GET]).
        3. **Suggested Filename**: Genera el nombre EXACTO: "{{Prefix}}{{Series Spanish}} - {{Volumen}} [{{Siglas}}].epub".
           - **Prefix (CRÍTICO)**:
             - Si el libro tiene "Ilustraciones a Color" en sus géneros: usa `[Color]`.
             - Si el libro tiene "Sin Censura" en sus géneros: usa `[SC]`.
             - Si tiene AMBOS: usa `[Color-SC]`.
             - De lo contrario, no pongas nada delante.
           - Si el volumen es 0.0, usa "Volumen Único" para la parte de {{Volumen}}.
           - Si el volumen es > 0, usa "V{{XX}}" (ej: V01, V08.5).
        
        SEGURIDAD DE ARCHIVOS:
        - El campo `suggested_filename` NUNCA debe incluir caracteres Prohibidos: \ / : * ? " < > |
        - Los campos de metadata (`series_english`, `series_spanish`) SÍ pueden incluirlos (ej: "Serie: Subtítulo").

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
            data = json.loads(txt)
            if data.get("suggested_filename"):
                data["suggested_filename"] = AIService.sanitize_filename(data["suggested_filename"])
            return data
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
        
        REGLAS DE IDIOMA:
        - El campo 'reason' (explicación) debe estar SIEMPRE en ESPAÑOL.
        
        Nombre Actual en DB: "{current_series_name}"
        Archivos de muestra: {json.dumps(sample_titles, indent=2)}
        
        Tareas:
        1. **Proposed English Name**: El nombre canónico en INGLÉS/ROMAJI.
        2. **Proposed Spanish Name**: El nombre oficial en ESPAÑOL.
        3. **Group Siglas**: Identifica la sigla del grupo (ej: 'GET', 'Tdx').
        4. **Volumes**: Para cada archivo, confirma su volumen real. Usa 0.0 si es Volumen Único.
        
        SEGURIDAD DE ARCHIVOS:
        - La restricción de caracteres (\ / : * ? " < > |) SOLO aplica a nombres de archivo en disco.
        - Los campos `proposed_english` y `proposed_spanish` PUEDEN contener ":" (ej: "Serie: Subtitulo").
        
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
        
        # 0. Get Learning Context (RAG-lite)
        learning_context = ""
        try:
            from sqlalchemy import text
            from utils.library_db import get_session
            with get_session() as session:
                # Get valid siglas
                res_siglas = session.execute(text("SELECT siglas FROM translators_groups WHERE siglas IS NOT NULL LIMIT 100"))
                valid_siglas = [r[0] for r in res_siglas]
                
                # Get similar historical corrections
                res_learning = session.execute(
                    text("SELECT proposed_name, final_name FROM ai_learning_feedback WHERE status='edited' LIMIT 5")
                )
                corrections = [f"IA propuso '{r[0]}' pero el usuario corrigió a '{r[1]}'" for r in res_learning]
                
                if valid_siglas:
                    learning_context += f"\nSIGLAS VÁLIDAS CONOCIDAS (Úsalas si encajan): {', '.join(valid_siglas)}"
                if corrections:
                    learning_context += f"\nAPRENDIZAJE DE CORRECCIONES PASADAS:\n" + "\n".join(corrections)
        except Exception as e:
            logger.warning(f"Failed to load learning context: {e}")

        try:
            full_prompt = prompt + f"\n\nCONTEXTO ADICIONAL DE APRENDIZAJE:\n{learning_context}"
            response = await model.generate_content_async(full_prompt)
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
                
                # Handling volume string
                if not current_vol or float(current_vol) == 0:
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
                is_sc = any("Sin Censura" in str(t) or "Uncensored" in str(t) for t in tags) or book.get("is_uncensored")
                
                prefix = ""
                if is_color and is_sc: prefix = "[Color-SC]"
                elif is_color: prefix = "[Color]"
                elif is_sc: prefix = "[SC]"
                
                # Generar nuevo nombre de archivo usando el nombre en ESPAÑOL y las SIGLAS
                spanish_name = proposal["proposed_spanish"] or proposal["proposed_series"]
                siglas = proposal["group_siglas"] or "Unknown"
                raw_filename = f"{prefix}{spanish_name} - {vol_part} [{siglas}].epub"
                new_filename = AIService.sanitize_filename(raw_filename)
                
                if book.get("filename") != new_filename:
                    proposal["changes"].append({
                        "book_id": book.get("id"),
                        "current_filename": book.get("filename") or book.get("filepath") or book.get("title"),
                        "proposed_filename": new_filename,
                        "volume": current_vol
                    })

            # Check if there is NO CHANGE at all (Series matches AND no files renamed)
            if proposal["proposed_series"] == current_series_name and not proposal["changes"]:
                # If proposed is identical to current and no changes, mark as 'sin propuesta'
                proposal["proposed_series"] = "sin propuesta"
                proposal["proposed_spanish"] = "sin propuesta"
                if not proposal["reason"]:
                    proposal["reason"] = "El estado actual coincide perfectamente con la estandarización sugerida."
            
            return proposal
            
            return proposal
            
        except Exception as e:
            logger.error(f"Error analyzing series: {e}")
            return {"error": str(e)}

    @staticmethod
    async def analyze_potential_merge(series_a: dict, series_b: dict) -> dict | None:
        """
        Analiza dos registros de serie y determina si son la misma obra.
        """
        model = AIService._get_model()
        if not model:
            return None

        prompt = f"""
        Actúa como un experto en catalogación. Determina si estas dos entradas corresponden a la misma serie/obra.
        A veces se crean duplicados por pequeñas diferencias en el nombre o autor.

        SERIE A:
        - Nombre: "{series_a.get('series_name')}"
        - Autor: "{series_a.get('author')}"
        - Libros: {series_a.get('book_count')}

        SERIE B:
        - Nombre: "{series_b.get('series_name')}"
        - Autor: "{series_b.get('author')}"
        - Libros: {series_b.get('book_count')}

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
            response = await model.generate_content_async(prompt)
            txt = AIService._extract_json_from_text(response.text)
            res = json.loads(txt)
            if res.get("is_same") and res.get("confidence", 0) > 0.85:
                # Normalizar booleano si llegó como string
                if isinstance(res["is_same"], str):
                    res["is_same"] = res["is_same"].lower() == "true"
                return res
            return None
        except Exception as e:
            logger.error(f"Error detectando merge: {e}")
            return None

    @staticmethod
    async def log_feedback(series_hash: str, original: str, proposed: str, final: str, status: str, ai_reason: str = None):
        """Guarda retroalimentación para el aprendizaje de la IA."""
        try:
            from sqlalchemy import text
            from utils.library_db import get_session
            with get_session() as session:
                query = text("""
                    INSERT INTO ai_learning_feedback (series_hash, original_name, proposed_name, final_name, status, ai_reason)
                    VALUES (:h, :o, :p, :f, :s, :r)
                """)
                session.execute(query, {
                    "h": series_hash, "o": original, "p": proposed, "f": final, "s": status, "r": ai_reason
                })
                session.commit()
        except Exception as e:
            logger.error(f"Error logging AI feedback: {e}")

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

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Elimina caracteres prohibidos para sistemas de archivos (\ / : * ? " < > |)."""
        if not name:
            return ""
        import re
        # Reemplazar caracteres prohibidos por guiones
        forbidden = r'[\\/:*?"<>|]'
        clean = re.sub(forbidden, "-", name)
        # Limpiar espacios extra y puntos al final (prohibidos en Windows)
        return clean.strip().strip('.')
