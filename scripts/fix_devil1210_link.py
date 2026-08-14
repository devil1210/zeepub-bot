import asyncio
import logging
from sqlalchemy import select, update
from core.db_manager_pg import pg_manager
from models.users import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_linkage():
    """
    Re-vincula el correo charly.silva.v@gmail.com a la cuenta de Telegram Devil_1210 (ID 133994688)
    y desasocia el correo de pruebas spcore325@gmail.com.
    """
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        # 1. Buscar si charly.silva.v@gmail.com está asignado a otra cuenta temporal
        res_email = await session.execute(select(User).where(User.email == "charly.silva.v@gmail.com"))
        existing_email_user = res_email.scalar_one_or_none()

        # 2. Buscar cuenta de Telegram Devil_1210 (ID 133994688 o username Devil_1210)
        res_tg = await session.execute(
            select(User).where((User.telegram_id == 133994688) | (User.username.ilike("Devil_1210")))
        )
        devil_user = res_tg.scalar_one_or_none()

        if existing_email_user and (not devil_user or existing_email_user.telegram_id != devil_user.telegram_id):
            logger.info(f"Liberando email 'charly.silva.v@gmail.com' de usuario temporal ID {existing_email_user.telegram_id}")
            existing_email_user.email = None
            await session.flush()

        if devil_user:
            logger.info(f"Actualizando email de usuario Devil_1210 (ID {devil_user.telegram_id}) a 'charly.silva.v@gmail.com'")
            devil_user.email = "charly.silva.v@gmail.com"
            await session.commit()
            print(f"✅ Éxito: Cuenta @Devil_1210 (ID {devil_user.telegram_id}) vinculada correctamente con 'charly.silva.v@gmail.com'")
        else:
            logger.warning("No se encontró al usuario @Devil_1210 en la base de datos local PostgreSQL.")

if __name__ == "__main__":
    asyncio.run(fix_linkage())
