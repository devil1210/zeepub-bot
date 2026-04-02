import asyncio
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

async def check_columns():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    client = create_client(url, key)
    
    try:
        # Intenta seleccionar las columnas
        res = client.table("local_books").select("id, title, spanish_title, english_title").limit(1).execute()
        print("Columnas aceptadas:")
        print(res.data)
    except Exception as e:
        print("Error comprobando columnas:")
        print(e)
        
if __name__ == "__main__":
    asyncio.run(check_columns())
