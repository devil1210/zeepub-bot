import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()


def verify_db():
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "321654")
    host = "localhost"
    port = "5432"
    dbname = "zeepub"

    print(f"Intentando conectar a PostgreSQL como '{user}' en {host}:{port}...")

    try:
        # Conectar a la base de datos 'postgres' para administración
        conn = psycopg2.connect(dbname="postgres", user=user, password=password, host=host, port=port)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Verificar si existe 'zeepub'
        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (dbname,))
        exists = cur.fetchone()

        if not exists:
            print(f"Creando base de datos '{dbname}'...")
            cur.execute(f"CREATE DATABASE {dbname}")
            print(f"Base de datos '{dbname}' creada correctamente.")
        else:
            print(f"La base de datos '{dbname}' ya existe.")

        cur.close()
        conn.close()

        # Conectar a la base de datos 'zeepub' para verificar extensiones
        print(f"Verificando extensiones en '{dbname}'...")
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Intentar habilitar pgvector (si existe el archivo de la extensión)
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            print("Extensión 'pgvector' habilitada.")
        except Exception as e:
            print(f"Aviso: No se pudo habilitar 'pgvector': {e}")
            print("Esto es normal si no instalaste pgvector con el Stack Builder.")

        cur.close()
        conn.close()
        print("\n--- TODO LISTO PARA EL BOT ---")

    except Exception as e:
        print(f"\nERROR CRÍTICO: {e}")


if __name__ == "__main__":
    verify_db()
