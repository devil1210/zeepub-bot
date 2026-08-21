import asyncio
import httpx
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel
from sqlalchemy import select

async def compare_tokens():
    await pg_manager.initialize()
    async with pg_manager.get_session() as s:
        ch_oficial = (await s.execute(select(PublicationChannel).where(PublicationChannel.id == 6))).scalar_one_or_none()
        ch_pruebas = (await s.execute(select(PublicationChannel).where(PublicationChannel.id == 4))).scalar_one_or_none()
        
        t_oficial = ch_oficial.config.get("page_access_token") or ch_oficial.config.get("access_token")
        t_pruebas = ch_pruebas.config.get("page_access_token") or ch_pruebas.config.get("access_token")
        
        async with httpx.AsyncClient() as c:
            r_oficial = await c.get("https://graph.facebook.com/v19.0/debug_token", params={"input_token": t_oficial, "access_token": t_oficial})
            r_pruebas = await c.get("https://graph.facebook.com/v19.0/debug_token", params={"input_token": t_pruebas, "access_token": t_pruebas})
            
            print("--- TOKEN OFICIAL (Canal 6: ZeePubs Oficial) ---")
            d_o = r_oficial.json().get("data", {})
            print("Tipo:", d_o.get("type"))
            print("App:", d_o.get("application"))
            print("Profile ID:", d_o.get("profile_id"))
            print("Scopes:", d_o.get("scopes"))
            
            print("\n--- TOKEN PRUEBAS (Canal 4: Pruebas EvilEpubs) ---")
            d_p = r_pruebas.json().get("data", {})
            print("Tipo:", d_p.get("type"))
            print("App:", d_p.get("application"))
            print("Profile ID:", d_p.get("profile_id"))
            print("Scopes:", d_p.get("scopes"))

asyncio.run(compare_tokens())
