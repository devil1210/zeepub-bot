import asyncio
import os
import re
from core.db_manager_pg import pg_manager
from models.library import Book
from services.publisher.publisher_service import PublisherService
from services.publisher.telegram_provider import TelegramPublisherProvider
from services.rich_message_service import RichMessageService
from services.cover_service import resolve_cover_data
from utils.metadata_utils import resolve_title_cascade, normalize_demography
from api.main import bot as main_bot

async def main():
    async with pg_manager.get_session() as s:
        svc = PublisherService(s)
        book = await svc.book_repo.get_by_hash("8bcfccc012fdc9ce18b42dec6fe88347e3f24bd67cd5a9e3837f9ec325a9feae")
        if not book:
            print("Libro no encontrado")
            return
        
        book_data = svc._build_book_data_dict(book)
        
        # 1. Portada
        cover_data = book_data.get("cover_original") or book_data.get("cover_medium") or book.cover_medium or book.cover_original
        resolved_cover = await resolve_cover_data(cover_data)
        
        files = None
        media = None
        if resolved_cover and isinstance(resolved_cover, str) and os.path.exists(resolved_cover):
            with open(resolved_cover, "rb") as f:
                cover_bytes = f.read()
            files = {"tomozaki_cover": ("cover.jpg", cover_bytes, "image/jpeg")}
            media = [{"id": "tomozaki_cover", "media": {"type": "photo", "media": "attach://tomozaki_cover"}}]
        
        # 2. Rich HTML idéntico al oficial
        html_parts = []
        if media:
            html_parts.append('<img src="tg://photo?id=tomozaki_cover" />\n')
        
        title_en, title_jp, title_es = resolve_title_cascade(book_data)
        html_parts.append(f"<h3>🇬🇧 {title_en}</h3>")
        if title_es:
            html_parts.append(f"<h5>🇪🇸 {title_es}</h5>")
        if title_jp:
            html_parts.append(f"<h4>🇯🇵 {title_jp}</h4>")
        
        vol = book_data.get("volume", "6")
        html_parts.append(f"<h6>📚 Volumen {vol}</h6>\n")
        
        # Tabla literaria
        tabla = "<table bordered striped>\n"
        tabla += f"  <tr><td><b>👤 Autor</b></td><td>{book_data.get('author', 'Desconocido')}</td></tr>\n"
        if book_data.get("illustrator"):
            tabla += f"  <tr><td><b>🎨 Ilustrador</b></td><td>{book_data['illustrator']}</td></tr>\n"
        if book_data.get("layout_by"):
            tabla += f"  <tr><td><b>💻 Maquetador</b></td><td>{book_data['layout_by']}</td></tr>\n"
        tabla += f"  <tr><td><b>📦 Categoría</b></td><td>{book_data.get('book_type', 'Novela Ligera')}</td></tr>\n"
        
        demo = normalize_demography(book_data.get("demographics_json") or book_data.get("demography")) or "Seinen"
        tabla += f"  <tr><td><b>👥 Demografía</b></td><td>{demo}</td></tr>\n"
        
        genres = ", ".join(book_data.get("tags_json", []))
        if genres:
            tabla += f"  <tr><td><b>🎭 Géneros</b></td><td>{genres}</td></tr>\n"
        if book_data.get("translator"):
            tabla += f"  <tr><td><b>🌐 Traductor</b></td><td>{book_data['translator']}</td></tr>\n"
        if book_data.get("publisher"):
            tabla += f"  <tr><td><b>🏢 Grupo Traductor</b></td><td>{book_data['publisher']}</td></tr>\n"
        tabla += "</table>\n"
        html_parts.append(tabla)
        
        # Sinopsis
        sinopsis = book_data.get("description") or book_data.get("sinopsis") or "Sin sinopsis disponible."
        html_parts.append(f"<details>\n  <summary>📖 Ver Sinopsis</summary>\n  <blockquote>\n    {sinopsis}\n  </blockquote>\n</details>\n")
        
        # Detalles del archivo
        size_val = f"{book.file_size / (1024 * 1024):.2f} MB" if book.file_size else "5.40 MB"
        tabla_archivo = "<details>\n  <summary>📂 Ver Detalles del Archivo</summary>\n  <table bordered striped>\n"
        tabla_archivo += f"    <tr><td><b>📂 Nombre</b></td><td>{book_data.get('title')}</td></tr>\n"
        tabla_archivo += f"    <tr><td><b>📖 Volumen</b></td><td>Volumen {vol}</td></tr>\n"
        tabla_archivo += "    <tr><td><b>ℹ️ Versión Epub</b></td><td>3.0</td></tr>\n"
        if book.file_modified_at:
            tabla_archivo += f"    <tr><td><b>📅 Actualizado</b></td><td>{book.file_modified_at.strftime('%d/%m/%Y')}</td></tr>\n"
        tabla_archivo += f"    <tr><td><b>💾 Tamaño</b></td><td>{size_val}</td></tr>\n  </table>\n</details>\n"
        html_parts.append(tabla_archivo)
        
        # Footer
        html_parts.append("<hr/>")
        slug = (book_data.get("slug") or "Arifureta").replace("-", "_")
        if not slug.startswith("#"):
            slug = f"#{slug}"
        html_parts.append(f"{slug}\n\n\n")
        
        html_content = "\n".join(html_parts)
        
        res = await RichMessageService.send_rich_message(
            chat_id="@ZeePubs",
            html=html_content,
            media=media,
            files=files
        )
        print("SEND RICH MESSAGE RESULT:", res)
        if res and res.get("ok"):
            try:
                await main_bot.app.bot.delete_message(chat_id="@ZeePubs", message_id=1701)
                print("Deleted old broken message 1701")
            except Exception as e:
                print("Could not delete old message:", e)
            
            new_msg_id = res["result"]["message_id"]
            book.tg_message_id = str(new_msg_id)
            await s.commit()
            print("Successfully published authentic Rich Message with ID:", new_msg_id)

if __name__ == "__main__":
    asyncio.run(main())
