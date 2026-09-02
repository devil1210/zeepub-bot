import asyncio
from repositories.publisher_repository import PublisherRepository
from models.database import PublicationTemplate
from services.publisher.telegram_provider import TelegramPublisherProvider

async def main():
    repo = PublisherRepository()
    await repo.init_db()

    templates = [
        PublicationTemplate(
            name="Plantilla Oficial Telegram (Canal)",
            content=(
                "<img src=\"tg://photo?id=cover\" />\n"
                "[?series_english]<h3>{series_english}</h3>[/?]\n"
                "[?romaji_title]<h4>{romaji_title}</h4>[/?]\n"
                "[?series_spanish]<h5>{series_spanish}</h5>[/?]\n"
                "[?volumen]<h6>Volumen {volumen}</h6>[/?]\n\n"
                "<table bordered striped>\n"
                "[?autor]<tr><td>👤 <b>Autor</b></td><td>{autor}</td></tr>[/?]\n"
                "[?illustrator]<tr><td>🎨 <b>Ilustrador</b></td><td>{illustrator}</td></tr>[/?]\n"
                "[?layout_by]<tr><td>🖌️ <b>Maquetador</b></td><td>{layout_by}</td></tr>[/?]\n"
                "[?tipo]<tr><td>🏷 <b>Categoría</b></td><td>{tipo}</td></tr>[/?]\n"
                "[?demography]<tr><td>👥 <b>Demografía</b></td><td>{demography}</td></tr>[/?]\n"
                "[?genres]<tr><td>🎭 <b>Géneros</b></td><td>{genres}</td></tr>[/?]\n"
                "[?traductor]<tr><td>🌐 <b>Traductor</b></td><td>{traductor}</td></tr>[/?]\n"
                "[?editorial]<tr><td>🏢 <b>Grupo Traductor</b></td><td>{editorial}</td></tr>[/?]\n"
                "</table>\n\n"
                "[?sinopsis]<blockquote expandable>\n"
                "📖 <b>Sinopsis:</b>\n"
                "{sinopsis}\n"
                "</blockquote>[/?]\n\n"
                "[?download_link]📥 <a href=\"{download_link}\">Descargar EPUB</a>\n[/?]"
                "#{slug} #ZeePubs"
            ),
            platform="telegram",
            is_default=True,
            extra_config={"type": "official_rich"},
        ),
        PublicationTemplate(
            name="Plantilla Oficial Facebook (Página)",
            content=TelegramPublisherProvider.FB_CAPTION_TEMPLATE,
            platform="facebook",
            is_default=True,
            extra_config={"type": "official_fb"},
        ),
    ]

    for tpl in templates:
        created = await repo.create_template(tpl)
        print(f"Created template: {created.name} (id: {created.id})")

if __name__ == "__main__":
    asyncio.run(main())
