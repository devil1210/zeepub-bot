import asyncio
from core.db_manager_pg import pg_manager
from models.communications import PublicationTemplate
from sqlalchemy import select, update

TELEGRAM_OFFICIAL_RICH_TEMPLATE = """<img src="tg://photo?id=tomozaki_cover" />

[?series_english]🇬🇧 <b>{series_english}</b>
[/?][?!series_english]🇬🇧 <b>{serie}</b>
[/?][?romaji_title]🇯🇵 <b>{romaji_title}</b>
[/?][?series_spanish]🇪🇸 <b>{series_spanish}</b>
[/?][?volumen]📖 <b>Volumen {volumen}</b>
[/?]
<table bordered striped>
[?autor]  <tr><td>👤 Autor</td><td>{autor}</td></tr>
[/?][?illustrator]  <tr><td>🎨 Ilustrador</td><td>{illustrator}</td></tr>
[/?][?layout_by]  <tr><td>📓 Maquetador</td><td>#{layout_by}</td></tr>
[/?][?tipo]  <tr><td>📦 Categoría</td><td>{tipo}</td></tr>
[/?][?demography]  <tr><td>👥 Demografía</td><td>{demography}</td></tr>
[/?][?genres]  <tr><td>🎭 Géneros</td><td>{genres}</td></tr>
[/?][?traductor]  <tr><td>🌐 Traductor</td><td>{traductor}</td></tr>
[/?][?editorial]  <tr><td>🏢 Grupo Traductor</td><td>{editorial}</td></tr>
[/?]</table>

[?sinopsis]<details>
  <summary>📖 Ver Sinopsis</summary>
  <blockquote>
{sinopsis}
  </blockquote>
</details>
[/?]
<details>
  <summary>📁 Ver Detalles del Archivo</summary>
  <table bordered striped>
    <tr><td>📁 Nombre</td><td>{titulo}</td></tr>
[?volumen]    <tr><td>📖 Volumen</td><td>Volumen {volumen}</td></tr>
[/?][?version]    <tr><td>ℹ️ Versión Epub</td><td>{version}</td></tr>
[/?][?fecha]    <tr><td>📅 Actualizado</td><td>{fecha}</td></tr>
[/?][?size_mb]    <tr><td>💾 Tamaño</td><td>{size_mb}</td></tr>
[/?]  </table>
</details>

<tg-document src="tg://document?id=epub_file" />

#{slug}"""

FACEBOOK_TELEGRAM_TEMPLATE = """📚 [?series_english]{series_english}[/?][?!series_english]{serie}[/?][?romaji_title] ║ {romaji_title}[/?][?series_spanish] ║ {series_spanish}[/?]
[?volumen]📖 Volumen {volumen}
[/?]#{slug}

[?download_link]⬇️ Descarga: {download_link}
[/?]
[?fecha]📅 Actualizado: {fecha}
[/?][?size_mb]📦 Tamaño: {size_mb}
[/?][?!size_mb][?tamaño]📦 Tamaño: {tamaño}
[/?][?layout_by]🎨 Maquetado por: #{layout_by} #ZeePubs
[/?][?tipo]🏷️ Categoría: {tipo}
[/?][?genres]🎭 Géneros: {genres}
[/?][?autor]✍️ Autor: {autor}
[/?][?illustrator]🎨 Ilustrador: {illustrator}
[/?][?published_at]📅 Publicado: {published_at}
[/?][?traductor]🌐 Traducción: {traductor}
[/?][?editorial]🏢 Grupo Traductor: {editorial}
[/?]
[?sinopsis]📝 Sinopsis:

{sinopsis}
[/?]"""

async def populate():
    async with pg_manager.get_session() as session:
        # Reset is_default
        await session.execute(update(PublicationTemplate).values(is_default=False))

        # 1. Telegram RichMessage template (Official Canal)
        tg_res = await session.execute(
            select(PublicationTemplate).where(PublicationTemplate.name.in_(["Telegram RichMessage (Canal Oficial)", "Telegram RichMessage", "Telegram (Canal Oficial)"]))
        )
        tg_tpl = tg_res.scalars().first()
        if tg_tpl:
            tg_tpl.name = "Telegram (Canal Oficial)"
            tg_tpl.content = TELEGRAM_OFFICIAL_RICH_TEMPLATE
            tg_tpl.platform = "telegram"
            tg_tpl.is_default = True
            session.add(tg_tpl)
        else:
            new_tg = PublicationTemplate(
                name="Telegram (Canal Oficial)",
                content=TELEGRAM_OFFICIAL_RICH_TEMPLATE,
                platform="telegram",
                is_default=True,
                extra_config={"type": "rich_message"}
            )
            session.add(new_tg)

        # 2. Facebook Template for Telegram
        fb_res = await session.execute(
            select(PublicationTemplate).where(PublicationTemplate.name.in_(["Plantilla de Publicación para Facebook", "Facebook (Página Oficial)", "Facebook"]))
        )
        fb_tpl = fb_res.scalars().first()
        if fb_tpl:
            fb_tpl.name = "Plantilla de Publicación para Facebook"
            fb_tpl.content = FACEBOOK_TELEGRAM_TEMPLATE
            fb_tpl.platform = "facebook"
            fb_tpl.is_default = True
            session.add(fb_tpl)
        else:
            new_fb = PublicationTemplate(
                name="Plantilla de Publicación para Facebook",
                content=FACEBOOK_TELEGRAM_TEMPLATE,
                platform="facebook",
                is_default=True,
                extra_config={"type": "facebook_copy"}
            )
            session.add(new_fb)

        await session.commit()

        # Print all
        res = await session.execute(select(PublicationTemplate).order_by(PublicationTemplate.is_default.desc(), PublicationTemplate.id.asc()))
        for t in res.scalars().all():
            star = "⭐ OFICIAL" if t.is_default else "  Opcional"
            print(f"[{star}] ID {t.id} - '{t.name}' ({t.platform})")

if __name__ == "__main__":
    asyncio.run(populate())
