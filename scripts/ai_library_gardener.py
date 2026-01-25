
import asyncio
import logging
from typing import List, Optional

from sqlalchemy import select, update, func, and_
from rich.console import Console
from rich.progress import Progress

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

async def process_groups(groups: List[dict]):
    """Procesa cada grupo con la IA."""
    
    updated_total = 0
    
    for group in groups:
        rep_book: LocalBook = group["representative"]
        count = group["count"]
        series_hash = group["hash"]
        
        console.print(f"\n[cyan]Procesando grupo:[/cyan] Hash={series_hash[:8]}... (Items: {count})")
        
        # 1. Determinar string de entrada para la IA
        # Si tiene serie, usarla. Si no, usar el título.
        input_name = rep_book.series if rep_book.series else rep_book.title
        
        console.print(f"  [dim]Input para IA:[/dim] '{input_name}'")
        
        # 2. Consultar IA
        try:
            suggested_name = await AIService.suggest_series_rename(input_name)
        except Exception as e:
            console.print(f"  [red]Error consultando IA:[/red] {e}")
            continue
            
        if not suggested_name:
            console.print("  [yellow]IA no devolvió sugerencia. Saltando.[/yellow]")
            continue
            
        console.print(f"  [green]Sugerencia IA:[/green] '{suggested_name}'")
        
        # 3. Actualizar DB (Todos los libros del hash)
        async with pg_manager.get_session() as session:
            stmt = (
                update(LocalBook)
                .where(LocalBook.series_hash == series_hash)
                .values(series_spanish=suggested_name)
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
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[red]Detenido por el usuario.[/red]")
