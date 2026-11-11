import json
import logging
from typing import Any

import httpx

logger = logging.getLogger("zeepub.widgets")


def build_series_carousel_widget_html(
    series_title: str,
    author: str,
    description: str,
    volumes: list[dict[str, Any]],
    current_index: int = 0,
    base_web_url: str = "",
) -> str:
    """
    Construye un documento HTML5 autónomo para renderizar un Carrusel de Volúmenes interactivo
    dentro de un mensaje de Telegram mediante Bot API 10.4.
    """
    clean_desc = (
        (description or "Sin descripción disponible.")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    if len(clean_desc) > 300:
        clean_desc = clean_desc[:297] + "..."

    # Sanitizar y preparar los datos de los volúmenes para el script local
    volumes_payload = []
    for idx, v in enumerate(volumes):
        v_title = (
            v.get("titulo")
            or v.get("title")
            or f"Volumen {v.get('vol_display', idx + 1)}"
        )
        cover = v.get("portada") or v.get("coverUrl") or v.get("cover_original") or ""
        if cover and cover.startswith("/") and base_web_url:
            cover = f"{base_web_url.rstrip('/')}{cover}"

        volumes_payload.append(
            {
                "id": str(v.get("id") or v.get("book_hash") or ""),
                "vol_num": str(v.get("vol_display", v.get("volume", idx + 1))),
                "title": v_title,
                "translator": v.get("translator_siglas")
                or v.get("translator")
                or "Oficial",
                "is_color": bool(v.get("color")),
                "cover": cover,
            }
        )

    volumes_json = json.dumps(volumes_payload, ensure_ascii=False)

    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<style>
  :root {{
    --bg-card: rgba(15, 23, 42, 0.85);
    --border: rgba(255, 255, 255, 0.12);
    --primary: #2b6cee;
    --primary-hover: #3b82f6;
    --text-primary: #f8fafc;
    --text-muted: #94a3b8;
    --badge-bg: rgba(43, 108, 238, 0.2);
    --badge-color: #60a5fa;
  }}
  * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
  body {{
    margin: 0;
    padding: 10px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: var(--text-primary);
    background: transparent;
  }}
  .glass-card {{
    background: var(--bg-card);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 14px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
  }}
  .header {{
    display: flex;
    gap: 12px;
    align-items: flex-start;
  }}
  .cover-box {{
    position: relative;
    width: 78px;
    height: 114px;
    flex-shrink: 0;
    border-radius: 10px;
    overflow: hidden;
    background: rgba(0,0,0,0.4);
    box-shadow: 0 4px 14px rgba(0,0,0,0.5);
  }}
  .cover-box img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: opacity 0.2s ease;
  }}
  .color-badge {{
    position: absolute;
    top: 4px;
    right: 4px;
    background: rgba(245, 158, 11, 0.9);
    color: #000;
    font-size: 9px;
    font-weight: 800;
    padding: 2px 4px;
    border-radius: 4px;
  }}
  .info {{
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 114px;
  }}
  .series-title {{
    font-size: 13px;
    font-weight: 700;
    margin: 0;
    line-height: 1.3;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }}
  .author {{
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 2px;
  }}
  .vol-badge {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    margin-top: 4px;
    font-size: 11px;
    font-weight: 600;
    color: var(--badge-color);
    background: var(--badge-bg);
    padding: 2px 8px;
    border-radius: 6px;
    align-self: flex-start;
  }}
  .synopsis {{
    font-size: 10.5px;
    line-height: 1.4;
    color: var(--text-muted);
    margin: 8px 0 0 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }}
  .selector-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 10px;
    padding: 6px 8px;
    background: rgba(255, 255, 255, 0.04);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.05);
  }}
  .nav-btn {{
    background: rgba(255, 255, 255, 0.08);
    border: none;
    color: var(--text-primary);
    font-size: 12px;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.15s;
  }}
  .nav-btn:active {{
    background: rgba(255, 255, 255, 0.2);
  }}
  .counter {{
    font-size: 11px;
    font-weight: 700;
    font-mono: monospace;
    color: var(--text-muted);
  }}
  .action-row {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 10px;
  }}
  .btn-act {{
    padding: 8px 10px;
    border-radius: 10px;
    border: none;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    transition: transform 0.1s, background 0.2s;
  }}
  .btn-act:active {{ transform: scale(0.97); }}
  .btn-read {{
    background: var(--primary);
    color: #ffffff;
  }}
  .btn-read:active {{ background: var(--primary-hover); }}
  .btn-dl {{
    background: rgba(255, 255, 255, 0.08);
    color: var(--text-primary);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }}
</style>
</head>
<body>
  <div class="glass-card">
    <div class="header">
      <div class="cover-box">
        <img id="volCover" src="" alt="Portada" />
        <span id="colorBadge" class="color-badge" style="display: none;">COLOR</span>
      </div>
      <div class="info">
        <div>
          <h2 class="series-title">{series_title}</h2>
          <div class="author">✍️ {author}</div>
          <div class="vol-badge" id="volBadge">📖 Vol. 1</div>
        </div>
        <div style="font-size: 10px; color: var(--text-muted);" id="transLabel">🌐 Fansub</div>
      </div>
    </div>

    <p class="synopsis">{clean_desc}</p>

    <!-- Barra de Selección de Volúmenes Instantánea -->
    <div class="selector-row">
      <button class="nav-btn" onclick="prevVol()">◀ Ant</button>
      <span class="counter" id="volCounter">1 / {len(volumes)}</span>
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

    function renderVolume() {{
      if (!vols.length) return;
      const cur = vols[idx];
      const img = document.getElementById('volCover');
      img.style.opacity = '0.3';
      img.src = cur.cover || 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="80" height="120" fill="%23334155"><rect width="80" height="120"/></svg>';
      img.onload = () => {{ img.style.opacity = '1'; }};

      document.getElementById('volBadge').innerText = '📖 Vol. ' + cur.vol_num;
      document.getElementById('transLabel').innerText = '🌐 ' + cur.translator;
      document.getElementById('volCounter').innerText = (idx + 1) + ' / ' + vols.length;
      document.getElementById('colorBadge').style.display = cur.is_color ? 'block' : 'none';

      // Feedback háptico nativo de Telegram al navegar entre volúmenes
      if (window.TelegramWidget?.HapticFeedback) {{
        window.TelegramWidget.HapticFeedback.selectionChanged();
      }}
    }}

    function prevVol() {{
      if (idx > 0) {{
        idx--;
        renderVolume();
      }} else {{
        idx = vols.length - 1;
        renderVolume();
      }}
    }}

    function nextVol() {{
      if (idx < vols.length - 1) {{
        idx++;
        renderVolume();
      }} else {{
        idx = 0;
        renderVolume();
      }}
    }}

    function triggerRead() {{
      const cur = vols[idx];
      if (window.TelegramWidget?.HapticFeedback) {{
        window.TelegramWidget.HapticFeedback.impactOccurred('medium');
      }}
      if (window.TelegramWidget?.request) {{
        window.TelegramWidget.request(JSON.stringify({{
          action: 'read',
          book_id: cur.id,
          volume: cur.vol_num
        }}));
      }} else {{
        alert('Abriendo lector web para el volumen ' + cur.vol_num);
      }}
    }}

    function triggerDownload() {{
      const cur = vols[idx];
      if (window.TelegramWidget?.HapticFeedback) {{
        window.TelegramWidget.HapticFeedback.impactOccurred('light');
      }}
      if (window.TelegramWidget?.request) {{
        window.TelegramWidget.request(JSON.stringify({{
          action: 'download',
          book_id: cur.id,
          volume: cur.vol_num
        }}));
      }} else {{
        alert('Descargando volumen ' + cur.vol_num);
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
        payload = {
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
