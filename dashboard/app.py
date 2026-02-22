import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="ZeePub Observatory",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stMetric {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.05));
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
    }
    .stMetric label {
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #9ca3af !important;
    }
    .stMetric value {
        font-size: 1.5rem !important;
        font-weight: 700;
    }
    .glass-card {
        background: rgba(30, 30, 40, 0.6);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 1.5rem;
    }
    .status-pending { color: #fbbf24; }
    .status-sent { color: #34d399; }
    .status-failed { color: #f87171; }
    .status-publishing { color: #60a5fa; }
    div[data-testid="stSidebarNav"] { display: none; }
</style>
""",
    unsafe_allow_html=True,
)


def get_db_url():
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        st.error("DATABASE_URL no configurada")
        return None
    if "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "")
    if "@db:" in db_url and os.name == "nt":
        db_url = db_url.replace("@db:", "@localhost:")
    return db_url


@st.cache_resource
def get_engine():
    db_url = get_db_url()
    if not db_url:
        return None
    return create_engine(db_url, pool_pre_ping=True, pool_size=5)


def fetch_df(query: str, params: dict = None):
    engine = get_engine()
    if not engine:
        return pd.DataFrame()
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params or {})
    except Exception as e:
        st.error(f"Error de BD: {e}")
        return pd.DataFrame()


def fetch_scalar(query: str, params: dict = None):
    engine = get_engine()
    if not engine:
        return 0
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            row = result.fetchone()
            return row[0] if row else 0
    except Exception:
        return 0


def render_sidebar():
    with st.sidebar:
        st.markdown("### 📚 ZeePub Observatory")
        st.markdown("---")
        st.markdown("**Sistema de Observabilidad**")
        st.markdown("Capa 4 - Monitoreo Centralizado")
        st.markdown("---")

        refresh = st.button("🔄 Actualizar", use_container_width=True)
        if refresh:
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.markdown(f"⏰ Última actualización: `{datetime.now().strftime('%H:%M:%S')}`")

        st.markdown("---")
        st.markdown("### 📊 Vistas")
        view = st.radio(
            "Seleccionar", ["Resumen", "Ejecuciones", "Publicaciones", "Métricas"], label_visibility="collapsed"
        )
        return view


def render_overview():
    st.markdown("## 🎯 Panel de Control")
    st.markdown("Resumen general del sistema ZeePub")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_books = fetch_scalar("SELECT COUNT(*) FROM local_books")
        st.metric("📚 Libros", f"{total_books:,}")

    with col2:
        total_users = fetch_scalar("SELECT COUNT(*) FROM users")
        st.metric("👥 Usuarios", f"{total_users:,}")

    with col3:
        today_downloads = fetch_scalar("""
            SELECT COUNT(*) FROM download_history 
            WHERE downloaded_at >= CURRENT_DATE
        """)
        st.metric("⬇️ Descargas Hoy", f"{today_downloads:,}")

    with col4:
        pending_pubs = fetch_scalar("""
            SELECT COUNT(*) FROM publication_queue 
            WHERE status = 'pending'
        """)
        st.metric("📤 Publicaciones Pendientes", f"{pending_pubs:,}")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 📈 Actividad (Últimos 7 días)")
        df_activity = fetch_df("""
            SELECT 
                DATE(downloaded_at) as fecha,
                COUNT(*) as descargas
            FROM download_history
            WHERE downloaded_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(downloaded_at)
            ORDER BY fecha
        """)

        if not df_activity.empty:
            fig = px.bar(
                df_activity,
                x="fecha",
                y="descargas",
                color_discrete_sequence=["#6366f1"],
                labels={"fecha": "Fecha", "descargas": "Descargas"},
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#9ca3af"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos de actividad")

    with col_right:
        st.markdown("### 👥 Distribución de Usuarios")
        df_levels = fetch_df("""
            SELECT 
                COALESCE(ul.name, 'Sin nivel') as nivel,
                COUNT(u.id) as usuarios
            FROM users u
            LEFT JOIN user_levels ul ON u.level_id = ul.id
            GROUP BY ul.name
            ORDER BY usuarios DESC
        """)

        if not df_levels.empty:
            fig = px.pie(
                df_levels, values="usuarios", names="nivel", color_discrete_sequence=px.colors.sequential.Indigo
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#9ca3af"),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos de usuarios")


def render_executions():
    st.markdown("## 🤖 Ejecuciones de Agente")
    st.markdown("Logs de operaciones ejecutadas por el sistema")

    col1, col2 = st.columns([3, 1])
    with col1:
        hours = st.slider("Mostrar últimas horas", 1, 72, 24)
    with col2:
        status_filter = st.selectbox("Estado", ["Todos", "success", "error"], label_visibility="visible")

    query = """
        SELECT 
            id,
            timestamp,
            func_name,
            status,
            duration,
            error,
            metadata_json
        FROM agent_executions
        WHERE timestamp >= NOW() - INTERVAL :hours_str
    """
    params = {"hours_str": f"{hours} hours"}

    if status_filter != "Todos":
        query += " AND status = :status"
        params["status"] = status_filter

    query += " ORDER BY timestamp DESC LIMIT 200"

    df = fetch_df(query, params)

    if df.empty:
        st.warning("No hay ejecuciones registradas en el período seleccionado")
        return

    st.markdown(f"**{len(df)} ejecuciones encontradas**")

    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        success_count = len(df[df["status"] == "success"])
        st.metric("✅ Exitosas", success_count)
    with col_stat2:
        error_count = len(df[df["status"] == "error"])
        st.metric("❌ Errores", error_count)
    with col_stat3:
        avg_duration = df["duration"].mean()
        st.metric("⏱️ Duración Promedio", f"{avg_duration:.2f}s" if pd.notna(avg_duration) else "N/A")

    df_display = df.copy()
    df_display["timestamp"] = pd.to_datetime(df_display["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    df_display["duration"] = df_display["duration"].apply(lambda x: f"{x:.2f}s" if pd.notna(x) else "-")

    st.dataframe(
        df_display[["timestamp", "func_name", "status", "duration", "error"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "timestamp": "Fecha/Hora",
            "func_name": "Función",
            "status": "Estado",
            "duration": "Duración",
            "error": "Error",
        },
    )


def render_publications():
    st.markdown("## 📤 Sistema de Publicaciones")
    st.markdown("Estado de la cola de publicación y canales")

    tab1, tab2, tab3 = st.tabs(["Cola de Publicación", "Canales", "Plantillas"])

    with tab1:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            pending = fetch_scalar("SELECT COUNT(*) FROM publication_queue WHERE status = 'pending'")
            st.metric("⏳ Pendientes", pending)
        with col2:
            publishing = fetch_scalar("SELECT COUNT(*) FROM publication_queue WHERE status = 'publishing'")
            st.metric("📤 Publicando", publishing)
        with col3:
            sent = fetch_scalar("SELECT COUNT(*) FROM publication_queue WHERE status = 'sent'")
            st.metric("✅ Enviados", sent)
        with col4:
            failed = fetch_scalar("SELECT COUNT(*) FROM publication_queue WHERE status = 'failed'")
            st.metric("❌ Fallidos", failed)

        st.markdown("### Últimas Publicaciones")
        df_queue = fetch_df("""
            SELECT 
                pq.id,
                pq.book_hash,
                pc.name as canal,
                pc.platform,
                pq.scheduled_for,
                pq.status,
                pq.published_at,
                pq.error_message
            FROM publication_queue pq
            LEFT JOIN publication_channels pc ON pq.channel_id = pc.id
            ORDER BY pq.scheduled_for DESC
            LIMIT 50
        """)

        if not df_queue.empty:
            df_queue["scheduled_for"] = pd.to_datetime(df_queue["scheduled_for"]).dt.strftime("%Y-%m-%d %H:%M")
            df_queue["published_at"] = pd.to_datetime(df_queue["published_at"]).dt.strftime("%Y-%m-%d %H:%M")

            st.dataframe(
                df_queue,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "ID",
                    "book_hash": "Hash del Libro",
                    "canal": "Canal",
                    "platform": "Plataforma",
                    "scheduled_for": "Programado",
                    "status": "Estado",
                    "published_at": "Publicado",
                    "error_message": "Error",
                },
            )
        else:
            st.info("No hay publicaciones en la cola")

    with tab2:
        df_channels = fetch_df("""
            SELECT 
                id, name, platform, target_id, is_active, is_favorite, created_at
            FROM publication_channels
            ORDER BY is_favorite DESC, name ASC
        """)

        if not df_channels.empty:
            st.dataframe(
                df_channels,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "ID",
                    "name": "Nombre",
                    "platform": "Plataforma",
                    "target_id": "Target ID",
                    "is_active": "Activo",
                    "is_favorite": "Favorito",
                    "created_at": "Creado",
                },
            )
        else:
            st.info("No hay canales configurados")

        st.markdown("### Chats Descubiertos")
        df_discovered = fetch_df("""
            SELECT chat_id, title, type, member_count, last_seen_at
            FROM discovered_chats
            ORDER BY last_seen_at DESC
            LIMIT 20
        """)

        if not df_discovered.empty:
            st.dataframe(df_discovered, use_container_width=True, hide_index=True)
        else:
            st.info("No hay chats descubiertos")

    with tab3:
        df_templates = fetch_df("""
            SELECT id, name, platform, created_at
            FROM publication_templates
            ORDER BY created_at DESC
        """)

        if not df_templates.empty:
            st.dataframe(
                df_templates,
                use_container_width=True,
                hide_index=True,
                column_config={"id": "ID", "name": "Nombre", "platform": "Plataforma", "created_at": "Creado"},
            )
        else:
            st.info("No hay plantillas configuradas")


def render_metrics():
    st.markdown("## 📊 Métricas del Sistema")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📚 Biblioteca")

        total_books = fetch_scalar("SELECT COUNT(*) FROM local_books")
        total_series = fetch_scalar("SELECT COUNT(*) FROM series_metadata")
        total_ratings = fetch_scalar("SELECT COUNT(*) FROM user_ratings")
        avg_rating = fetch_scalar("SELECT AVG(rating) FROM user_ratings")

        c1, c2 = st.columns(2)
        c1.metric("Total Libros", f"{total_books:,}")
        c2.metric("Total Series", f"{total_series:,}")
        c1.metric("Valoraciones", f"{total_ratings:,}")
        c2.metric("Rating Promedio", f"{avg_rating:.1f}" if avg_rating else "N/A")

    with col2:
        st.markdown("### ⬇️ Descargas")

        total_downloads = fetch_scalar("SELECT COUNT(*) FROM download_history")
        today_downloads = fetch_scalar("SELECT COUNT(*) FROM download_history WHERE downloaded_at >= CURRENT_DATE")
        week_downloads = fetch_scalar("""
            SELECT COUNT(*) FROM download_history 
            WHERE downloaded_at >= CURRENT_DATE - INTERVAL '7 days'
        """)

        c1, c2 = st.columns(2)
        c1.metric("Total Histórico", f"{total_downloads:,}")
        c2.metric("Hoy", f"{today_downloads:,}")
        c1.metric("Última Semana", f"{week_downloads:,}")

    st.markdown("---")

    st.markdown("### 📈 Tendencia de Descargas (30 días)")
    df_trend = fetch_df("""
        SELECT 
            DATE(downloaded_at) as fecha,
            COUNT(*) as descargas
        FROM download_history
        WHERE downloaded_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE(downloaded_at)
        ORDER BY fecha
    """)

    if not df_trend.empty:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df_trend["fecha"],
                y=df_trend["descargas"],
                mode="lines+markers",
                name="Descargas",
                line=dict(color="#6366f1", width=2),
                marker=dict(size=6),
                fill="tozeroy",
                fillcolor="rgba(99, 102, 241, 0.1)",
            )
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9ca3af"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos suficientes para mostrar tendencia")

    st.markdown("### 🏆 Top 10 Libros Más Descargados")
    df_top = fetch_df("""
        SELECT 
            COALESCE(lb.title, dh.title, 'Desconocido') as titulo,
            COUNT(*) as descargas
        FROM download_history dh
        LEFT JOIN local_books lb ON dh.book_hash = lb.book_hash
        GROUP BY COALESCE(lb.title, dh.title)
        ORDER BY descargas DESC
        LIMIT 10
    """)

    if not df_top.empty:
        fig = px.bar(df_top, x="descargas", y="titulo", orientation="h", color_discrete_sequence=["#8b5cf6"])
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9ca3af"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            height=400,
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos de descargas")


def main():
    st.markdown(
        """
    <div style="text-align: center; padding: 1rem 0;">
        <h1 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 0;">
            🛰️ ZeePub <span style="color: #6366f1;">Observatory</span>
        </h1>
        <p style="color: #6b7280; font-size: 0.9rem;">
            Dashboard de Observabilidad • Capa 4
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    view = render_sidebar()

    if view == "Resumen":
        render_overview()
    elif view == "Ejecuciones":
        render_executions()
    elif view == "Publicaciones":
        render_publications()
    elif view == "Métricas":
        render_metrics()


if __name__ == "__main__":
    main()
