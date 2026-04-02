
import asyncio
import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

def check_duplicate_books_schema():
    db_url = os.getenv("DATABASE_URL")
    # Replace 'db' with 'localhost' if running locally outside docker
    if "@db:" in db_url:
        db_url = db_url.replace("@db:", "@localhost:")
    
    print(f"Connecting to: {db_url}")
    engine = create_engine(db_url)
    
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns('duplicate_books')
        print("\nColumns in 'duplicate_books':")
        for col in columns:
            print(f"- {col['name']}: {col['type']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_duplicate_books_schema()
