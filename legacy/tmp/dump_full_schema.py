import asyncio
import io
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def dump_schema():
    async with pg_manager.get_session() as session:
        # Get all table names in public schema
        result = await session.execute(text("""
            SELECT tablename 
            FROM pg_catalog.pg_tables 
            WHERE schemaname = 'public';
        """))
        tables = [row[0] for row in result]
        
        print("-- FULL SQL SCHEMA DUMP (LOCAL)")
        for table in sorted(tables):
            # For each table, try to get its column info
            print(f"\n-- Table: {table}")
            col_result = await session.execute(text(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position;
            """))
            cols = []
            for col in col_result:
                name, dtype, nullable, default = col
                null_str = "NOT NULL" if nullable == "NO" else "NULL"
                def_str = f" DEFAULT {default}" if default else ""
                cols.append(f"    {name} {dtype} {null_str}{def_str}")
            
            print(f"CREATE TABLE {table} (\n" + ",\n".join(cols) + "\n);")

if __name__ == "__main__":
    asyncio.run(dump_schema())
