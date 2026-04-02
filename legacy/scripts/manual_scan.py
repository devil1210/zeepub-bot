import asyncio
import logging

from services.scanner_service import ScannerService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_manual_scan():
    print("🚀 Iniciando escaneo manual de la librería...")
    try:
        # Inicializar service con config vacía para que use las fuentes de la DB
        scanner = ScannerService("{}")
        results = await scanner.sync_all(force_scan=True)
        if results:
            print("✅ Escaneo completado con éxito!")
            print(f"📊 Resultados: {results}")
        else:
            print("⚠️ El escaneo no devolvió resultados o ya había uno en curso.")
    except Exception as e:
        print(f"❌ Error durante el escaneo: {e}")


if __name__ == "__main__":
    asyncio.run(run_manual_scan())
