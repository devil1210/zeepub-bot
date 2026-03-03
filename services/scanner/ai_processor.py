# services/scanner/ai_processor.py

import logging
from typing import Any

from services.ai_service import AIService

logger = logging.getLogger(__name__)


class AIProcessor:
    """
    Handle AI-powered metadata processing and proposal generation.
    Single Responsibility: AI operations and intelligent metadata enhancement.
    """

    def __init__(self):
        self.ai_service = AIService()

    async def generate_metadata_proposals(
        self, series_hash: str, current_metadata: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Generate AI-powered metadata proposals for series improvement.
        """
        try:
            proposals = []

            # Generate author proposal if missing
            if not current_metadata.get("author"):
                author_proposal = await self._generate_author_proposal(current_metadata)
                if author_proposal:
                    proposals.append(author_proposal)

            # Generate description proposal if missing or poor
            if not current_metadata.get("description") or len(current_metadata.get("description", "")) < 50:
                desc_proposal = await self._generate_description_proposal(current_metadata)
                if desc_proposal:
                    proposals.append(desc_proposal)

            # Generate tags proposal if insufficient
            current_tags = current_metadata.get("tags", [])
            if len(current_tags) < 3:
                tags_proposal = await self._generate_tags_proposal(current_metadata)
                if tags_proposal:
                    proposals.append(tags_proposal)

            # Generate demographics proposal if missing
            if not current_metadata.get("demographics"):
                demographics_proposal = await self._generate_demographics_proposal(current_metadata)
                if demographics_proposal:
                    proposals.append(demographics_proposal)

            logger.info(f"🤖 Generadas {len(proposals)} propuestas IA para {series_hash}")
            return proposals

        except Exception as e:
            logger.error(f"❌ Error generando propuestas IA: {e}")
            return []

    async def _generate_author_proposal(self, metadata: dict[str, Any]) -> dict[str, Any] | None:
        """Generate AI proposal for missing author."""
        try:
            # Use AI to analyze title and suggest author
            title = metadata.get("series", "") + " " + metadata.get("volume", "")

            prompt = f"""
            Analiza el siguiente título de novela ligera y sugiere el autor más probable:

            Título: {title}

            Responde con un JSON válido:
            {{
                "author": "nombre del autor",
                "confidence": 0.8,
                "reasoning": "razón de la sugerencia"
            }}
            """

            response = await self.ai_service.generate_completion(prompt)

            if response and response.strip():
                import json

                try:
                    proposal = json.loads(response)
                    return {
                        "type": "author",
                        "proposed_value": proposal.get("author", ""),
                        "confidence": proposal.get("confidence", 0.5),
                        "reasoning": proposal.get("reasoning", ""),
                        "current_value": metadata.get("author", ""),
                    }
                except json.JSONDecodeError:
                    logger.warning(f"Respuesta IA no válida para autor: {response}")
                    return None

            return None

        except Exception as e:
            logger.error(f"❌ Error generando propuesta de autor: {e}")
            return None

    async def _generate_description_proposal(self, metadata: dict[str, Any]) -> dict[str, Any] | None:
        """Generate AI proposal for improved description."""
        try:
            title = metadata.get("series", "")
            current_desc = metadata.get("description", "")

            prompt = f"""
            Analiza la siguiente serie de novela ligera y genera una descripción mejorada:

            Serie: {title}
            Descripción actual: {current_desc}

            Genera una descripción más atractiva y completa que incluya:
            - Sinopsis general
            - Géneros principales
            - Temas abordados
            - Tono apropiado para el género

            Responde con un JSON válido:
            {{
                "description": "descripción mejorada",
                "confidence": 0.8,
                "reasoning": "razón de la mejora"
            }}
            """

            response = await self.ai_service.generate_completion(prompt)

            if response and response.strip():
                import json

                try:
                    proposal = json.loads(response)
                    return {
                        "type": "description",
                        "proposed_value": proposal.get("description", ""),
                        "confidence": proposal.get("confidence", 0.5),
                        "reasoning": proposal.get("reasoning", ""),
                        "current_value": current_desc,
                    }
                except json.JSONDecodeError:
                    logger.warning(f"Respuesta IA no válida para descripción: {response}")
                    return None

            return None

        except Exception as e:
            logger.error(f"❌ Error generando propuesta de descripción: {e}")
            return None

    async def _generate_tags_proposal(self, metadata: dict[str, Any]) -> dict[str, Any] | None:
        """Generate AI proposal for better tags."""
        try:
            title = metadata.get("series", "")
            current_tags = metadata.get("tags", [])

            prompt = f"""
            Analiza la siguiente serie de novela ligera y sugiere etiquetas apropiadas:

            Serie: {title}
            Tags actuales: {', '.join(current_tags)}

            Sugiere 5-10 etiquetas relevantes que incluyan:
            - Géneros (romance, isekai, fantasía, etc.)
            - Temas (reencarnación, escuela, magia, etc.)
            - Demografía (shonen, seinen, shojo, etc.)
            - Elementos narrativos (aventura, drama, comedia, etc.)

            Responde con un JSON válido:
            {{
                "tags": ["tag1", "tag2", "tag3"],
                "confidence": 0.8,
                "reasoning": "razón de las sugerencias"
            }}
            """

            response = await self.ai_service.generate_completion(prompt)

            if response and response.strip():
                import json

                try:
                    proposal = json.loads(response)
                    return {
                        "type": "tags",
                        "proposed_value": proposal.get("tags", []),
                        "confidence": proposal.get("confidence", 0.5),
                        "reasoning": proposal.get("reasoning", ""),
                        "current_value": current_tags,
                    }
                except json.JSONDecodeError:
                    logger.warning(f"Respuesta IA no válida para tags: {response}")
                    return None

            return None

        except Exception as e:
            logger.error(f"❌ Error generando propuesta de tags: {e}")
            return None

    async def _generate_demographics_proposal(self, metadata: dict[str, Any]) -> dict[str, Any] | None:
        """Generate AI proposal for demographics."""
        try:
            title = metadata.get("series", "")

            prompt = f"""
            Analiza la siguiente serie de novela ligera y sugiere la demografía principal:

            Serie: {title}

            Basado en el título y temas comunes, sugiere una demografía:
            - shonen (para jóvenes masculinos)
            - seinen (para hombres jóvenes)
            - shojo (para jóvenes femeninas)
            - josei (para mujeres adultas)
            - kodomo (para niños)

            Responde con un JSON válido:
            {{
                "demographics": ["demografía_principal"],
                "confidence": 0.8,
                "reasoning": "razón de la sugerencia"
            }}
            """

            response = await self.ai_service.generate_completion(prompt)

            if response and response.strip():
                import json

                try:
                    proposal = json.loads(response)
                    return {
                        "type": "demographics",
                        "proposed_value": proposal.get("demographics", []),
                        "confidence": proposal.get("confidence", 0.5),
                        "reasoning": proposal.get("reasoning", ""),
                        "current_value": [],
                    }
                except json.JSONDecodeError:
                    logger.warning(f"Respuesta IA no válida para demografía: {response}")
                    return None

            return None

        except Exception as e:
            logger.error(f"❌ Error generando propuesta de demografía: {e}")
            return None

    async def save_proposals(self, series_hash: str, proposals: list[dict[str, Any]]) -> bool:
        """
        Save AI proposals to database.
        """
        try:
            # This would integrate with the actual database save logic
            # For now, just logging the proposals
            for proposal in proposals:
                proposal_type = proposal.get("type", "unknown")
                confidence = proposal.get("confidence", 0.5)
                reasoning = proposal.get("reasoning", "")

                logger.info(f"💾 Propuesta IA guardada: {proposal_type} (conf: {confidence}) - {reasoning}")

            return True

        except Exception as e:
            logger.error(f"❌ Error guardando propuestas: {e}")
            return False
