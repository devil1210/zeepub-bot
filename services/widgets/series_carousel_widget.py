# services/widgets/series_carousel_widget.py
"""
Servicio para la generación y despacho de Widgets HTML interactivos (Telegram Bot API 10.4).
Proporciona Carruseles de Volúmenes enriquecidos, renderizados dentro del chat mediante QuickJS.
Diseñado para el entorno de desarrollo (Dev) con fallback resiliente.
"""

import base64
import json
import logging
import os
import re
from typing import Any

import httpx

from config.config_settings import config

logger = logging.getLogger("zeepub.widgets")


def _clean_text(raw_text: str | None) -> str:
    """Elimina etiquetas HTML y espacios redundantes."""
    if not raw_text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", str(raw_text))
    clean = " ".join(clean.split()).strip()
    return clean.replace("<", "&lt;").replace(">", "&gt;")


def _resolve_cover_data_uri(v: dict[str, Any], base_web_url: str = "") -> str:
    """
    Resuelve la portada para el Widget HTML.
    Prioriza leer la imagen local desde disco en Base64 (data:image/jpeg;base64,...)
    para garantizar renderizado offline inmediato y evitar bloqueos de Cloudflare Access.
    """
    from utils.library_db import COVERS_DIR, THUMBNAILS_DIR

    book_id = str(v.get("id") or v.get("book_hash") or "")

    # Lista de nombres/rutas candidatas a buscar en disco
    candidates: list[str] = []
    for key in [
        "cover_low",
        "cover_medium",
        "cover_high",
        "cover_original",
        "portada",
        "coverUrl",
    ]:
        val = v.get(key)
        if val and isinstance(val, str):
            candidates.append(os.path.basename(val))

    if book_id:
        candidates.extend([
            f"{book_id}_low.jpg",
            f"{book_id}.jpg",
            f"{book_id}_medium.jpg",
            f"{book_id}_high.jpg",
        ])

    # 1. Intentar leer en base64 desde disco (en THUMBNAILS_DIR o COVERS_DIR)
    search_dirs = [d for d in [THUMBNAILS_DIR, COVERS_DIR] if os.path.exists(d)]
    for target_dir in search_dirs:
        for cand in candidates:
            cand_path = os.path.join(target_dir, cand)
            if os.path.isfile(cand_path):
                try:
                    size = os.path.getsize(cand_path)
                    # Aceptar imágenes hasta 128 KB para incrustar en widget
                    if 0 < size <= 131072:
                        with open(cand_path, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode("ascii")
                            return f"data:image/jpeg;base64,{b64}"
                except OSError:
                    pass

    # 2. Fallback a URL pública
    for key in [
        "cover_medium",
        "cover_low",
        "cover_high",
        "cover_original",
        "coverUrl",
        "portada",
    ]:
        val = v.get(key)
        if val and isinstance(val, str):
            if val.startswith(("http://", "https://")):
                return val
            if val.startswith("/") and base_web_url:
                return f"{base_web_url.rstrip('/')}{val}"

    return ""


def build_series_carousel_widget_html(
    series_title: str,
    author: str,
    description: str,
    volumes: list[dict[str, Any]],
    current_index: int = 0,
    base_web_url: str = "",
) -> str:
    """
    Construye un documento HTML5 autónomo y con altura generosa para renderizar un
    Carrusel de Volúmenes interactivo dentro de un mensaje de Telegram mediante Bot API 10.4.
    """
    clean_series_desc = _clean_text(description) or "Sin descripción disponible para esta serie."
    if len(clean_series_desc) > 360:
        clean_series_desc = clean_series_desc[:357] + "..."

    bot_username = getattr(config, "BOT_USERNAME", "") or "ZeePubs_Bot"

    # Preparar el payload de volúmenes con sinopsis y portadas individuales
    volumes_payload = []
    for idx, v in enumerate(volumes):
        v_title = (
            v.get("titulo")
            or v.get("title")
            or f"Volumen {v.get('vol_display', v.get('volume', idx + 1))}"
        )
        vol_desc_raw = v.get("description")
        v_synopsis = _clean_text(vol_desc_raw) if vol_desc_raw else clean_series_desc
        if len(v_synopsis) > 360:
            v_synopsis = v_synopsis[:357] + "..."

        cover_uri = _resolve_cover_data_uri(v, base_web_url)

        volumes_payload.append({
            "id": str(v.get("id") or v.get("book_hash") or ""),
            "vol_num": str(v.get("vol_display", v.get("volume", idx + 1))),
            "title": v_title,
            "translator": v.get("translator_siglas") or v.get("translator") or "Oficial",
            "is_color": bool(v.get("color")),
            "cover": cover_uri,
            "synopsis": v_synopsis,
        })

    volumes_json = json.dumps(volumes_payload, ensure_ascii=False)
    initial_vol = volumes_payload[current_index] if volumes_payload else {}
    initial_synopsis = initial_vol.get("synopsis", clean_series_desc)
    initial_title = initial_vol.get("title", f"Volumen {current_index + 1}")
    total_vols = len(volumes_payload)

    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<style>
  :root {{
    --bg-card: rgba(15, 23, 42, 0.92);
    --border: rgba(255, 255, 255, 0.12);
    --primary: #2b6cee;
    --primary-hover: #3b82f6;
    --text-primary: #f8fafc;
    --text-muted: #94a3b8;
    --badge-bg: rgba(43, 108, 238, 0.22);
    --badge-color: #60a5fa;
  }}
  * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
  body {{
    margin: 0;
    padding: 8px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: var(--text-primary);
    background: transparent;
  }}
  .glass-card {{
    background: var(--bg-card);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 16px;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45);
    display: flex;
    flex-direction: column;
    gap: 12px;
  }}
  .header {{
    display: flex;
    gap: 14px;
    align-items: stretch;
  }}
  .cover-box {{
    position: relative;
    width: 110px;
    height: 162px;
    flex-shrink: 0;
    border-radius: 12px;
    overflow: hidden;
    background: linear-gradient(135deg, #1e293b, #0f172a);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.55);
    border: 1px solid rgba(255, 255, 255, 0.12);
  }}
  .cover-placeholder {{
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    background: linear-gradient(145deg, #1e293b, #0f172a);
  }}
  .ph-icon {{ font-size: 32px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5)); }}
  .ph-vol {{ font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.5px; }}
  .cover-box img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: opacity 0.25s ease;
    display: none;
  }}
  .color-badge {{
    position: absolute;
    top: 6px;
    right: 6px;
    background: rgba(245, 158, 11, 0.95);
    color: #000;
    font-size: 9px;
    font-weight: 800;
    padding: 2px 5px;
    border-radius: 4px;
    letter-spacing: 0.3px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.4);
  }}
  .info {{
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 2px 0;
  }}
  .series-title {{
    font-size: 14px;
    font-weight: 700;
    margin: 0;
    line-height: 1.35;
    color: #f8fafc;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }}
  .vol-title {{
    font-size: 12px;
    font-weight: 600;
    color: #60a5fa;
    margin-top: 4px;
    line-height: 1.3;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }}
  .author {{
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 3px;
  }}
  .badges-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
  }}
  .badge {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 6px;
  }}
  .badge-vol {{
    color: var(--badge-color);
    background: var(--badge-bg);
    border: 1px solid rgba(59, 130, 246, 0.25);
  }}
  .badge-trans {{
    background: rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
    border: 1px solid rgba(255, 255, 255, 0.06);
  }}
  .synopsis-box {{
    padding: 10px 12px;
    background: rgba(255, 255, 255, 0.035);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.06);
  }}
  .synopsis-header {{
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748b;
    margin-bottom: 4px;
  }}
  .synopsis-text {{
    font-size: 11.5px;
    line-height: 1.5;
    color: #cbd5e1;
    margin: 0;
    min-height: 54px;
    max-height: 110px;
    overflow-y: auto;
    display: block;
  }}
  .selector-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 10px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.06);
  }}
  .nav-btn {{
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    font-size: 13px;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.15s;
  }}
  .nav-btn:active {{
    background: rgba(255, 255, 255, 0.22);
  }}
  .counter {{
    font-size: 12px;
    font-weight: 700;
    font-family: monospace;
    color: var(--text-muted);
  }}
  .action-row {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }}
  .btn-act {{
    padding: 11px 12px;
    border-radius: 12px;
    border: none;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    min-height: 42px;
    transition: transform 0.1s, background 0.2s;
  }}
  .btn-act:active {{ transform: scale(0.97); }}
  .btn-read {{
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: #ffffff;
    border: 1px solid rgba(96, 165, 250, 0.3);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
  }}
  .btn-read:active {{ background: #1d4ed8; }}
  .btn-dl {{
    background: rgba(255, 255, 255, 0.08);
    color: var(--text-primary);
    border: 1px solid rgba(255, 255, 255, 0.12);
  }}
  .btn-dl:active {{ background: rgba(255, 255, 255, 0.16); }}
</style>
</head>
<body>
  <div class="glass-card">
    <div class="header">
      <div class="cover-box">
        <div id="coverPlaceholder" class="cover-placeholder">
          <span class="ph-icon">📖</span>
          <span class="ph-vol" id="phVolNum">Vol. 1</span>
        </div>
        <img id="volCover" src="" alt="" />
        <span id="colorBadge" class="color-badge" style="display: none;">COLOR</span>
      </div>
      <div class="info">
        <div>
          <h2 class="series-title">{series_title}</h2>
          <div class="vol-title" id="volTitle">{initial_title}</div>
          <div class="author">✍️ {author}</div>
        </div>
        <div class="badges-row">
          <span class="badge badge-vol" id="volBadge">📖 Vol. 1</span>
          <span class="badge badge-trans" id="transLabel">🌐 Fansub</span>
        </div>
      </div>
    </div>

    <!-- Caja de Sinopsis Dinámica por Volumen -->
    <div class="synopsis-box">
      <div class="synopsis-header">Sinopsis del Volumen</div>
      <p class="synopsis-text" id="volSynopsis">{initial_synopsis}</p>
    </div>

    <!-- Barra de Selección de Volúmenes Instantánea -->
    <div class="selector-row">
      <button class="nav-btn" onclick="prevVol()">◀ Ant</button>
      <span class="counter" id="volCounter">1 / {total_vols}</span>
      <button class="nav-btn" onclick="nextVol()">Sig ▶</button>
    </div>

    <!-- Botones de Acción Interactivas -->
    <div class="action-row">
      <button class="btn-act btn-read" onclick="triggerRead()">
        📖 Leer Online
      </button>
      <button class="btn-act btn-dl" onclick="triggerDownload()">
        ⬇️ Descargar
      </button>
    </div>
  </div>

  <script>
    const vols = {volumes_json};
    let idx = {current_index};
    const defaultSeriesSynopsis = {_clean_text(clean_series_desc)!r};
    const botName = {bot_username!r};
    const baseWebUrl = {base_web_url!r};

    function renderVolume() {{
      if (!vols.length) return;
      const cur = vols[idx];
      const img = document.getElementById('volCover');
      const ph = document.getElementById('coverPlaceholder');
      const phVol = document.getElementById('phVolNum');

      phVol.innerText = 'Vol. ' + cur.vol_num;

      if (cur.cover) {{
        img.onload = () => {{
          img.style.display = 'block';
          ph.style.display = 'none';
        }};
        img.onerror = () => {{
          img.style.display = 'none';
          ph.style.display = 'flex';
        }};
        img.src = cur.cover;
      }} else {{
        img.style.display = 'none';
        ph.style.display = 'flex';
      }}

      document.getElementById('volTitle').innerText = cur.title || ('Volumen ' + cur.vol_num);
      document.getElementById('volBadge').innerText = '📖 Vol. ' + cur.vol_num;
      document.getElementById('transLabel').innerText = '🌐 ' + cur.translator;
      document.getElementById('volSynopsis').innerText = cur.synopsis || defaultSeriesSynopsis;
      document.getElementById('volCounter').innerText = (idx + 1) + ' / ' + vols.length;
      document.getElementById('colorBadge').style.display = cur.is_color ? 'block' : 'none';

      // Feedback háptico nativo de Telegram al navegar entre volúmenes
      if (window.TelegramWidget && window.TelegramWidget.HapticFeedback) {{
        try {{
          window.TelegramWidget.HapticFeedback.selectionChanged();
        }} catch(e) {{}}
      }}
    }}

    function prevVol() {{
      if (idx > 0) {{
        idx--;
      }} else {{
        idx = vols.length - 1;
      }}
      renderVolume();
    }}

    function nextVol() {{
      if (idx < vols.length - 1) {{
        idx++;
      }} else {{
        idx = 0;
      }}
      renderVolume();
    }}

    function triggerRead() {{
      const cur = vols[idx];
      if (window.TelegramWidget && window.TelegramWidget.HapticFeedback) {{
        try {{
          window.TelegramWidget.HapticFeedback.impactOccurred('medium');
        }} catch(e) {{}}
      }}
      let handled = false;
      try {{
        if (window.TelegramWidget && typeof window.TelegramWidget.request === 'function') {{
          window.TelegramWidget.request(JSON.stringify({{
            action: 'read',
            book_id: cur.id,
            volume: cur.vol_num
          }}));
          handled = true;
        }}
      }} catch(err) {{
        console.warn(err);
      }}

      if (!handled) {{
        const targetUrl = (baseWebUrl || 'https://zp-dev.sp-core.vip').replace(/\\/$/, '') + '/reader?bookId=' + cur.id;
        window.open(targetUrl, '_blank');
      }}
    }}

    function triggerDownload() {{
      const cur = vols[idx];
      if (window.TelegramWidget && window.TelegramWidget.HapticFeedback) {{
        try {{
          window.TelegramWidget.HapticFeedback.impactOccurred('light');
        }} catch(e) {{}}
      }}
      let handled = false;
      try {{
        if (window.TelegramWidget && typeof window.TelegramWidget.request === 'function') {{
          window.TelegramWidget.request(JSON.stringify({{
            action: 'download',
            book_id: cur.id,
            volume: cur.vol_num
          }}));
          handled = true;
        }}
      }} catch(err) {{
        console.warn(err);
      }}

      // Fallback universal a deep link de Telegram si widget_query no está disponible
      if (!handled) {{
        const tgLink = 'tg://resolve?domain=' + botName + '&start=dl_' + cur.id;
        try {{
          window.location.href = tgLink;
        }} catch(e) {{
          window.open('https://t.me/' + botName + '?start=dl_' + cur.id, '_blank');
        }}
      }}
    }}

    // Iniciar renderizado
    renderVolume();
  </script>
</body>
</html>"""
    return html_template


class SeriesCarouselWidgetService:
    """
    Servicio para el despacho y manejo de Widgets HTML de series y volúmenes.
    Diseñado para entorno de Desarrollo (Dev) con fallback resiliente.
    """

    @classmethod
    async def send_widget(
        cls,
        bot_token: str,
        chat_id: int,
        html_content: str,
        message_thread_id: int | None = None,
    ) -> bool:
        """
        Envía un widget HTML mediante el método oficial sendWidget de Telegram Bot API 10.4.
        Retorna True si fue aceptado por Telegram; False si el cliente/API no lo soporta.
        """
        if not bot_token or not chat_id:
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendWidget"
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "html": html_content,
        }
        if message_thread_id:
            payload["message_thread_id"] = message_thread_id

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("ok"):
                        logger.info(
                            f"✅ HTML Widget de serie enviado exitosamente a {chat_id}"
                        )
                        return True

                logger.warning(
                    f"⚠️ sendWidget no disponible o rechazado (status={res.status_code}): {res.text}. "
                    "Activando fallback a Rich Message."
                )
                return False
        except (httpx.HTTPError, OSError, RuntimeError) as e:
            logger.warning(f"Excepción al invocar sendWidget: {e}. Activando fallback.")
            return False

    @classmethod
    async def answer_widget_query(
        cls,
        bot_token: str,
        widget_query_id: str,
        url: str | None = None,
        alert_text: str | None = None,
    ) -> bool:
        """Responde a una consulta de widget (answerWidgetQuery)."""
        api_url = f"https://api.telegram.org/bot{bot_token}/answerWidgetQuery"
        payload: dict[str, Any] = {"widget_query_id": widget_query_id}
        if url:
            payload["url"] = url
        if alert_text:
            payload["alert"] = alert_text

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(api_url, json=payload)
                return res.status_code == 200 and res.json().get("ok", False)
        except (httpx.HTTPError, OSError, RuntimeError) as e:
            logger.error(f"Error respondiendo a widget query {widget_query_id}: {e}")
            return False
