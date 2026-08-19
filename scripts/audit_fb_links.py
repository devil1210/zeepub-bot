#!/usr/bin/env python3
"""
Facebook Posts & Links Auditor (Fase 1 y Fase 2)
Audita todas las publicaciones de la Fanpage de Facebook vía Graph API v21.0,
extrae los enlaces contenidos en los posts y verifica concurrentemente su estado HTTP.
"""

import asyncio
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fb_audit")

# Regex robusta para capturar URLs (http/https)
URL_REGEX = re.compile(
    r"https?://(?:[a-zA-Z0-9\-_]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:/[^\s<>'\"`(){}[\]]*)?",
    re.IGNORECASE,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


async def fetch_all_posts(page_id: str, access_token: str) -> list[dict[str, Any]]:
    """
    Fase 1: Conecta a la Graph API v21.0 y pagina por todo el feed de publicaciones.
    """
    url = f"https://graph.facebook.com/v21.0/{page_id}/published_posts"
    params = {
        "access_token": access_token,
        "fields": "id,message,created_time,permalink_url",
        "limit": "100",
    }
    
    all_posts = []
    page_num = 1
    
    logger.info(f"🚀 [FASE 1] Iniciando extracción de publicaciones para Page ID: {page_id}...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while url:
            try:
                resp = await client.get(url, params=params if page_num == 1 else None)
                if resp.status_code != 200:
                    logger.error(f"❌ Error en Graph API (HTTP {resp.status_code}): {resp.text}")
                    break
                
                data = resp.json()
                posts = data.get("data", [])
                all_posts.extend(posts)
                
                logger.info(f"   📄 Página {page_num}: Obtenidas {len(posts)} publicaciones (Total acumulado: {len(all_posts)})")
                
                paging = data.get("paging", {})
                url = paging.get("next")
                page_num += 1
                params = None  # En las siguientes páginas la URL ya contiene los parámetros
                
                # Pausa preventiva para respetar Rate Limits de Meta
                await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.error(f"❌ Excepción al paginar publicaciones: {e}")
                break
                
    logger.info(f"✅ [FASE 1 COMPLETADA] Total de publicaciones encontradas: {len(all_posts)}")
    return all_posts


async def check_single_url(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    url: str,
) -> dict[str, Any]:
    """Verifica el estado HTTP de una URL con timeout y seguimiento de redirecciones."""
    async with semaphore:
        try:
            # Intento inicial con HEAD
            resp = await client.head(url, headers=HEADERS, follow_redirects=True, timeout=12.0)
            status_code = resp.status_code
            
            # Si el servidor no soporta HEAD (405, 403, 501), reintentar con GET
            if status_code in (405, 403, 501, 400):
                resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=12.0)
                status_code = resp.status_code
                
            is_broken = status_code >= 400
            error_reason = None
            if is_broken:
                error_reason = f"HTTP {status_code}"
                
            return {
                "url": url,
                "status_code": status_code,
                "final_url": str(resp.url),
                "is_broken": is_broken,
                "error": error_reason,
            }
        except httpx.TimeoutException:
            return {
                "url": url,
                "status_code": None,
                "final_url": None,
                "is_broken": True,
                "error": "Timeout (>12s)",
            }
        except httpx.ConnectError as e:
            return {
                "url": url,
                "status_code": None,
                "final_url": None,
                "is_broken": True,
                "error": f"Error de conexión / Dominio caído ({type(e).__name__})",
            }
        except Exception as e:
            return {
                "url": url,
                "status_code": None,
                "final_url": None,
                "is_broken": True,
                "error": f"Error: {str(e)[:60]}",
            }


async def audit_links_in_posts(posts: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Fase 2: Extrae todos los enlaces de los posts y verifica concurrentemente su estado.
    """
    logger.info("🔍 [FASE 2] Extrayendo enlaces de los mensajes...")
    
    # Mapear qué post tiene qué enlaces
    posts_with_links = []
    unique_urls = set()
    
    for p in posts:
        msg = p.get("message") or ""
        found_urls = URL_REGEX.findall(msg)
        # Limpieza básica de caracteres finales no deseados
        cleaned_urls = []
        for u in found_urls:
            u_clean = u.rstrip(".,;!?)]}")
            cleaned_urls.append(u_clean)
            unique_urls.add(u_clean)
            
        if cleaned_urls:
            posts_with_links.append({
                "post_id": p.get("id"),
                "created_time": p.get("created_time"),
                "permalink_url": p.get("permalink_url"),
                "message": msg,
                "urls": cleaned_urls,
            })
            
    logger.info(f"   📊 Posts con enlaces: {len(posts_with_links)}")
    logger.info(f"   🔗 Total de URLs únicas a verificar: {len(unique_urls)}")
    
    # Verificación concurrente con Semaphore (máx 15 simultáneas para evitar saturación)
    semaphore = asyncio.Semaphore(15)
    url_results = {}
    
    logger.info("⚡ Comprobando estado HTTP de cada enlace...")
    async with httpx.AsyncClient(verify=False) as client:
        tasks = [check_single_url(client, semaphore, url) for url in unique_urls]
        checked = 0
        total = len(tasks)
        
        for coro in asyncio.as_completed(tasks):
            res = await coro
            url_results[res["url"]] = res
            checked += 1
            if checked % 20 == 0 or checked == total:
                logger.info(f"   Verificados: {checked}/{total} ({checked*100//total}%)")
                
    # Cruzar resultados con las publicaciones
    audit_report = []
    broken_links_count = 0
    
    for item in posts_with_links:
        broken_in_post = []
        for u in item["urls"]:
            u_res = url_results.get(u, {})
            if u_res.get("is_broken"):
                broken_in_post.append({
                    "url": u,
                    "status_code": u_res.get("status_code"),
                    "error": u_res.get("error"),
                })
                broken_links_count += 1
                
        if broken_in_post:
            audit_report.append({
                "post_id": item["post_id"],
                "created_time": item["created_time"],
                "permalink_url": item["permalink_url"],
                "message_snippet": item["message"][:120].replace("\n", " ") + "..." if len(item["message"]) > 120 else item["message"],
                "broken_links": broken_in_post,
            })
            
    return {
        "total_posts": len(posts),
        "posts_with_links": len(posts_with_links),
        "total_unique_urls": len(unique_urls),
        "total_broken_occurrences": broken_links_count,
        "posts_with_broken_links": len(audit_report),
        "broken_posts_details": audit_report,
        "all_urls_status": url_results,
    }


async def main():
    # Obtener credenciales de la BD o variables
    from core.db_manager_pg import pg_manager
    from models.communications import PublicationChannel
    from sqlalchemy import select

    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        # Canal 6: ZeePubs Oficial
        res = await session.execute(select(PublicationChannel).where(PublicationChannel.id == 6))
        channel = res.scalar_one_or_none()
        
        if not channel:
            logger.error("❌ No se encontró el canal ID 6 (ZeePubs Oficial) en la base de datos.")
            return

        page_id = str(channel.target_id)
        token = channel.config.get("page_access_token") if channel.config else None
        
        if not page_id or not token:
            logger.error("❌ Falta target_id o page_access_token en el canal.")
            return

    # 1. Fase 1: Extracción
    posts = await fetch_all_posts(page_id=page_id, access_token=token)
    
    # 2. Fase 2: Auditoría de Links
    results = await audit_links_in_posts(posts)
    
    # 3. Guardar Reporte en JSON
    output_path = Path("data/facebook_links_audit_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    logger.info(f"💾 Reporte completo guardado en: {output_path.resolve()}")
    
    # 4. Mostrar resumen en consola
    print("\n" + "=" * 60)
    print("📊 RESUMEN EJECUTIVO DE AUDITORÍA (Fases 1 y 2)")
    print("=" * 60)
    print(f"Total de Publicaciones en la Fanpage: {results['total_posts']}")
    print(f"Publicaciones que contienen enlaces:   {results['posts_with_links']}")
    print(f"Total de URLs únicas verificadas:     {results['total_unique_urls']}")
    print(f"Publicaciones con enlaces rotos:      {results['posts_with_broken_links']}")
    print(f"Total de instancias de links rotos:   {results['total_broken_occurrences']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
