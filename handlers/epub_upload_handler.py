"""
Comando para subir EPUBs a la librería con validación admin
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from config.config_settings import config
from utils.library_db import get_session
from models.library_models import LocalBook
from services.epub_service import parse_opf_from_epub, enrich_metadata_from_epub

logger = logging.getLogger(__name__)

# Estado temporal para uploads en proceso
pending_uploads = {}

class EPUBUploader:
    """Maneja el proceso de upload de EPUBs con validación admin."""
    
    def __init__(self):
        self.temp_dir = Path("/tmp/epub_uploads")
        self.temp_dir.mkdir(exist_ok=True)
    
    async def start_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia el proceso de upload."""
        user_id = update.effective_user.id
        
        # Verificar si es admin
        if not await self.is_admin(user_id):
            await update.message.reply_text("❌ Solo admins pueden usar este comando.")
            return
        
        await update.message.reply_text(
            "📚 **Upload de EPUB**\n\n"
            "Por favor, envíame el archivo EPUB que quieres subir a la librería.\n\n"
            "📋 **Proceso:**\n"
            "1. Envías el EPUB\n"
            "2. Analizo el content.opf\n"
            "3. Muestro vista previa para validación\n"
            "4. Admin aprueba/rechaza\n"
            "5. Se agrega a la librería\n\n"
            "📎 **Envía el archivo EPUB ahora:**"
        )
        
        # Marcar que estamos esperando un archivo
        context.user_data['awaiting_epub'] = True
    
    async def handle_epub_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa el archivo EPUB recibido."""
        user_id = update.effective_user.id
        
        # Verificar si es admin y está esperando archivo
        if not await self.is_admin(user_id) or not context.user_data.get('awaiting_epub'):
            return
        
        # Obtener el archivo
        file = update.message.document
        if not file or not file.file_name.lower().endswith('.epub'):
            await update.message.reply_text("❌ Por favor, envía un archivo EPUB válido.")
            return
        
        await update.message.reply_text("📥 Descargando y analizando EPUB...")
        
        try:
            # Descargar archivo a temporal
            file_path = await self.download_epub(file, context)
            
            # Analizar EPUB y extraer metadata
            metadata = await self.analyze_epub(file_path)
            
            if not metadata:
                await update.message.reply_text("❌ No se pudo leer el content.opf del EPUB.")
                return
            
            # Guardar información para validación
            upload_id = f"upload_{user_id}_{datetime.now().timestamp()}"
            pending_uploads[upload_id] = {
                'file_path': str(file_path),
                'metadata': metadata,
                'user_id': user_id,
                'original_filename': file.file_name
            }
            
            # Enviar vista previa para validación
            await self.send_preview_for_approval(update, upload_id, metadata, file.file_name)
            
            # Limpiar estado
            context.user_data['awaiting_epub'] = False
            
        except Exception as e:
            logger.error(f"Error processing EPUB: {e}")
            await update.message.reply_text(f"❌ Error procesando el EPUB: {str(e)}")
    
    async def download_epub(self, file, context: ContextTypes.DEFAULT_TYPE) -> Path:
        """Descarga el archivo EPUB."""
        temp_file = self.temp_dir / f"{file.file_name}_{datetime.now().timestamp()}.epub"
        
        # Descargar archivo
        new_file = await context.bot.get_file(file.file_id)
        await new_file.download_to_drive(temp_file)
        
        return temp_file
    
    async def analyze_epub(self, epub_path: Path) -> Optional[Dict[str, Any]]:
        """Analiza el EPUB usando el servicio existente del bot."""
        try:
            logger.info(f"Analyzing EPUB with existing service: {epub_path}")
            
            # Usar el servicio existente para extraer metadata del OPF
            opf_metadata = await parse_opf_from_epub(str(epub_path))
            
            if not opf_metadata:
                logger.error("Could not extract OPF metadata from EPUB")
                return None
            
            # Enriquecer metadata usando el servicio existente
            enriched_metadata = await enrich_metadata_from_epub(
                epub_bytes=str(epub_path),
                epub_url=f"file://{epub_path}",
                existing_meta={}
            )
            
            if not enriched_metadata:
                logger.error("Could not enrich EPUB metadata")
                return None
            
            # Convertir al formato esperado por el handler
            metadata = {
                'title': enriched_metadata.get('titulo_volumen') or enriched_metadata.get('titulo_serie') or 'Sin título',
                'author': enriched_metadata.get('autor') or enriched_metadata.get('autores', ['Autor desconocido'])[0] if enriched_metadata.get('autores') else 'Autor desconocido',
                'description': enriched_metadata.get('sinopsis', ''),
                'language': enriched_metadata.get('idioma', 'es'),
                'isbn': enriched_metadata.get('isbn', ''),
                'publisher': enriched_metadata.get('publisher', ''),
                'publish_date': enriched_metadata.get('fecha_publicacion', ''),
                'tags': ', '.join(enriched_metadata.get('generos', [])),
                'series': enriched_metadata.get('titulo_serie', ''),
                'volume': enriched_metadata.get('volumen', ''),
                'illustrator': enriched_metadata.get('ilustrador', ''),
                'translator': enriched_metadata.get('traductor', ''),
                'category': enriched_metadata.get('categoria', ''),
                'demography': enriched_metadata.get('demografia', []),
                'typesetters': enriched_metadata.get('maquetadores', []),
                'original_metadata': enriched_metadata  # Guardar metadata original para referencia
            }
            
            # Generar ruta basada en el formato existente de la biblioteca
            metadata['suggested_path'] = self.generate_path(metadata)
            
            logger.info(f"Successfully extracted metadata: title='{metadata.get('title')}', author='{metadata.get('author')}'")
            return metadata
            
        except Exception as e:
            logger.error(f"Error analyzing EPUB with existing service: {e}")
            return None
    
    def generate_path(self, metadata: Dict[str, Any]) -> str:
        """Genera ruta sugerida basada en metadata y formato existente de la biblioteca."""
        author = metadata.get('author', 'Autor desconocido')
        title = metadata.get('title', 'Sin título')
        language = metadata.get('language', 'es')
        
        # Limpiar y normalizar nombres
        author_clean = self.clean_filename(author)
        title_clean = self.clean_filename(title)
        
        # Estrategias de ruta basadas en formatos comunes de bibliotecas
        strategies = [
            # Estrategia 1: Autor/Titulo (formato más común)
            f"{author_clean}/{title_clean}.epub",
            
            # Estrategia 2: Autor/Titulo (idioma) si no es español
            f"{author_clean}/{title_clean} ({language}).epub" if language != 'es' else None,
            
            # Estrategia 3: Categoría por idioma/Autor/Titulo
            f"books_{language}/{author_clean}/{title_clean}.epub",
            
            # Estrategia 4: Directo si el autor es muy largo
            f"{title_clean}.epub" if len(author_clean) > 50 else None,
            
            # Estrategia 5: Autor (apellido)/Titulo
            f"{author_clean.split()[-1]}/{title_clean}.epub" if ' ' in author_clean else None,
            
            # Estrategia 6: Iniciales del autor/Titulo
            f"{''.join([word[0] for word in author_clean.split()[:2]])}/{title_clean}.epub" if len(author_clean.split()) > 1 else None,
        ]
        
        # Filtrar estrategias válidas y devolver la primera
        for strategy in strategies:
            if strategy and len(strategy) < 200:  # Evitar rutas muy largas
                return strategy
        
        # Fallback: formato simple
        return f"{author_clean}/{title_clean}.epub"
    
    def clean_filename(self, filename: str) -> str:
        """Limpia filename para uso en sistema de archivos."""
        # Caracteres no permitidos
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limitar longitud
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename.strip()
    
    async def send_preview_for_approval(self, update: Update, upload_id: str, metadata: Dict[str, Any], original_filename: str):
        """Envía vista previa para aprobación del admin."""
        
        # Construir vista previa enriquecida
        preview_text = f"""📚 **Vista Previa de EPUB**

📄 **Archivo:** {original_filename}

📋 **Metadata Extraída (Servicio Enriquecido):**
📖 **Título:** {metadata.get('title', 'N/A')}
✍️ **Autor:** {metadata.get('author', 'N/A')}
🏢 **Editorial:** {metadata.get('publisher', 'N/A')}
📅 **Publicado:** {metadata.get('publish_date', 'N/A')}
🌐 **Idioma:** {metadata.get('language', 'N/A')}
🔢 **ISBN:** {metadata.get('isbn', 'N/A')}
🏷️ **Géneros:** {metadata.get('tags', 'N/A')}"""
        
        # Agregar información adicional si está disponible
        if metadata.get('series'):
            preview_text += f"\n📚 **Serie:** {metadata.get('series', 'N/A')}"
        if metadata.get('volume'):
            preview_text += f"\n📖 **Volumen:** {metadata.get('volume', 'N/A')}"
        if metadata.get('illustrator'):
            preview_text += f"\n🎨 **Ilustrador:** {metadata.get('illustrator', 'N/A')}"
        if metadata.get('translator'):
            preview_text += f"\n🔄 **Traductor:** {metadata.get('translator', 'N/A')}"
        if metadata.get('category'):
            preview_text += f"\n📂 **Categoría:** {metadata.get('category', 'N/A')}"
        if metadata.get('demography'):
            preview_text += f"\n👥 **Demografía:** {', '.join(metadata.get('demography', []))}"
        
        preview_text += f"""

📝 **Descripción:**
{metadata.get('description', 'Sin descripción')[:400]}{'...' if len(metadata.get('description', '')) > 400 else ''}

📁 **Ruta Sugerida:**
`{metadata.get('suggested_path', 'N/A')}`

⚠️ **¿Aprobar este EPUB para agregar a la librería?**"""
        
        # Botones de acción
        keyboard = [
            [
                InlineKeyboardButton("✅ Aprobar", callback_data=f"approve_epub_{upload_id}"),
                InlineKeyboardButton("❌ Rechazar", callback_data=f"reject_epub_{upload_id}")
            ],
            [
                InlineKeyboardButton("📝 Editar Ruta", callback_data=f"edit_path_{upload_id}")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(preview_text, reply_markup=reply_markup)
    
    async def handle_approval_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja los callbacks de aprobación/rechazo."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        # Verificar si es admin
        if not await self.is_admin(user_id):
            await query.edit_message_text("❌ No tienes permisos para esta acción.")
            return
        
        callback_data = query.data
        upload_id = callback_data.split('_')[-1]
        
        if upload_id not in pending_uploads:
            await query.edit_message_text("❌ Upload no encontrado o expirado.")
            return
        
        upload_info = pending_uploads[upload_id]
        
        if callback_data.startswith('approve_epub'):
            await self.approve_upload(query, upload_id, upload_info)
        elif callback_data.startswith('reject_epub'):
            await self.reject_upload(query, upload_id, upload_info)
        elif callback_data.startswith('edit_path'):
            await self.request_path_edit(query, upload_id, upload_info)
    
    async def approve_upload(self, query, upload_id: str, upload_info: Dict[str, Any]):
        """Aprueba y procesa el upload."""
        try:
            file_path = Path(upload_info['file_path'])
            metadata = upload_info['metadata']
            suggested_path = metadata.get('suggested_path', '')
            
            await query.edit_message_text("✅ **Aprobado**. Procesando upload...")
            
            # Mover archivo a la librería
            success = await self.add_to_library(file_path, suggested_path, metadata)
            
            if success:
                await query.edit_message_text(
                    f"✅ **EPUB agregado exitosamente**\n\n"
                    f"📁 **Ruta:** `{suggested_path}`\n"
                    f"📚 **Título:** {metadata.get('title')}\n"
                    f"✍️ **Autor:** {metadata.get('author')}"
                )
            else:
                await query.edit_message_text("❌ Error agregando el EPUB a la librería.")
            
            # Limpiar
            self.cleanup_upload(upload_id, file_path)
            
        except Exception as e:
            logger.error(f"Error approving upload: {e}")
            await query.edit_message_text(f"❌ Error procesando upload: {str(e)}")
    
    async def reject_upload(self, query, upload_id: str, upload_info: Dict[str, Any]):
        """Rechaza el upload."""
        try:
            file_path = Path(upload_info['file_path'])
            
            await query.edit_message_text("❌ **Upload rechazado**")
            
            # Limpiar archivo temporal
            self.cleanup_upload(upload_id, file_path)
            
        except Exception as e:
            logger.error(f"Error rejecting upload: {e}")
    
    async def request_path_edit(self, query, upload_id: str, upload_info: Dict[str, Any]):
        """Solicita edición de ruta."""
        current_path = upload_info['metadata'].get('suggested_path', '')
        
        await query.edit_message_text(
            f"📝 **Editar Ruta**\n\n"
            f"Ruta actual: `{current_path}`\n\n"
            f"Envía la nueva ruta (formato: Autor/Titulo.epub)\n"
            f"O responde 'cancel' para usar la ruta actual."
        )
        
        # Marcar que estamos esperando edición de ruta
        query.message.chat_data[f'editing_path_{upload_id}'] = True
    
    async def add_to_library(self, epub_path: Path, suggested_path: str, metadata: Dict[str, Any]) -> bool:
        """Agrega el EPUB a la librería usando metadata enriquecida."""
        try:
            # Directorio base de la librería
            library_base = Path("/mnt/books/library")
            
            # Crear ruta completa
            full_path = library_base / suggested_path
            
            # Crear directorio si no existe
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Mover archivo
            import shutil
            shutil.move(str(epub_path), str(full_path))
            
            # Agregar a base de datos con metadata enriquecida
            session = get_session()
            try:
                # Verificar si ya existe
                existing = session.query(LocalBook).filter_by(file_path=str(full_path)).first()
                if existing:
                    # Actualizar metadata existente con datos enriquecidos
                    existing.title = metadata.get('title', existing.title)
                    existing.author = metadata.get('author', existing.author)
                    existing.description = metadata.get('description', existing.description)
                    existing.isbn = metadata.get('isbn', existing.isbn)
                    existing.publisher = metadata.get('publisher', existing.publisher)
                    existing.publish_date = metadata.get('publish_date', existing.publish_date)
                    existing.language = metadata.get('language', existing.language)
                    existing.tags = metadata.get('tags', existing.tags)
                    existing.series = metadata.get('series', existing.series)
                    existing.volume = metadata.get('volume', existing.volume)
                    existing.illustrator = metadata.get('illustrator', existing.illustrator)
                    existing.translator = metadata.get('translator', existing.translator)
                    existing.category = metadata.get('category', existing.category)
                    existing.indexed_at = datetime.utcnow()
                    
                    # Guardar metadata adicional en JSON si existe
                    if metadata.get('original_metadata'):
                        existing.extra_metadata = metadata.get('original_metadata')
                else:
                    # Crear nuevo registro con metadata enriquecida
                    new_book = LocalBook(
                        title=metadata.get('title', ''),
                        author=metadata.get('author', ''),
                        description=metadata.get('description', ''),
                        isbn=metadata.get('isbn', ''),
                        publisher=metadata.get('publisher', ''),
                        publish_date=metadata.get('publish_date', ''),
                        language=metadata.get('language', ''),
                        tags=metadata.get('tags', ''),
                        series=metadata.get('series', ''),
                        volume=metadata.get('volume', ''),
                        illustrator=metadata.get('illustrator', ''),
                        translator=metadata.get('translator', ''),
                        category=metadata.get('category', ''),
                        file_path=str(full_path),
                        file_size=full_path.stat().st_size,
                        indexed_at=datetime.utcnow(),
                        extra_metadata=metadata.get('original_metadata', {})
                    )
                    session.add(new_book)
                
                session.commit()
                return True
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error adding to library: {e}")
            return False
    
    def cleanup_upload(self, upload_id: str, epub_path: Path):
        """Limpia archivos temporales y estado."""
        try:
            # Eliminar archivo temporal si existe
            if epub_path.exists():
                epub_path.unlink()
        except:
            pass
        
        # Eliminar del estado pendiente
        if upload_id in pending_uploads:
            del pending_uploads[upload_id]
    
    async def is_admin(self, user_id: int) -> bool:
        """Verifica si el usuario es admin."""
        try:
            from repositories.user_repository import user_repo
            user_data = await user_repo.get_by_id(user_id)
            return user_data and user_data.get('level') == 'admin'
        except:
            return False

# Instancia global
epub_uploader = EPUBUploader()

# Handlers
async def upload_epub_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /upload_epub"""
    await epub_uploader.start_upload(update, context)

async def handle_epub_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja archivos EPUB recibidos."""
    await epub_uploader.handle_epub_file(update, context)

async def handle_upload_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja callbacks de upload."""
    await epub_uploader.handle_approval_callback(update, context)

def setup_upload_handlers(application):
    """Configura los handlers para upload de EPUBs."""
    application.add_handler(CommandHandler("upload_epub", upload_epub_command))
    application.add_handler(MessageHandler(filters.Document & filters.FileExtension("epub"), handle_epub_file))
    application.add_handler(CallbackQueryHandler(handle_upload_callback, pattern=r"^(approve|reject|edit_path)_epub_"))
