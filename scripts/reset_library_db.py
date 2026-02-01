#!/usr/bin/env python3
"""
Script para resetear completamente la base de datos local de la biblioteca.
ADVERTENCIA: Esto eliminará TODA la información indexada y las portadas generadas.
"""

import os
import shutil
import sys
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


# Paths
DATA_DIR = os.path.join(ROOT_DIR, "data")
LIBRARY_DIR = os.path.join(DATA_DIR, "library")
DB_PATH = os.path.join(LIBRARY_DIR, "library.db")
COVERS_DIR = os.path.join(LIBRARY_DIR, "covers")


def confirm_reset():
    """Pedir confirmación al usuario antes de eliminar"""
    print(
        "⚠️  ADVERTENCIA: Vas a eliminar TODA la base de datos local de la biblioteca."
    )
    print("   Esto incluye:")
    print("   - Todos los libros indexados")
    print("   - Todas las portadas generadas")
    print("   - Todas las fuentes de biblioteca configuradas")
    print("")
    print("   Necesitarás volver a escanear tu biblioteca después de esto.")
    print("")

    response = input(
        "¿Estás seguro de que quieres continuar? (escribe 'SI' para confirmar): "
    )
    return response.strip().upper() == "SI"


def reset_database():
    """Eliminar la base de datos y portadas"""
    items_deleted = []

    # 1. Eliminar base de datos
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            items_deleted.append(f"✅ Base de datos eliminada: {DB_PATH}")
        except Exception as e:
            print(f"❌ Error eliminando DB: {e}")
            return False
    else:
        items_deleted.append(f"ℹ️  Base de datos no existía: {DB_PATH}")

    # 2. Eliminar directorio de portadas
    if os.path.exists(COVERS_DIR):
        try:
            # Contar archivos antes de eliminar
            cover_count = len(
                [
                    f
                    for f in os.listdir(COVERS_DIR)
                    if os.path.isfile(os.path.join(COVERS_DIR, f))
                ]
            )

            shutil.rmtree(COVERS_DIR)
            items_deleted.append(f"✅ {cover_count} portadas eliminadas")
        except Exception as e:
            print(f"❌ Error eliminando portadas: {e}")
            return False
    else:
        items_deleted.append("ℹ️  Directorio de portadas no existía")

    # 3. Recrear directorio de portadas vacío
    try:
        os.makedirs(COVERS_DIR, exist_ok=True)
        items_deleted.append("✅ Directorio de portadas recreado")
    except Exception as e:
        print(f"❌ Error recreando directorio: {e}")
        return False

    # Mostrar resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE RESET:")
    print("=" * 60)
    for item in items_deleted:
        print(item)
    print("=" * 60)
    print("\n✨ Base de datos reseteada exitosamente!")
    print(
        "\n📝 Próximo paso: Ejecuta el escaneo de biblioteca para reindexar tus libros."
    )

    return True


def main():
    print("")
    print("=" * 60)
    print("🗑️  RESET DE BASE DE DATOS LOCAL - ZEEPUB-BOT")
    print("=" * 60)
    print("")

    if not confirm_reset():
        print("\n❌ Operación cancelada por el usuario.")
        return

    print("\n🔄 Iniciando reset de base de datos...")

    if reset_database():
        print("\n✅ ¡Reset completado con éxito!")
        sys.exit(0)
    else:
        print("\n❌ El reset no se completó correctamente.")
        sys.exit(1)


if __name__ == "__main__":
    main()
