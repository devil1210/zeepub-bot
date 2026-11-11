# services/widgets/series_carousel_widget.py
"""
Servicio para la generación y despacho de Widgets HTML interactivos (Telegram Bot API 10.4).
Proporciona Carruseles de Volúmenes enriquecidos, renderizados dentro del chat mediante QuickJS.
Utiliza adjuntos multipart (attachment://cover_{i}) para entrega instantánea de portadas locales.
"""

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


def _find_cover_file_on_disk(v: dict[str, Any]) -> str | None:
    """Localiza el archivo de portada en el almacenamiento local."""
    from utils.library_db import COVERS_DIR, THUMBNAILS_DIR

    book_id = str(v.get("id") or v.get("book_hash") or "")
    candidates: list[str] = []
    for key in ["cover_medium", "cover_high", "cover_low", "cover_original", "portada", "coverUrl"]:
        val = v.get(key)
        if val and isinstance(val, str):
            candidates.append(os.path.basename(val))

    if book_id:
        candidates.extend([
            f"{book_id}_medium.jpg",
            f"{book_id}_high.jpg",
            f"{book_id}.jpg",
            f"{book_id}_low.jpg",
        ])

    search_dirs = [d for d in [THUMBNAILS_DIR, COVERS_DIR] if os.path.exists(d)]
    for target_dir in search_dirs:
        for cand in candidates:
            cand_path = os.path.join(target_dir, cand)
            if os.path.isfile(cand_path):
                return cand_path

    return None


def _render_widget_html(
    series_title: str,
    author: str,
    first_vol: dict[str, Any],
    total_vols: int,
    vols_json: str,
    bot_username: str,
    base_web_url: str,
) -> str:
    """Genera la plantilla HTML5 optimizada (<10 KB) para Telegram HTML Widgets."""
    first_cover = first_vol.get("cover") or ""
    css = """:root{--bg:rgba(15,23,42,0.96);--bd:rgba(255,255,255,0.12);--txt:#f8fafc;--mut:#94a3b8;--bdgc:#60a5fa}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;padding:6px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:var(--txt);background:transparent}
.card{background:var(--bg);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid var(--bd);border-radius:18px;padding:14px;box-shadow:0 12px 36px rgba(0,0,0,0.5);display:flex;flex-direction:column;gap:12px;min-height:460px}
.hdr{display:flex;gap:14px;align-items:stretch}
.cov-bx{position:relative;width:125px;height:185px;flex-shrink:0;border-radius:12px;overflow:hidden;background:linear-gradient(135deg,#1e293b,#0f172a);box-shadow:0 8px 24px rgba(0,0,0,0.6);border:1px solid rgba(255,255,255,0.14)}
.cov-bx img{width:100%;height:100%;object-fit:cover;display:block}
.cov-ph{width:100%;height:100%;display:none;flex-direction:column;align-items:center;justify-content:center;gap:6px}
.ph-ic{font-size:34px}.ph-vl{font-size:12px;font-weight:700;color:var(--mut)}
.c-bdg{position:absolute;top:6px;right:6px;background:rgba(245,158,11,0.95);color:#000;font-size:9px;font-weight:800;padding:2px 6px;border-radius:4px;display:none}
.info{flex:1;min-width:0;display:flex;flex-direction:column;justify-content:space-between;padding:2px 0}
.s-ttl{font-size:15px;font-weight:700;margin:0;line-height:1.3;color:#fff;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.v-ttl{font-size:13px;font-weight:600;color:var(--bdgc);margin-top:6px;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.auth{font-size:12px;color:var(--mut);margin-top:4px}
.bdgs{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.badge{display:inline-flex;align-items:center;font-size:11px;font-weight:600;padding:4px 8px;border-radius:6px}
.b-vol{color:var(--bdgc);background:rgba(37,99,235,0.22);border:1px solid rgba(59,130,246,0.25)}
.b-tr{background:rgba(255,255,255,0.08);color:#cbd5e1;border:1px solid rgba(255,255,255,0.06)}
.syn-bx{padding:12px 14px;background:rgba(255,255,255,0.04);border-radius:12px;border:1px solid rgba(255,255,255,0.06)}
.syn-hdr{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:#64748b;margin-bottom:6px}
.syn-txt{font-size:12.5px;line-height:1.55;color:#cbd5e1;margin:0;min-height:75px;max-height:130px;overflow-y:auto;display:block}
.sel-rw{display:flex;align-items:center;justify-content:space-between;padding:8px 12px;background:rgba(255,255,255,0.05);border-radius:12px;border:1px solid rgba(255,255,255,0.06)}
.n-btn{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.1);color:var(--txt);font-size:13px;font-weight:600;padding:8px 16px;border-radius:8px;cursor:pointer}
.ctr{font-size:12.5px;font-weight:700;font-family:monospace;color:var(--mut)}
.act-rw{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.btn{padding:12px 14px;border-radius:12px;border:none;font-size:13.5px;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;min-height:44px}
.b-rd{background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;border:1px solid rgba(96,165,250,0.3);box-shadow:0 4px 12px rgba(37,99,235,0.3)}
.b-dl{background:rgba(255,255,255,0.08);color:var(--txt);border:1px solid rgba(255,255,255,0.12)}"""

    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><style>{css}</style></head>
<body><div class="card">
<div class="hdr">
  <div class="cov-bx">
    <div id="covPh" class="cov-ph"><span class="ph-ic">📖</span><span id="phVl" class="ph-vl">Vol. {first_vol.get('vol_num', 1)}</span></div>
    <img id="volCov" src="{first_cover}" alt="" />
    <span id="colBdg" class="c-bdg">COLOR</span>
  </div>
  <div class="info">
    <div>
      <h2 class="s-ttl">{series_title}</h2>
      <div id="vTtl" class="v-ttl">{first_vol.get('title', '')}</div>
      <div class="auth">✍️ {author}</div>
    </div>
    <div class="bdgs">
      <span id="vBdg" class="badge b-vol">📖 Vol. {first_vol.get('vol_num', 1)}</span>
      <span id="trLbl" class="badge b-tr">🌐 {first_vol.get('translator', 'Oficial')}</span>
    </div>
  </div>
</div>
<div class="syn-bx">
  <div class="syn-hdr">Sinopsis del Volumen</div>
  <p id="vSyn" class="syn-txt">{first_vol.get('synopsis', '')}</p>
</div>
<div class="sel-rw">
  <button class="n-btn" onclick="prev()">◀ Ant</button>
  <span id="vCtr" class="ctr">1 / {total_vols}</span>
  <button class="n-btn" onclick="next()">Sig ▶</button>
</div>
<div class="act-rw">
  <button class="btn b-rd" onclick="read()">📖 Leer Online</button>
  <button class="btn b-dl" onclick="dl()">⬇️ Descargar</button>
</div>
</div>
<script>
const vols={vols_json};let idx=0;const bot={bot_username!r};const web={base_web_url!r};
function ren(){{
  if(!vols.length)return;const c=vols[idx];
  const im=document.getElementById('volCov'),ph=document.getElementById('covPh');
  document.getElementById('phVl').innerText='Vol. '+c.vol_num;
  if(c.cover){{im.style.display='block';ph.style.display='none';im.src=c.cover;}}else{{im.style.display='none';ph.style.display='flex';}}
  document.getElementById('vTtl').innerText=c.title||('Volumen '+c.vol_num);
  document.getElementById('vBdg').innerText='📖 Vol. '+c.vol_num;
  document.getElementById('trLbl').innerText='🌐 '+c.translator;
  document.getElementById('vSyn').innerText=c.synopsis;
  document.getElementById('vCtr').innerText=(idx+1)+' / '+vols.length;
  document.getElementById('colBdg').style.display=c.is_color?'block':'none';
  if(window.TelegramWidget&&window.TelegramWidget.HapticFeedback){{try{{window.TelegramWidget.HapticFeedback.selectionChanged();}}catch(e){{}}}}
}}
function prev(){{idx=(idx>0)?(idx-1):(vols.length-1);ren();}}
function next(){{idx=(idx<vols.length-1)?(idx+1):0;ren();}}
function read(){{
  const c=vols[idx];
  if(window.TelegramWidget&&window.TelegramWidget.HapticFeedback){{try{{window.TelegramWidget.HapticFeedback.impactOccurred('medium');}}catch(e){{}}}}
  let h=false;
  try{{if(window.TelegramWidget&&typeof window.TelegramWidget.request==='function'){{window.TelegramWidget.request(JSON.stringify({{action:'read',book_id:c.id,volume:c.vol_num}}));h=true;}}}}catch(e){{}}
  if(!h){{window.open(web.replace(/\\/$/,'')+'/reader?bookId='+c.id,'_blank');}}
}}
function dl(){{
  const c=vols[idx];
  if(window.TelegramWidget&&window.TelegramWidget.HapticFeedback){{try{{window.TelegramWidget.HapticFeedback.impactOccurred('light');}}catch(e){{}}}}
  let h=false;
  try{{if(window.TelegramWidget&&typeof window.TelegramWidget.request==='function'){{window.TelegramWidget.request(JSON.stringify({{action:'download',book_id:c.id,volume:c.vol_num}}));h=true;}}}}catch(e){{}}
  if(!h){{try{{window.location.href='tg://resolve?domain='+bot+'&start=dl_'+c.id;}}catch(e){{window.open('https://t.me/'+bot+'?start=dl_'+c.id,'_blank');}}}}
}}
</script></body></html>"""


def prepare_carousel_payload(
    series_title: str,
    author: str,
    description: str,
    volumes: list[dict[str, Any]],
    base_web_url: str = "",
) -> tuple[str, dict[str, Any]]:
    """
    Construye el HTML y el diccionario de archivos multipart (attachments) para el widget.
    Retorna (html, files_dict).
    """
    clean_series_desc = _clean_text(description) or "Sin descripción disponible."
    bot_username = getattr(config, "BOT_USERNAME", "") or "spcore_bot"

    files: dict[str, Any] = {}
    volumes_payload: list[dict[str, Any]] = []

    for idx, v in enumerate(volumes):
        v_title = v.get("titulo") or v.get("title") or f"Volumen {v.get('vol_display', v.get('volume', idx + 1))}"
        if len(v_title) > 35:
            v_title = v_title[:32] + "..."

        vol_desc_raw = v.get("description")
        v_syn = _clean_text(vol_desc_raw) if vol_desc_raw else clean_series_desc
        if len(v_syn) > 85:
            v_syn = v_syn[:82] + "..."

        cover_ref = ""
        cover_file = _find_cover_file_on_disk(v)
        if cover_file:
            attach_key = f"cover_{idx}"
            try:
                with open(cover_file, "rb") as fh:
                    files[attach_key] = (f"{attach_key}.jpg", fh.read(), "image/jpeg")
                cover_ref = f"attachment://{attach_key}"
            except OSError as e:
                logger.debug(f"No se pudo leer carátula {cover_file}: {e}")

        volumes_payload.append({
            "id": str(v.get("id") or v.get("book_hash") or ""),
            "vol_num": str(v.get("vol_display", v.get("volume", idx + 1))),
            "title": v_title,
            "translator": (v.get("translator_siglas") or v.get("translator") or "Oficial")[:10],
            "is_color": bool(v.get("color")),
            "cover": cover_ref,
            "synopsis": v_syn,
        })

    vols_json = json.dumps(volumes_payload, ensure_ascii=False)
    first_vol = volumes_payload[0] if volumes_payload else {}
    total_vols = len(volumes_payload)

    html = _render_widget_html(
        series_title=series_title,
        author=author,
        first_vol=first_vol,
        total_vols=total_vols,
        vols_json=vols_json,
        bot_username=bot_username,
        base_web_url=base_web_url or "https://zp-dev.sp-core.vip",
    )

    return html, files


def build_series_carousel_widget_html(
    series_title: str,
    author: str,
    description: str,
    volumes: list[dict[str, Any]],
    current_index: int = 0,
    base_web_url: str = "",
) -> str:
    """Función de compatibilidad para generar el HTML autónomo del carrusel."""
    html, _ = prepare_carousel_payload(
        series_title=series_title,
        author=author,
        description=description,
        volumes=volumes,
        base_web_url=base_web_url,
    )
    return html


class SeriesCarouselWidgetService:
    """
    Servicio para el despacho y manejo de Widgets HTML de series y volúmenes.
    Diseñado para entorno de Desarrollo (Dev) con soporte para multipart attachments.
    """

    @classmethod
    async def send_carousel_widget(
        cls,
        bot_token: str,
        chat_id: int,
        series_title: str,
        author: str,
        description: str,
        volumes: list[dict[str, Any]],
        base_web_url: str = "",
        message_thread_id: int | None = None,
    ) -> bool:
        """
        Genera y envía el carrusel interactivo completo adjuntando las portadas como archivos multipart.
        Garantiza fallback resiliente si el cliente no soporta widgets.
        """
        html, files = prepare_carousel_payload(
            series_title=series_title,
            author=author,
            description=description,
            volumes=volumes,
            base_web_url=base_web_url,
        )

        return await cls.send_widget(
            bot_token=bot_token,
            chat_id=chat_id,
            html_content=html,
            files=files,
            message_thread_id=message_thread_id,
        )

    @classmethod
    async def send_widget(
        cls,
        bot_token: str,
        chat_id: int,
        html_content: str,
        files: dict[str, Any] | None = None,
        message_thread_id: int | None = None,
    ) -> bool:
        """
        Envía un widget HTML mediante el método oficial sendWidget de Telegram Bot API 10.4.
        Soporta envío JSON directo o multipart form-data con adjuntos.
        """
        if not bot_token or not chat_id:
            return False

        payload_bytes = len(html_content.encode("utf-8"))
        files_count = len(files) if files else 0
        logger.info(
            f"Enviando sendWidget a {chat_id} (HTML: {payload_bytes} bytes, archivos: {files_count})"
        )

        url = f"https://api.telegram.org/bot{bot_token}/sendWidget"
        data: dict[str, Any] = {
            "chat_id": chat_id,
            "html": html_content,
        }
        if message_thread_id:
            data["message_thread_id"] = message_thread_id

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                if files:
                    res = await client.post(url, data=data, files=files)
                else:
                    res = await client.post(url, json=data)

                if res.status_code == 200:
                    body = res.json()
                    if body.get("ok"):
                        logger.info(f"✅ HTML Widget de serie enviado exitosamente a {chat_id}")
                        return True

                logger.warning(
                    f"⚠️ sendWidget rechazado (status={res.status_code}): {res.text}. "
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
