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
        
        # Verificar si hay un archivo EPUB reciente en el contexto
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "❌ **Uso incorrecto**\n\n"
                "Este comando debe usarse como respuesta a un mensaje con un archivo EPUB.\n\n"
                "📋 **Flujo correcto:**\n"
                "1. Sube un archivo EPUB\n"
                "2. Responde a ese mensaje con `/upload_epub`\n"
                "3. El bot procesará el archivo"
            )
            return
        
        # Verificar si el mensaje replied tiene un documento EPUB
        replied_message = update.message.reply_to_message
        if not (replied_message.document and replied_message.document.file_name.lower().endswith('.epub')):
            await update.message.reply_text(
                "❌ **Archivo no válido**\n\n"
                "El mensaje al que respondes debe contener un archivo EPUB (.epub).\n\n"
                "Por favor, sube un archivo EPUB y responde a ese mensaje con `/upload_epub`."
            )
            return
        
        # Procesar el archivo EPUB directamente
        await self.process_epub_from_reply(update, context, replied_message.document)
    
    async def process_epub_from_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file):
        """Procesa el EPUB desde un mensaje reply."""
        user_id = update.effective_user.id
        
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
            from config.config_settings import config
            return user_id in config.ADMIN_USERS
        except:
            return False

# Instancia global
epub_uploader = EPUBUploader()

# Handlers
async def upload_epub_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /upload_epub"""
    await epub_uploader.start_upload(update, context)

async def handle_upload_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja callbacks de upload."""
    await epub_uploader.handle_approval_callback(update, context)

def setup_upload_handlers(application):
    """Configura los handlers para upload de EPUBs."""
    application.add_handler(CommandHandler("upload_epub", upload_epub_command))
    application.add_handler(CallbackQueryHandler(handle_upload_callback, pattern=r"^(approve|reject|edit_path)_epub_"))
