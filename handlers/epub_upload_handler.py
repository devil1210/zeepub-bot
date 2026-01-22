"""
Comando para subir EPUBs a la librería con validación admin
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from config.config_settings import config
from utils.library_db import get_session
from models.library_models import LocalBook
from utils.helpers import generate_book_hash
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
            await update.message.reply_text("❌ Solo admins pueden usar este comando.", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Verificar si hay un archivo EPUB reciente en el contexto
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "❌ **Uso incorrecto**\n\n"
                "Este comando debe usarse como respuesta a un mensaje con un archivo EPUB.\n\n"
                "📋 **Flujo correcto:**\n"
                "1. Sube un archivo EPUB\n"
                "2. Responde a ese mensaje con `/upload_epub`\n"
                "3. El bot procesará el archivo",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Verificar si el mensaje replied tiene un documento EPUB
        replied_message = update.message.reply_to_message
        if not (replied_message.document and replied_message.document.file_name.lower().endswith('.epub')):
            await update.message.reply_text(
                "❌ **Archivo no válido**\n\n"
                "El mensaje al que respondes debe contener un archivo EPUB (.epub).\n\n"
                "Por favor, sube un archivo EPUB y responde a ese mensaje con `/upload_epub`.",
                parse_mode=ParseMode.MARKDOWN
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
            metadata = await self.analyze_epub(file_path, file.file_name)
            
            if not metadata:
                await update.message.reply_text(
                    "❌ **Error analizando el EPUB**\n\n"
                    "No se pudo leer el metadata del archivo. Esto puede deberse a:\n\n"
                    "🔍 **Posibles problemas:**\n"
                    "• El archivo no es un EPUB válido\n"
                    "• El EPUB está corrupto o dañado\n"
                    "• No contiene el archivo content.opf\n"
                    "• Formato EPUB no estándar\n\n"
                    "📋 **Soluciones:**\n"
                    "• Intenta con otro archivo EPUB\n"
                    "• Verifica que el archivo se abra correctamente\n"
                    "• Convierte el archivo a formato EPUB estándar\n\n"
                    "📝 **Nota:** Revisa los logs del sistema para más detalles técnicos.",
                    parse_mode=ParseMode.MARKDOWN
                )
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
            await update.message.reply_text(f"❌ Error procesando el EPUB: {str(e)}", parse_mode=ParseMode.MARKDOWN)
    
    async def download_epub(self, file, context: ContextTypes.DEFAULT_TYPE) -> Path:
        """Descarga el archivo EPUB."""
        temp_file = self.temp_dir / f"{file.file_name}_{datetime.now().timestamp()}.epub"
        
        # Descargar archivo
        new_file = await context.bot.get_file(file.file_id)
        await new_file.download_to_drive(temp_file)
        
        return temp_file
    
    async def analyze_epub(self, epub_path: Path, original_filename: str) -> Optional[Dict[str, Any]]:
        """Analiza el EPUB usando el servicio existente del bot."""
        try:
            logger.info(f"Analyzing EPUB with existing service: {epub_path}")
            
            # Verificar que el archivo existe y no esté vacío
            if not epub_path.exists():
                logger.error(f"EPUB file does not exist: {epub_path}")
                return None
            
            file_size = epub_path.stat().st_size
            if file_size == 0:
                logger.error(f"EPUB file is empty: {epub_path}")
                return None
            
            logger.info(f"EPUB file size: {file_size} bytes")
            
            # Intentar leer el archivo como ZIP para validar estructura
            import zipfile
            try:
                with zipfile.ZipFile(epub_path, 'r') as test_zip:
                    # Listar archivos para diagnóstico
                    file_list = test_zip.namelist()
                    logger.info(f"EPUB contains {len(file_list)} files")
                    
                    # Buscar archivos .opf
                    opf_files = [f for f in file_list if f.lower().endswith('.opf')]
                    logger.info(f"Found OPF files: {opf_files}")
                    
                    # Buscar container.xml
                    container_files = [f for f in file_list if 'container.xml' in f.lower()]
                    logger.info(f"Found container files: {container_files}")
                    
                    if not opf_files and not container_files:
                        logger.error("No OPF or container files found in EPUB")
                        return None
                        
            except zipfile.BadZipFile:
                logger.error(f"EPUB file is not a valid ZIP: {epub_path}")
                return None
            except Exception as e:
                logger.error(f"Error reading EPUB as ZIP: {e}")
                return None
            
            # Usar el servicio existente para extraer metadata del OPF
            opf_metadata = await parse_opf_from_epub(str(epub_path))
            
            if not opf_metadata:
                logger.error("Could not extract OPF metadata from EPUB")
                return None
            
            logger.info(f"OPF metadata extracted: {list(opf_metadata.keys())}")
            
            # Enriquecer metadata usando el servicio existente
            enriched_metadata = await enrich_metadata_from_epub(
                epub_bytes=str(epub_path),
                epub_url=f"file://{epub_path}",
                existing_meta={}
            )
            
            if not enriched_metadata:
                logger.error("Could not enrich EPUB metadata")
                return None
            
            logger.info(f"Enriched metadata keys: {list(enriched_metadata.keys())}")
            
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
                'original_metadata': enriched_metadata,  # Guardar metadata original para referencia
                'original_filename': original_filename  # Agregar el nombre original del archivo
            }
            
            # Generar hash del libro para detección de duplicados
            book_hash = generate_book_hash(
                title=metadata['title'],
                author=metadata['author'],
                series=metadata['series'],
                volume=metadata['volume'],
                book_type=metadata.get('category') or metadata.get('book_type'),
                language=metadata['language'],
                translator=metadata['translator']
            )
            metadata['book_hash'] = book_hash
            
            # 1. Detección de Conflictos (Identidad vs Ruta)
            metadata['identity_match'] = None # Coincidencia por HASH
            metadata['path_match'] = None     # Coincidencia por RUTA (Sobrescritura)
            metadata['existing_data'] = None  # Metadata para comparar
            
            with get_session() as session:
                # Buscar por identidad (Hash)
                existing_hash = session.query(LocalBook).filter(LocalBook.book_hash == book_hash).first()
                if existing_hash:
                    metadata['identity_match'] = {
                        'id': existing_hash.id,
                        'path': existing_hash.filepath,
                    }
                    metadata['existing_data'] = {
                        'title': existing_hash.title,
                        'author': existing_hash.author,
                        'series': existing_hash.series,
                        'volume': str(existing_hash.volume) if existing_hash.volume else '',
                        'translator': existing_hash.translator,
                        'publisher': existing_hash.publisher,
                        'language': existing_hash.language,
                        'isbn': existing_hash.isbn,
                        'tags': existing_hash.tags
                    }
                
                # 2. Generar ruta sugerida
                metadata['suggested_path'] = self.generate_path(metadata)
                
                # 3. Verificar colisión física por ruta
                library_base = Path("/library")
                full_target_path = library_base / metadata['suggested_path']
                metadata['file_exists'] = full_target_path.exists()
                
                # Si el archivo existe físicamente, buscar qué libro es en la BD
                if metadata['file_exists']:
                    existing_path = session.query(LocalBook).filter(LocalBook.filepath == metadata['suggested_path']).first()
                    if existing_path:
                        metadata['path_match'] = {
                            'id': existing_path.id,
                            'path': existing_path.filepath,
                        }
                        # Si no teníamos metadata por hash (o si es otro libro el que estorba en la ruta),
                        # priorizamos mostrar la comparación con el que está en la ruta para prevenir errores
                        if not metadata['identity_match'] or metadata['identity_match']['id'] != metadata['path_match']['id']:
                             metadata['existing_data'] = {
                                'title': existing_path.title,
                                'author': existing_path.author,
                                'series': existing_path.series,
                                'volume': str(existing_path.volume) if existing_path.volume else '',
                                'translator': existing_path.translator,
                                'publisher': existing_path.publisher,
                                'language': existing_path.language,
                                'isbn': existing_path.isbn,
                                'tags': existing_path.tags
                            }
            
            logger.info(f"Successfully extracted metadata: title='{metadata.get('title')}', hash='{book_hash}', identity_match={metadata['identity_match'] is not None}, path_collision={metadata['path_match'] is not None}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error analyzing EPUB with existing service: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    def generate_path(self, metadata: Dict[str, Any]) -> str:
        """Genera ruta sugerida basada en metadata y formato existente de la biblioteca."""
        author = metadata.get('author', 'Autor desconocido')
        title = metadata.get('title', 'Sin título')
        series = metadata.get('series', '')
        language = metadata.get('language', 'es')
        
        # Obtener el nombre original del archivo subido desde los metadatos
        original_filename = metadata.get('original_filename', '')
        if original_filename:
            # Extraer solo el nombre del archivo sin extensión
            filename_without_ext = original_filename.rsplit('.', 1)[0]
            # Limpiar tags existentes como [NL], [NW], [ShinsengumiTL], etc.
            import re
            filename_clean = re.sub(r'\s*\[(?:NL|NW|M\.?\s*Nigthkrelin\s*Subs|ShinsengumiTL)\]\s*', '', filename_without_ext)
        else:
            # Si no hay filename original, usar el título limpio
            filename_clean = self.clean_filename(title)
        
        # Limpiar y normalizar nombres
        author_clean = self.clean_filename(author)
        if series:
            import re
            series_ok = re.sub(r"\s*\[(?:NL|NW)\]\s*$", "", series, flags=re.IGNORECASE)
            series_clean = self.clean_filename(series_ok)
        else:
            series_clean = None
        
        # Determinar el tag basado en el tipo de novela
        tag = self.determine_novel_type_tag(metadata, original_filename)
        
        # Si hay serie, usar el formato: Serie - Autor [Tag]/Filename
        if series_clean:
            # Formato: Serie - Autor [Tag]/Filename
            suggested_path = f"{series_clean} - {author_clean} [{tag}]/{filename_clean}.epub"
        else:
            # Si no hay serie, usar formato: Autor [Tag]/Filename
            suggested_path = f"{author_clean} [{tag}]/{filename_clean}.epub"
        
        # Limitar longitud total de la ruta
        if len(suggested_path) > 250:
            # Si es muy larga, acortar el filename
            if series_clean:
                prefix_len = len(f"{series_clean} - {author_clean} [{tag}]")
            else:
                prefix_len = len(f"{author_clean} [{tag}]")
            
            max_filename_len = 250 - prefix_len - 5  # 5 para ".epub"
            filename_clean = filename_clean[:max_filename_len]
            
            if series_clean:
                suggested_path = f"{series_clean} - {author_clean} [{tag}]/{filename_clean}.epub"
            else:
                suggested_path = f"{author_clean} [{tag}]/{filename_clean}.epub"
        
        return suggested_path
    
    def determine_novel_type_tag(self, metadata: Dict[str, Any], original_filename: str) -> str:
        """Determina si es Novela Ligera [NL] o Novela Web [NW]."""
        
        # 1. Revisar si el filename original ya indica el tipo
        filename_lower = original_filename.lower()
        if '[nl]' in filename_lower:
            return 'NL'  # Ya tiene el tag, no agregar
        elif '[nw]' in filename_lower:
            return 'NW'  # Ya tiene el tag, no agregar
        
        # 2. Revisar metadata para detectar el tipo
        publisher = metadata.get('publisher', '').lower()
        description = metadata.get('description', '').lower()
        tags = metadata.get('tags', '').lower()
        
        # Indicadores de Novela Ligera
        nl_indicators = [
            'shinsengumi', 'mangaplus', 'mangadex', 'tumblr', 'light novel',
            'ln', 'traducción light', 'light novel translation'
        ]
        
        # Indicadores de Novela Web
        nw_indicators = [
            'novela web', 'web novel', 'wn', 'traducción web',
            'webnovel', 'syosetu', 'kakuyomu', 'novela online'
        ]
        
        # 3. Revisar publisher/distribuidor
        for indicator in nl_indicators:
            if indicator in publisher or indicator in tags:
                return 'NL'
        
        for indicator in nw_indicators:
            if indicator in publisher or indicator in tags:
                return 'NW'
        
        # 4. Revisar descripción
        for indicator in nl_indicators:
            if indicator in description:
                return 'NL'
        
        for indicator in nw_indicators:
            if indicator in description:
                return 'NW'
        
        # 5. Revisar categorías y demografía
        category = metadata.get('category', '').lower()
        demography = metadata.get('demography', [])
        
        # Las novelas ligeras suelen tener categorías específicas
        nl_categories = ['light novel', 'ln', 'shōnen', 'shōjo', 'seinen']
        for dem in demography:
            if any(cat in dem.lower() for cat in nl_categories):
                return 'NL'
        
        # 6. Por defecto, asumir Novela Ligera (es más común)
        return 'NL'
    
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
        `{metadata.get('suggested_path', 'N/A')}`"""

        # Alertas de conflictos
        identity_match = metadata.get('identity_match')
        path_match = metadata.get('path_match')
        
        if identity_match:
            # Caso 1: El libro ya existe (ID idéntico)
            preview_text += f"\n\n⚠️ **DUPLICADO DETECTADO**\nEsta misma edición ya existe en la biblioteca."
            if path_match and identity_match['id'] == path_match['id']:
                preview_text += f"\n📍 **Ubicación coincidente:** `{identity_match['path']}`"
            else:
                preview_text += f"\n📍 **Se encuentra actualmente en:** `{identity_match['path']}`"
                preview_text += f"\n📁 **Nueva ubicación sugerida:** `{metadata.get('suggested_path')}`"
            
            diffs = self.compare_metadata(metadata, metadata.get('existing_data'))
            if diffs:
                preview_text += f"\n\n🔍 **Cambios respecto a la versión actual:**\n{diffs}"
            
            approve_label = "🔄 Actualizar / Reemplazar"
            callback_prefix = "replace_epub"
            
        elif metadata.get('file_exists'):
            # Caso 2: Colisión de archivo pero distinta identidad
            preview_text += f"\n\n⚠️ **CONFLICTO DE FILENAME / RUTA**\nYa existe un archivo llamado `{os.path.basename(metadata['suggested_path'])}` en esa carpeta, pero es un libro distinto (distinto hash)."
            
            if path_match:
                preview_text += f"\n👤 **Libro que estorba:** `{path_match['path']}`"
                diffs = self.compare_metadata(metadata, metadata.get('existing_data'))
                if diffs:
                    preview_text += f"\n\n🔍 **Diferencias con el archivo a sobrescribir:**\n{diffs}"
            
            approve_label = "⚠️ Sobrescribir Archivo"
            callback_prefix = "overwrite_epub"
        else:
            preview_text += f"\n\n✅ Este es un archivo nuevo para la biblioteca."
            approve_label = "✅ Aprobar Subida"
            callback_prefix = "approve_epub"

        preview_text += "\n\n**¿Cómo deseas proceder?**"
        
        # Botones de acción
        keyboard = [
            [
                InlineKeyboardButton(approve_label, callback_data=f"{callback_prefix}_{upload_id}"),
                InlineKeyboardButton("❌ Rechazar", callback_data=f"reject_epub_{upload_id}")
            ],
            [
                InlineKeyboardButton("📝 Editar Ruta", callback_data=f"edit_path_{upload_id}")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(preview_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_approval_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja los callbacks de aprobación/rechazo."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        # Verificar si es admin
        if not await self.is_admin(user_id):
            await query.edit_message_text("❌ No tienes permisos para esta acción.", parse_mode=ParseMode.MARKDOWN)
            return
        
        callback_data = query.data
        # Extraer upload_id del callback_data (format: approve_epub_upload_123456789_1234567890)
        parts = callback_data.split('_')
        upload_id = '_'.join(parts[2:])  # Tomar desde el tercer elemento en adelante
        
        if upload_id not in pending_uploads:
            await query.edit_message_text("❌ Upload no encontrado o expirado.", parse_mode=ParseMode.MARKDOWN)
            return
        
        upload_info = pending_uploads[upload_id]
        
        if callback_data.startswith('approve_epub') or callback_data.startswith('replace_epub') or callback_data.startswith('overwrite_epub'):
            # Si es overwrite de archivo pero no de hash, pedir confirmación extra si no se ha pedido
            if callback_data.startswith('overwrite_epub') and not upload_info.get('overwrite_confirmed'):
                upload_info['overwrite_confirmed'] = True
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Sí, sobrescribir archivo", callback_data=f"approve_epub_{upload_id}"),
                        InlineKeyboardButton("🔙 Cancelar", callback_data=f"reject_epub_{upload_id}")
                    ]
                ]
                await query.edit_message_text(
                    "⚠️ **Confirmación de Sobrescritura**\n\n"
                    "El archivo físico ya existe. Al continuar, el archivo anterior será eliminado y reemplazado por este.\n\n"
                    "¿Estás seguro?",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            await self.approve_upload(query, upload_id, upload_info, is_replacement=callback_data.startswith('replace_epub'))
        elif callback_data.startswith('reject_epub'):
            await self.reject_upload(query, upload_id, upload_info)
        elif callback_data.startswith('edit_path'):
            await self.request_path_edit(query, upload_id, upload_info)
    
    async def approve_upload(self, query, upload_id: str, upload_info: Dict[str, Any], is_replacement: bool = False):
        """Aprueba y procesa el upload."""
        try:
            file_path = Path(upload_info['file_path'])
            metadata = upload_info['metadata']
            suggested_path = metadata.get('suggested_path', '')
            
            status_msg = "🔄 Reemplazando libro..." if is_replacement else "✅ Procesando upload..."
            await query.edit_message_text(status_msg, parse_mode=ParseMode.MARKDOWN)
            
            # Si es reemplazo por hash, eliminar el archivo físico antiguo primero
            identity_match = metadata.get('identity_match')
            if is_replacement and identity_match and identity_match.get('path'):
                old_path = Path("/library") / identity_match['path']
                if old_path.exists():
                    try:
                        old_path.unlink()
                        logger.info(f"Deleted old file for replacement: {old_path}")
                    except Exception as e:
                        logger.error(f"Error deleting old file: {e}")
            
            # Si es sobrescritura de archivo pero el hash es distinto, el archivo anterior se perderá
            if not is_replacement and metadata.get('file_exists'):
                target_path = Path("/library") / suggested_path
                if target_path.exists():
                    try:
                        target_path.unlink()
                        logger.info(f"Deleted existing file for overwrite collision: {target_path}")
                    except Exception as e:
                        logger.error(f"Error deleting existing file for overwrite: {e}")

            # Mover archivo a la librería
            success = await self.add_to_library(file_path, suggested_path, metadata)
            
            if success:
                result_text = "✅ **Libro reemplazado con éxito**" if is_replacement else "✅ **EPUB agregado exitosamente**"
                await query.edit_message_text(
                    f"{result_text}\n\n"
                    f"📁 **Ruta:** `{suggested_path}`\n"
                    f"📚 **Título:** {metadata.get('title')}\n"
                    f"✍️ **Autor:** {metadata.get('author')}\n\n"
                    f"⌛ _El sistema lo indexará automáticamente en el próximo escaneo._",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await query.edit_message_text("❌ Error agregando el EPUB a la librería.", parse_mode=ParseMode.MARKDOWN)
            
            # Limpiar
            self.cleanup_upload(upload_id, file_path)
            
        except Exception as e:
            logger.error(f"Error approving upload: {e}")
            await query.edit_message_text(f"❌ Error procesando upload: {str(e)}", parse_mode=ParseMode.MARKDOWN)
    
    async def reject_upload(self, query, upload_id: str, upload_info: Dict[str, Any]):
        """Rechaza el upload."""
        try:
            file_path = Path(upload_info['file_path'])
            
            await query.edit_message_text("❌ **Upload rechazado**", parse_mode=ParseMode.MARKDOWN)
            
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
            f"O responde 'cancel' para usar la ruta actual.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Marcar que estamos esperando edición de ruta
        query.message.chat_data[f'editing_path_{upload_id}'] = True

    def compare_metadata(self, new_data: Dict[str, Any], old_data: Optional[Dict[str, Any]]) -> str:
        """Compara metadatos y devuelve un string con las diferencias."""
        if not old_data:
            return ""
        
        diffs = []
        fields = {
            'title': 'Título',
            'author': 'Autor',
            'series': 'Serie',
            'volume': 'Volumen',
            'translator': 'Traductor',
            'publisher': 'Editorial',
            'language': 'Idioma',
            'isbn': 'ISBN'
        }
        
        from utils.helpers import norm_string
        
        for key, label in fields.items():
            new_val = str(new_data.get(key) or '').strip()
            old_val = str(old_data.get(key) or '').strip()
            
            # Usar normalización básica para comparar
            if norm_string(new_val) != norm_string(old_val):
                diffs.append(f"🔹 **{label}**: `{old_val or 'N/A'}` ➡️ `{new_val or 'N/A'}`")
        
        # Tags (Géneros) - Comparar listas
        new_tags = set(t.strip().lower() for t in (new_data.get('tags') or '').split(',') if t.strip())
        old_tags = set(t.strip().lower() for t in (old_data.get('tags') or '').split(',') if t.strip()) if isinstance(old_data.get('tags'), str) else set()
        
        if new_tags != old_tags:
            added = new_tags - old_tags
            removed = old_tags - new_tags
            tag_diff = []
            if added: tag_diff.append(f"🟢 +{', '.join(added)}")
            if removed: tag_diff.append(f"🔴 -{', '.join(removed)}")
            if tag_diff:
                diffs.append(f"🔹 **Géneros**: {' | '.join(tag_diff)}")

        return "\n".join(diffs)
    
    async def add_to_library(self, epub_path: Path, suggested_path: str, metadata: Dict[str, Any]) -> bool:
        """Agrega el EPUB a la librería y lo escanea inmediatamente."""
        try:
            logger.info(f"Starting add_to_library: epub_path={epub_path}, suggested_path={suggested_path}")
            
            # Directorio base de la librería
            library_base = Path("/library")
            
            # Crear ruta completa
            full_path = library_base / suggested_path
            
            # Verificar que el archivo fuente existe
            if not epub_path.exists():
                logger.error(f"Source EPUB file does not exist: {epub_path}")
                return False
            
            # Crear directorio si no existe
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Mover archivo
            import shutil
            logger.info(f"Moving file to: {full_path}")
            shutil.move(str(epub_path), str(full_path))
            
            # ESCANEO INMEDIATO Y ESPECÍFICO
            # Importar el servicio de escaneo
            from services.scanner_service import ScannerService
            from config.config_settings import config
            
            # Inicializar servicio con configuración (o usar singleton si existiera)
            scanner = ScannerService(config.LIBRARIES_CONFIG)
            
            # Ejecutar escaneo específico del archivo recién movido
            # Esto registrará el libro y la serie (si es nueva) inmediatamente.
            import asyncio
            await asyncio.sleep(0.5) # Breve respiro para el FS
            
            scan_result = scanner.sync_path(str(full_path), force_scan=True)
            
            if scan_result and (scan_result.get("added") or scan_result.get("updated")):
                logger.info(f"✅ Libro indexado inmediatamente: {full_path}")
                return True
            elif scan_result and scan_result.get("duplicates"):
                logger.warning(f"⚠️ Libro detectado como duplicado durante indexado: {full_path}")
                return True
            else:
                logger.error(f"❌ Error indexando el libro después de moverlo: {scan_result}")
                return True # Retornamos True porque el archivo ya se movió con éxito
                
        except Exception as e:
            logger.error(f"Error adding to library: {e}")
            return False
                
        except Exception as e:
            logger.error(f"Error adding to library: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
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
    application.add_handler(CallbackQueryHandler(handle_upload_callback, pattern=r"^(approve|reject|edit_path|replace|overwrite)_epub_"))
