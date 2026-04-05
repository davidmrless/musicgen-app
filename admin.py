import streamlit as st
import pandas as pd
from database import get_all_stats


def show_admin_panel() -> None:
    """Panel de control para administradores: métricas y log de generaciones."""

    # ── Botón de regreso ──────────────────────────────────────────────────
    if st.button("◀ Volver a la App", use_container_width=False):
        st.session_state["show_admin"] = False
        st.rerun()

    st.title("Panel de Control")
    st.divider()

    # ── Carga de datos ────────────────────────────────────────────────────
    stats = get_all_stats()

    if not stats:
        st.info("Aún no hay generaciones registradas.")
        return

    # ── Construcción del DataFrame ────────────────────────────────────────
    df = pd.DataFrame(stats)

    # Supabase devuelve el join como dict anidado en la columna "users"
    df["username"] = df["users"].apply(
        lambda u: u.get("username", "—") if isinstance(u, dict) else "—"
    )

    # ── Métricas resumen ──────────────────────────────────────────────────
    total_songs = len(df)
    total_cost  = round(df["replicate_cost_usd"].sum(), 4)

    col1, col2 = st.columns(2)
    col1.metric("🎵 Canciones generadas", total_songs)
    col2.metric("💰 Costo total estimado", f"${total_cost} USD")

    st.divider()

    # ── Tabla de generaciones ─────────────────────────────────────────────
    st.subheader("📋 Registro de generaciones")
    st.dataframe(
        df[["username", "prompt_text", "replicate_cost_usd", "success", "created_at"]],
        use_container_width=True,
    )