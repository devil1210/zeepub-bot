import asyncio
import logging
import os
import difflib

from rich.console import Console
from sqlalchemy import func, select, update, or_
from datetime import datetime

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook, SeriesMetadata, MetadataProposal
from services.ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.ERROR) # Mute libraries
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console = Console()

async def get_series_for_proposal(limit: int = 20):
    """
    Obtiene series que necesitan revisión y NO tienen una propuesta pendiente.
    Prioriza series con nombres "sucios" o sin series_spanish.
    """
    async with pg_manager.get_session() as session:
        # Encontrar series que no tienen propuesta pendiente
        pending_subquery = select(MetadataProposal.series_hash).where(MetadataProposal.status == "pending")
        
        # Series candidatas: 
        # - series_spanish nulo o vacío
        # - O series_name contiene caracteres típicos de archivos (corchetes, paréntesis, "Vol")
        stmt = (
            select(LocalBook.series_hash)
            .where(
                or_(
                    LocalBook.series_spanish.is_(None),
                    LocalBook.series_spanish == "",
                    LocalBook.series.ilike("%[%"),
                    LocalBook.series.ilike("%(%"),
                    LocalBook.series.ilike("%Vol%")
                )
            )
            .where(LocalBook.series_hash.notin_(pending_subquery))
            .group_by(LocalBook.series_hash)
            .limit(limit)
        )
        
        result = await session.execute(stmt)
        hashes = result.scalars().all()
        
        series_data = []
        for h in hashes:
            # Obtener libros de la serie
            stmt_books = select(LocalBook).where(LocalBook.series_hash == h).order_by(LocalBook.volume.asc())
            books = (await session.execute(stmt_books)).scalars().all()
            
            if books:
                # Nombre actual representativo
                current_name = books[0].series or books[0].title
                series_data.append({
                    "series_hash": h,
                    "current_name": current_name,
                    "books": [b.to_dict() for b in books]
                })
        
        return series_data

async def process_proposals(series_list: list[dict]):
    """Genera propuestas de la IA y las guarda en la DB para revisión admin."""
    
    proposed_total = 0
    
    for entry in series_list:
        series_hash = entry["series_hash"]
        current_name = entry["current_name"]
        books_dicts = entry["books"]
        
        console.print(f"\n[cyan]Generando propuesta para:[/cyan] '{current_name}' (Hash: {series_hash[:8]}...)")
        
        try:
            # Consultar IA (Usa el mismo método que la MiniApp para coherencia)
            proposal = await AIService.analyze_series_for_updates(series_hash, current_name, books_dicts)
            
            if not proposal or proposal.get("proposed_series") == "sin propuesta":
                console.print("  [yellow]IA no encontró cambios necesarios. Saltando.[/yellow]")
                continue
                
            # Guardar en MetadataProposal
            async with pg_manager.get_session() as session:
                # Verificar de nuevo por si se creó una en paralelo
                stmt_exists = select(MetadataProposal).where(
                    MetadataProposal.series_hash == series_hash, 
                    MetadataProposal.status == "pending"
                )
                exists = (await session.execute(stmt_exists)).scalar_one_or_none()
                if exists:
                    console.print("  [yellow]Ya existe una propuesta pendiente para esta serie.[/yellow]")
                    continue
                
                new_proposal = MetadataProposal(
                    series_hash=series_hash,
                    proposal_data=proposal,
                    status="pending"
                )
                session.add(new_proposal)
                await session.commit()
                
                proposed_total += 1
                console.print(f"  [green]✅ Propuesta guardada para revisión admin.[/green]")
                console.print(f"  [dim]Sugerencia:[/dim] {proposal.get('proposed_series')} / {proposal.get('proposed_spanish')}")
                
        except Exception as e:
            console.print(f"  [red]Error procesando serie:[/red] {e}")
            continue
            
        # Rate limit preventivo para no saturar la API
        await asyncio.sleep(2.0)
        
    return proposed_total

async def find_merges(limit: int = 5):
    """
    Busca series con nombres similares y propone unificarlas.
    """
    async with pg_manager.get_session() as session:
        # 1. Obtener todas las series actuales
        stmt = select(SeriesMetadata)
        res = await session.execute(stmt)
        all_series = res.scalars().all()
        
        if len(all_series) < 2: return 0
        
        # 2. Encontrar candidatos por similitud de nombre (Heurística rápida)
        merge_count = 0
        checked_pairs = set()
        
        for i, s1 in enumerate(all_series):
            for j, s2 in enumerate(all_series[i+1:], start=i+1):
                # Evitar revisar lo mismo
                pair_id = tuple(sorted([s1.series_hash, s2.series_hash]))
                if pair_id in checked_pairs: continue
                checked_pairs.add(pair_id)
                
                # Regla rápida: Nombres parecidos
                ratio = difflib.SequenceMatcher(None, s1.series_name.lower(), s2.series_name.lower()).ratio()
                
                if ratio > 0.85 and ratio < 1.0: # Similares pero no idénticos (el hash es distinto)
                    # Verificar si ya existe propuesta
                    existing = (await session.execute(
                        select(MetadataProposal).where(
                            MetadataProposal.type == "merge",
                            MetadataProposal.series_hash == s1.series_hash,
                            MetadataProposal.secondary_hash == s2.series_hash,
                            MetadataProposal.status == "pending"
                        )
                    )).scalar_one_or_none()
                    
                    if existing: continue
                    
                    console.print(f"\n[bold magenta]🔍 Posible Duplicado:[/bold magenta] '{s1.series_name}' vs '{s2.series_name}' (Similitud: {ratio:.2f})")
                    
                    # 3. Consultar IA para confirmación y detalles
                    s1_dict = {"series_name": s1.series_name, "author": s1.author, "book_count": s1.book_count}
                    s2_dict = {"series_name": s2.series_name, "author": s2.author, "book_count": s2.book_count}
                    
                    merge_analysis = await AIService.analyze_potential_merge(s1_dict, s2_dict)
                    
                    if merge_analysis and merge_analysis.get("is_same"):
                        # Guardar propuesta de unificación
                        new_prop = MetadataProposal(
                            series_hash=s1.series_hash,
                            secondary_hash=s2.series_hash,
                            type="merge",
                            proposal_data=merge_analysis,
                            status="pending"
                        )
                        session.add(new_prop)
                        await session.commit()
                        
                        console.print(f"  [green]✅ Propuesta de FUSIÓN generada.[/green]")
                        console.print(f"  [dim]Razón:[/dim] {merge_analysis.get('reason')}")
                        merge_count += 1
                        
                        if merge_count >= limit: return merge_count
                    
                    await asyncio.sleep(1) # Rate limit
                    
        return merge_count

async def main():
    console.print("[bold green]🌱 Iniciando Jardinero IA de Biblioteca (Modo Propuestas)...[/bold green]")
    console.print("[dim]En este modo, la IA solo sugiere cambios pero NO los aplica hasta tu aprobación.[/dim]")
    
    # Check API Key
    from config.config_settings import config
    if not config.GEMINI_API_KEY:
        console.print("[bold red]❌ Error: GEMINI_API_KEY no encontrada en config.[/bold red]")
        return

    while True:
        # 1. Obtener series que necesitan revisión (Enriquecimiento)
        series_to_analyze = await get_series_for_proposal(limit=5)
        batch_count = 0
        
        if series_to_analyze:
            console.print(f"[yellow]Analizando lote de {len(series_to_analyze)} series para enriquecimiento...[/yellow]")
            batch_count = await process_proposals(series_to_analyze)
            console.print(f"[bold cyan]Lote completado: {batch_count} propuestas de enriquecimiento generadas.[/bold cyan]")
        
        # 2. Si no hubo enriquecimientos, buscar fusiones
        if batch_count == 0:
            console.print("[yellow]Buscando posibles fusiones de series duplicadas...[/yellow]")
            merge_count = await find_merges(limit=5)
            if merge_count == 0:
                console.print("[bold blue]✨ No se encontraron series pendientes de análisis ni de fusión.[/bold blue]")
                break
            console.print(f"[bold magenta]Se detectaron {merge_count} posibles fusiones.[/bold magenta]")
        
        # Pausa entre lotes
        console.print("esperando 10 segundos para el siguiente lote...")
        await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        if os.name == "nt":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[red]Detenido por el usuario.[/red]")
