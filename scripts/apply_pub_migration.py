import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

async def run_migration():
    # Convertir URL a asyncpg si es necesario
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not found")
        return
        
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Manejar el host 'db' si estamos fuera de docker
    # Si falla la conexión a 'db', intentamos 'localhost'
    try:
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            print(f"Connecting to {db_url}...")
            
            # Crear tablas si no existen (mismo bloque que envié a Supabase)
            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS publication_channels (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                platform VARCHAR(20) NOT NULL,
                target_id VARCHAR(100) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                is_favorite BOOLEAN DEFAULT FALSE,
                config JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS discovered_chats (
                id SERIAL PRIMARY KEY,
                chat_id VARCHAR(100) UNIQUE NOT NULL,
                title VARCHAR(255) NOT NULL,
                type VARCHAR(50),
                member_count INTEGER DEFAULT 0,
                username VARCHAR(100),
                last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS publication_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                content TEXT NOT NULL,
                platform VARCHAR(20) NOT NULL,
                extra_config JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS publication_queue (
                id SERIAL PRIMARY KEY,
                book_hash VARCHAR(64) NOT NULL,
                channel_id INTEGER REFERENCES publication_channels(id) NOT NULL,
                template_id INTEGER REFERENCES publication_templates(id),
                scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                published_at TIMESTAMP WITH TIME ZONE,
                error_message TEXT,
                payload JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Asegurar que la columna extra_config existe si la tabla ya existía
            CREATE INDEX IF NOT EXISTS idx_pub_queue_book_hash ON publication_queue(book_hash);
            CREATE INDEX IF NOT EXISTS idx_pub_queue_scheduled_for ON publication_queue(scheduled_for);
            CREATE INDEX IF NOT EXISTS idx_pub_queue_status ON publication_queue(status);
            """))
            
            # Intentar el ALTER TABLE por si acaso
            try:
                await conn.execute(text("ALTER TABLE publication_templates ADD COLUMN IF NOT EXISTS extra_config JSONB;"))
                print("Column extra_config added/verified.")
            except Exception as e:
                print(f"Alter table notice (might already exist): {e}")

            print("Migration completed successfully.")
    except Exception as e:
        if "db" in str(e) and "getaddrinfo" in str(e):
            print("Host 'db' not reachable, trying 'localhost'...")
            localhost_url = db_url.replace("@db:", "@localhost:")
            engine = create_async_engine(localhost_url)
            async with engine.begin() as conn:
                await conn.execute(text("ALTER TABLE publication_templates ADD COLUMN IF NOT EXISTS extra_config JSONB;"))
                print("Migration completed on localhost.")
        else:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_migration())
