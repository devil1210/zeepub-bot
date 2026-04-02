import asyncio
from sqlalchemy.schema import CreateTable
from sqlalchemy import text

# Importar todos los modelos para registrar metadata
from models.base import Base
from models.library import Series, Book, Genre, Demographic, MediaAsset
from models.users import User, UserLevel, UserUISettings
from models.operations import LibrarySource, DownloadHistory, LibraryArchive
from models.communications import PublicationChannel, PublicationTemplate, PublicationQueue

async def verify_metadata():
    print("--- Verificación de Metadata SQLAlchemy v4.0 ---")
    
    try:
        # Importar modelos para que se registren en la metadata de Base
        import models.library
        import models.users
        import models.operations
        import models.communications
        
        # Obtenemos la metadata desde el objeto Base importado
        from models.base import Base
        tables = Base.metadata.sorted_tables
        print(f"Total tablas detectadas: {len(tables)}")
        
        for table in tables:
            print(f"Tabla: {table.name}")
            for column in table.columns:
                fk = f" -> {list(column.foreign_keys)[0].target_fullname}" if column.foreign_keys else ""
                print(f"  - {column.name}: {column.type}{fk}")
        
    except Exception as e:
        print(f"ERROR DURANTE VERIFICACIÓN: {e}")
        import traceback
        traceback.print_exc()
        
    except Exception as e:
        print(f"ERROR DURANTE VERIFICACIÓN: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n--- Verificación de Integridad Completada ---")

if __name__ == "__main__":
    asyncio.run(verify_metadata())
