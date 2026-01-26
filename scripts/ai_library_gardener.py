
import asyncio
import logging
import os

from rich.console import Console
from sqlalchemy import func, select, update

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook, SeriesMetadata
from services.ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.ERROR) # Mute libraries
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console = Console()

async def get_series_groups(limit: int = 50):
    """
    Obtiene grupos de libros por series_hash que necesitan actualización.
    Prioriza grupos donde 'series_spanish' es NULL.
    """
    async with pg_manager.get_session() as session:
        # 1. Encontrar hashes que tienen series_spanish NULL
        # Usamos distinct para obtener los IDs de grupo (hashes)
        subquery = (
            select(LocalBook.series_hash)
            .where(
                or_(
                    LocalBook.series_spanish.is_(None),
                    LocalBook.series_spanish == ""
                )
            )
            .group_by(LocalBook.series_hash)
            .limit(limit)
        )
        
        result = await session.execute(subquery)
        hashes = result.scalars().all()
        
        groups = []
        for h in hashes:
            # Obtener UN libro representativo para este hash
            # Preferiblemente uno que tenga 'series' escrito si existe
            stmt = (
                select(LocalBook)
                .where(LocalBook.series_hash == h)
                .order_by(LocalBook.series.desc(), LocalBook.id.asc()) # series desc pone strings antes que vacíos
                .limit(1)
            )
            rep_book = (await session.execute(stmt)).scalar_one_or_none()
            
            if rep_book:
                stmt_count = select(func.count()).where(LocalBook.series_hash == h)
                count = (await session.execute(stmt_count)).scalar()
                groups.append({
                    "hash": h,
                    "representative": rep_book,
                    "count": count
                })
        
        return groups

from sqlalchemy import or_


async def process_groups(groups: list[dict]):
    """Procesa cada grupo con la IA."""
    
    updated_total = 0
    
    for group in groups:
        rep_book: LocalBook = group["representative"]
        count = group["count"]
        series_hash = group["hash"]
        
        console.print(f"\n[cyan]Procesando grupo:[/cyan] Hash={series_hash[:8]}... (Items: {count})")
        
        # 1. Determinar string de entrada para la IA
        # Si tiene nombre en español (por filename o prev.), usarlo.
        input_name = rep_book.filename or rep_book.series_spanish or rep_book.series or rep_book.title
        
        console.print(f"  [dim]Input para IA:[/dim] '{input_name}'")
        
        # 2. Consultar IA
        try:
            suggested_data = await AIService.suggest_series_rename(input_name)
        except Exception as e:
            console.print(f"  [red]Error consultando IA:[/red] {e}")
            continue
            
        proposed_en = suggested_data.get("proposed_english")
        proposed_es = suggested_data.get("proposed_spanish")
            
        if not proposed_en:
            console.print("  [yellow]IA no devolvió sugerencia válida. Saltando.[/yellow]")
            continue
            
        console.print(f"  [green]Sugerencia IA (EN):[/green] '{proposed_en}'")
        console.print(f"  [green]Sugerencia IA (ES):[/green] '{proposed_es}'")
        
        # 3. Actualizar DB (Serie y Libros)
        async with pg_manager.get_session() as session:
            # Sincronizar SeriesMetadata
            series = session.query(SeriesMetadata).filter_by(series_hash=series_hash).first()
            if series:
                series.series_name = proposed_en
                series.series_spanish = proposed_es
            
            # Actualizar todos los libros
            stmt = (
                update(LocalBook)
                .where(LocalBook.series_hash == series_hash)
                .values(
                    series=proposed_en,
                    series_spanish=proposed_es,
                    series_metadata_id=series.id if series else None
                )
            )
            await session.execute(stmt)
            await session.commit()
            
            updated_total += count
            console.print(f"  [bot]✅ Actualizados {count} libros en DB.[/bot]")
            
        # Rate limit preventivo
        await asyncio.sleep(1.0)
        
    return updated_total

async def main():
    console.print("[bold green]🌱 Iniciando Jardinero IA de Biblioteca...[/bold green]")
    
    # Check API Key
    from config.config_settings import config
    if not config.GEMINI_API_KEY:
        console.print("[bold red]❌ Error: GEMINI_API_KEY no encontrada en config.[/bold red]")
        return

    while True:
        # Procesar por lotes
        groups = await get_series_groups(limit=20)
        
        if not groups:
            console.print("[bold blue]✨ No se encontraron más series pendientes de revisión.[/bold blue]")
            break
            
        console.print(f"[yellow]Lote encontrado: {len(groups)} series.[/yellow]")
        
        await process_groups(groups)
        
        console.print("waiting for next batch...")
        await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        if os.name == "nt":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[red]Detenido por el usuario.[/red]")
