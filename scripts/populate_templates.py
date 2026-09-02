import asyncio
from repositories.publication_repository import pub_repo
from models.communications import PublicationTemplate
from sqlalchemy import select
from core.db_manager_pg import pg_manager

async def main():
    telegram_content = (
        "<b>{series_english}</b>\n"
        "[?volumen]<b>Volumen {volumen}</b>\n[/?]"
        "[?genres]{genres}\n[/?]"
        "\n<blockquote expandable>\n"
        "📋 <b>Ficha Técnica</b>\n\n"
        "[?autor]👤 <b>Autor:</b> {autor}\n[/?]"
        "[?illustrator]🎨 <b>Ilustrador:</b> {illustrator}\n[/?]"
        "[?layout_by]📓 <b>Maquetador:</b> #{layout_by}\n[/?]"
        "[?tipo]📦 <b>Categoría:</b> {tipo}\n[/?]"
        "[?demography]👥 <b>Demografía:</b> {demography}\n[/?]"
        "[?traductor]🌐 <b>Traductor:</b> {traductor}\n[/?]"
        "[?editorial]🏢 <b>Grupo Traductor:</b> {editorial}\n[/?]"
        "</blockquote>\n\n"
        "[?sinopsis]<blockquote expandable>\n"
        "📖 <b>Ver Sinopsis</b>\n\n"
        "{sinopsis}\n"
        "</blockquote>[/?]\n\n"
        "#{slug}"
    )

    facebook_content = (
        "📚 [?series_english]{series_english}[/?][?!series_english]{serie}[/?] ║ {serie} [?series_spanish]║ {series_spanish}[/?]\n"
        "[?volumen]📖 Volumen {volumen}\n[/?]"
        "#{slug}\n\n"
        "[?download_link]⬇️ Descarga: {download_link}\n\n[/?]"
        "[?fecha]📅 Actualizado: {fecha}\n[/?]"
        "[?tamaño]📦 Tamaño: {tamaño}\n[/?]"
        "[?layout_by]🎨 Maquetado por: {layout_by}\n[/?]"
        "[?tipo]🏷️ Categoría: {tipo}\n[/?]"
        "[?genres]🎭 Géneros: {genres}\n[/?]"
        "[?autor]✍️ Autor: {autor}\n[/?]"
        "[?illustrator]🎨 Ilustrador: {illustrator}\n[/?]"
        "[?published_at]📅 Publicado: {published_at}\n[/?]"
        "[?traductor]🌐 Traducción: {traductor}\n[/?]"
        "[?editorial]🏢 Grupo Traductor: {editorial}\n[/?]"
        "\n[?sinopsis]📝 Sinopsis:\n\n{sinopsis}\n[/?]"
    )

    templates = [
        PublicationTemplate(
            name="Telegram (Canal Oficial)",
            content=telegram_content,
            platform="telegram",
            is_default=True,
            extra_config={"type": "official_tg"},
        ),
        PublicationTemplate(
            name="Facebook (Página Oficial)",
            content=facebook_content,
            platform="facebook",
            is_default=True,
            extra_config={"type": "official_fb"},
        ),
    ]

    # Clean previous defaults and insert
    async with pg_manager.get_session() as session:
        stmt = select(PublicationTemplate).where(
            PublicationTemplate.name.in_([
                "Telegram (Canal Oficial)",
                "Facebook (Página Oficial)",
                "Plantilla Oficial Telegram (Canal)",
                "Plantilla Oficial Facebook (Página)",
                "Plantilla Facebook",
            ])
        )
        res = await session.execute(stmt)
        for t in res.scalars():
            await session.delete(t)
        await session.commit()

    for tpl in templates:
        created = await pub_repo.create_template(tpl)
        print(f"Created template: {created.name} (id: {created.id})")

if __name__ == "__main__":
    asyncio.run(main())
