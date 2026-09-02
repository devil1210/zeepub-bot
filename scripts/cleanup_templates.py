import asyncio
from core.db_manager_pg import pg_manager
from models.communications import PublicationTemplate
from sqlalchemy import select, update

async def cleanup_templates():
    async with pg_manager.get_session() as session:
        # 1. Reset all templates is_default to False
        await session.execute(update(PublicationTemplate).values(is_default=False))

        # 2. Set only the official templates as default
        await session.execute(
            update(PublicationTemplate)
            .where(PublicationTemplate.name == "Telegram (Canal Oficial)")
            .values(is_default=True)
        )
        await session.execute(
            update(PublicationTemplate)
            .where(PublicationTemplate.name == "Facebook (Página Oficial)")
            .values(is_default=True)
        )

        await session.commit()

        # 3. Print all templates
        res = await session.execute(select(PublicationTemplate).order_by(PublicationTemplate.is_default.desc(), PublicationTemplate.id.asc()))
        all_tpls = res.scalars().all()
        print("Templates in DB after setting exact defaults:")
        for t in all_tpls:
            star = "⭐ [OFICIAL PREDETERMINADA]" if t.is_default else "  [Opcional]"
            print(f"{star} ID {t.id}: '{t.name}' (plataforma: {t.platform})")

if __name__ == "__main__":
    asyncio.run(cleanup_templates())
