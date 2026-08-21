import asyncio
import os
import json
import httpx
from core.db_manager_pg import pg_manager
from services.publisher.publisher_service import PublisherService
from services.cover_service import resolve_cover_data
from utils.metadata_utils import resolve_title_cascade, normalize_demography
from config.config_settings import config

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
        size_val = book_data.get("size") or "5.40 MB"
        if book.file_size:
            size_val = f"{book.file_size / (1024 * 1024):.2f} MB"
        tabla_archivo = "<details>\n  <summary>📂 Ver Detalles del Archivo</summary>\n  <table bordered striped>\n"
        tabla_archivo += f"    <tr><td><b>📂 Nombre</b></td><td>{book_data.get('title')}</td></tr>\n"
        tabla_archivo += f"    <tr><td><b>📖 Volumen</b></td><td>Volumen {vol}</td></tr>\n"
        tabla_archivo += "    <tr><td><b>ℹ️ Versión Epub</b></td><td>3.0</td></tr>\n"
        if book.file_modified_at:
            tabla_archivo += f"    <tr><td><b>📅 Actualizado</b></td><td>{book.file_modified_at.strftime('%d/%m/%Y')}</td></tr>\n"
        tabla_archivo += f"    <tr><td><b>💾 Tamaño</b></td><td>{size_val}</td></tr>\n"
        tabla_archivo += "  </table>\n</details>\n"
        html_parts.append(tabla_archivo)
        
        # Footer
        html_parts.append("<hr/>")
        slug = (book_data.get("slug") or "Arifureta").replace("-", "_")
        if not slug.startswith("#"): slug = f"#{slug}"
        html_parts.append(f"{slug}\n\n\n")
        
        html_content = "\n".join(html_parts)
        
        # Intentar 1: editMessageCaption con rich_message
        url_caption = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/editMessageCaption"
        rich_payload = {"html": html_content}
        payload = {"chat_id": "@ZeePubs", "message_id": 1701, "rich_message": json.dumps(rich_payload)}
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url_caption, data=payload, timeout=30.0)
            print("RESPUESTA editMessageCaption (rich):", resp.status_code, resp.text)
            if not resp.json().get("ok"):
                # Intentar 2: sendRichMessage como nuevo mensaje si editMessageCaption no soporta rich HTML directamente
                print("Probando sendRichMessage...")

if __name__ == "__main__":
    asyncio.run(main())
