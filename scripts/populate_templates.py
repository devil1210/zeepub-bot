import asyncio
from core.db_manager_pg import pg_manager
from models.communications import PublicationTemplate
from sqlalchemy import select, update

TELEGRAM_RICH_MESSAGE = """<p>[?series_english]<h3>🇬🇧 {series_english}</h3></p>[?][?romaji_title]<h4>🇯🇵 {romaji_title}</h4></p>[?][?series_spanish]<h5>🇪🇸 {series_spanish}</h5></p><p>[?][?!series_spanish][?series_english]<h3>🇬🇧 {serie}</h3></p>[/?][?volumen]<h6>📚 Volumen {volumen}</h6></p>[/?]<p><table bordered striped></p><p>[?autor] <tr><td><b>👤 Autor:</b></td><td>{autor}</td></tr></p>[?][?illustrator] <tr><td><b>🎨 Ilustrador:</b></td><td>{illustrator}</td></tr></p>[?][?layout_by] <tr><td><b>📓 Maquetador:</b></td><td>#{layout_by}</td></tr></p>[?][?tipo] <tr><td><b>📦 Categoría:</b></td><td>{tipo}</td></tr></p>[?][?demography] <tr><td><b>👥 Demografía:</b></td><td>{demography}</td></tr></p>[?][?genres] <tr><td><b>🏷️ Géneros:</b></td><td>{genres}</td></tr></p>[?][?traductor] <tr><td><b>🌐 Traductor:</b></td><td>{traductor}</td></tr></p>[?][?grupo_traductor] [?editorial] <tr><td><b>🏢 Grupo Traductor:</b></td><td>{editorial}</td></tr></p>[/?]</table></p><p>[?sinopsis]<details><summary>📖 Ver Sinopsis</summary><p><blockquote>{sinopsis}</blockquote></p></details>[/?]</p><p><details><summary>📁 Ver Detalles del Archivo</summary><p><table bordered striped></p><p><tr><td><b>📑 Nombre:</b></td><td>{titulo}</td></tr>[?volumen] <tr><td><b>📖 Volumen:</b></td><td>Volumen {volumen}</td></tr>[/?][?version] <tr><td><b>ℹ️ Versión Epub:</b></td><td>{version}</td></tr>[/?][?fecha] <tr><td><b>📅 Actualizado:</b></td><td>{fecha}</td></tr>[/?][?size_mb] <tr><td><b>💾 Tamaño:</b></td><td>{size_mb}</td></tr></p>[/?] </table></p></details></p><hr/><p>#{slug}</p><p>{archivo}</p>"""

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

        # 1. Telegram RichMessage template
        tg_res = await session.execute(
            select(PublicationTemplate).where(PublicationTemplate.name.in_(["Telegram RichMessage", "Telegram (Canal Oficial)"]))
        )
        tg_tpl = tg_res.scalars().first()
        if tg_tpl:
            tg_tpl.name = "Telegram RichMessage"
            tg_tpl.content = TELEGRAM_RICH_MESSAGE
            tg_tpl.platform = "telegram"
            tg_tpl.is_default = True
            session.add(tg_tpl)
        else:
            new_tg = PublicationTemplate(
                name="Telegram RichMessage",
                content=TELEGRAM_RICH_MESSAGE,
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
