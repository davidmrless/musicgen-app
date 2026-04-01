import io
import requests
from datetime import datetime
import soundfile as sf
import streamlit as st
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder
from auth import login_user, register_user
from admin import show_admin_panel
from audio_processing import process_audio, trim_audio, get_audio_duration
from music_analysis import get_bpm, get_pitch_curve, create_piano_roll_chart
from database import log_generation, update_credits
from replicate_client import generate_music

# ---------------------------------------------------------------------------
# 1. Carga de variables de entorno
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# 2. Configuración de la página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="🎵 MelodyGen",
    page_icon="🎵",
    layout="wide",
)

# ---------------------------------------------------------------------------
# 3. Inicialización del estado de sesión
# ---------------------------------------------------------------------------
DEFAULTS = {
    "logged_in": False,
    "user_id": None,
    "username": None,
    "is_admin": False,
    "credits": 0,
    "show_admin": False,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------------------------------------------------------------------
# 4. Página de autenticación
# ---------------------------------------------------------------------------

def show_auth_page():
    # Encabezado centrado
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem 0 1rem'>
            <h1>🎵 MelodyGen</h1>
            <p style='color: gray; font-size: 1.1rem;'>
                Genera música original con IA a partir de texto o una melodía de referencia.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, col, _ = st.columns([1, 1.4, 1])

    with col:
        tab_login, tab_register = st.tabs(["Iniciar Sesión", "Registrarse"])

        # ── Tab: Login ────────────────────────────────────────────────────
        with tab_login:
            with st.form("form_login"):
                username = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                submitted = st.form_submit_button("Entrar", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Por favor completa todos los campos.")
                else:
                    success, user, msg = login_user(username, password)
                    if success:
                        st.session_state["logged_in"] = True
                        st.session_state["user_id"]   = user["id"]
                        st.session_state["username"]  = user["username"]
                        st.session_state["is_admin"]  = user["is_admin"]
                        st.session_state["credits"]   = user["credits_used_today"]
                        st.rerun()
                    else:
                        st.error(msg)

        # ── Tab: Registro ─────────────────────────────────────────────────
        with tab_register:
            with st.form("form_register"):
                new_username    = st.text_input("Usuario")
                new_email       = st.text_input("Correo electrónico")
                new_password    = st.text_input("Contraseña", type="password")
                confirm_password = st.text_input("Confirmar contraseña", type="password")
                invite_code     = st.text_input("Código de invitación")
                submitted_reg   = st.form_submit_button("Crear cuenta", use_container_width=True)

            if submitted_reg:
                if not all([new_username, new_email, new_password, confirm_password, invite_code]):
                    st.error("Por favor completa todos los campos.")
                elif new_password != confirm_password:
                    st.error("Las contraseñas no coinciden.")
                else:
                    success, msg = register_user(new_username, new_email, new_password, invite_code)
                    if success:
                        st.success(f"{msg} Ya puedes iniciar sesión.")
                    else:
                        st.error(msg)


# ---------------------------------------------------------------------------
# 5. App principal
# ---------------------------------------------------------------------------

CREDIT_LIMIT = 3  # Máximo de generaciones por día por usuario


def _build_sidebar():
    """Renderiza el sidebar de navegación y gestión de sesión."""
    with st.sidebar:
        st.markdown("## 🎵 MelodyGen")
        st.markdown(f"### Hola, **{st.session_state['username']}** 👋")
        st.divider()

        # ── Métricas de créditos ─────────────────────────────────────────────────
        is_admin  = st.session_state.get("is_admin", False)
        used      = st.session_state["credits"]
        remaining = "∞" if is_admin else max(0, CREDIT_LIMIT - used)
        col1, col2 = st.columns(2)
        col1.metric("Usados hoy",  used)
        col2.metric("Disponibles", remaining)

        st.divider()

        # ── Panel de administrador (solo admins) ──────────────────────────
        if st.session_state["is_admin"]:
            if st.button("🛠️ Panel Admin", use_container_width=True):
                st.session_state["show_admin"] = True
            if st.session_state["show_admin"]:
                if st.button("◀ Volver al generador", use_container_width=True):
                    st.session_state["show_admin"] = False
            st.divider()

        # ── Cerrar sesión ─────────────────────────────────────────────────
        if st.button("🚪 Cerrar sesión", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def show_generation_flow():
    """Flujo principal: prompt de texto primero, melodía de referencia opcional."""
    st.title("🎵 Generador de Música")
    st.markdown("Describe el estilo musical que quieres crear. Subir una melodía de referencia es *opcional*.")

    # ── 1. Prompt de texto (elemento principal) ───────────────────────────
    st.text_area(
        "✍️ Describe el sonido que buscas",
        placeholder=(
            "Ejemplos:\n"
            "\u2022 Lo-fi hip hop con piano suave y lluvia de fondo\n"
            "\u2022 Ambient electrónico oscuro con sintetizadores evocadores\n"
            "\u2022 Jazz acelerado estilo bebop con trompeta prominente"
        ),
        key="prompt_text",
        height=120,
    )

    st.divider()

    # ── 2. Melodía de referencia (opcional) ──────────────────────────────
    audio_to_send: bytes | None = None

    with st.expander("🎵 Añadir melodía de referencia (Opcional)", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📂 Subir archivo**")
            uploaded = st.file_uploader(
                "Sube tu archivo de audio",
                type=["wav", "mp3", "m4a", "ogg"],
                help="Formatos soportados: WAV, MP3, M4A, OGG",
                label_visibility="collapsed",
            )

        with col2:
            st.markdown("**🎤 Grabar ahora**")
            recorded_bytes = audio_recorder(
                text="Clic para grabar/detener",
                icon_size="2x",
            )

        # ── Elegir fuente: archivo tiene prioridad ────────────────────────
        if uploaded is not None:
            raw_audio_bytes = uploaded.read()
            file_id = uploaded.name + str(uploaded.size)
        elif recorded_bytes is not None:
            raw_audio_bytes = recorded_bytes
            file_id = "rec_" + str(len(recorded_bytes))
        else:
            raw_audio_bytes = None
            file_id = None

        if raw_audio_bytes is not None:
            # ── Procesar solo si cambió la fuente ─────────────────────────
            if st.session_state.get("_last_file_id") != file_id:
                with st.spinner("🔄 Procesando audio…"):
                    wav_bytes, audio, sr = process_audio(raw_audio_bytes)

                if audio is None:
                    st.error("❌ No se pudo procesar el audio. Verifica el formato e inténtalo de nuevo.")
                else:
                    st.session_state["wav_bytes"]      = wav_bytes
                    st.session_state["audio_array"]   = audio
                    st.session_state["sample_rate"]   = sr
                    st.session_state["_last_file_id"] = file_id

            if st.session_state.get("audio_array") is not None:
                audio = st.session_state["audio_array"]
                sr    = st.session_state["sample_rate"]

                # ── Reproductor ───────────────────────────────────────────
                st.markdown("#### 🔊 Audio procesado")
                st.audio(st.session_state["wav_bytes"], format="audio/wav")

                # ── Duración y BPM ────────────────────────────────────────
                duration = get_audio_duration(audio, sr)
                bpm      = get_bpm(audio, sr)
                col_dur, col_bpm = st.columns(2)
                col_dur.metric("⏱️ Duración", f"{duration:.1f} s")
                col_bpm.metric("🥁 BPM detectado", bpm if bpm else "N/A")

                # ── Slider de recorte ─────────────────────────────────────
                if duration > 30:
                    start_sec = st.slider(
                        "Selecciona el inicio del fragmento (segundos)",
                        min_value=0.0,
                        max_value=float(int(duration - 30)),
                        value=float(st.session_state.get("start_sec", 0)),
                        step=1.0,
                        format="%.0f s",
                    )
                else:
                    start_sec = 0.0
                st.session_state["start_sec"] = start_sec

                # ── Análisis de melodía ───────────────────────────────────
                if st.button("🎹 Analizar melodía", use_container_width=False):
                    with st.spinner("🔍 Extrayendo pitch…"):
                        times, freqs, notes = get_pitch_curve(audio, sr)
                    if times is not None:
                        st.session_state["pitch_times"] = times
                        st.session_state["pitch_freqs"] = freqs
                        st.session_state["pitch_notes"] = notes
                    else:
                        st.warning("⚠️ No se pudo extraer el pitch del audio.")

                if st.session_state.get("pitch_times") is not None:
                    fig = create_piano_roll_chart(
                        st.session_state["pitch_times"],
                        st.session_state["pitch_freqs"],
                        st.session_state["pitch_notes"],
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # ── Preparar bytes recortados para la API ─────────────────
                _, wav_buf = trim_audio(audio, sr, start_sec=st.session_state.get("start_sec", 0.0))
                audio_to_send = wav_buf.read()

    st.divider()

    # ── 3. Botón de generación (siempre visible) ──────────────────────────
    if st.button("🚀 Generar música", type="primary", use_container_width=True):
        # a. Guard de créditos diarios (admins tienen pase ilimitado)
        is_admin = st.session_state.get("is_admin", False)
        if st.session_state["credits"] >= CREDIT_LIMIT and not is_admin:
            st.warning("⏱️ Límite diario alcanzado. Vuelve mañana para más generaciones.")
            return

        # b. Validar prompt
        user_prompt = st.session_state.get("prompt_text", "").strip()
        if not user_prompt:
            st.warning("⚠️ Escribe una descripción antes de generar.")
            return

        # c. Llamada a la API
        with st.spinner("🎵 Generando tu canción con IA…"):
            success, output_url, cost = generate_music(
                prompt=user_prompt,
                wav_bytes=audio_to_send,
            )

        # d. Éxito
        if success and output_url:
            user_id     = st.session_state["user_id"]
            new_credits = st.session_state["credits"] + 1

            log_generation(user_id, user_prompt, cost, success=True)
            st.session_state["credits"] = new_credits
            update_credits(user_id, new_credits, datetime.now().date().isoformat())

            show_result(output_url, user_prompt)
            st.balloons()

        # e. Fallo
        else:
            st.error("❌ Error al generar. Intenta de nuevo.")


# ---------------------------------------------------------------------------
# 6. Resultado de generación
# ---------------------------------------------------------------------------

def show_result(output_url: str, prompt_text: str) -> None:
    """
    Muestra el audio generado y habilita su descarga.

    Intenta descargar los bytes vía requests para ofrecer un botón de
    descarga nativo. Si falla, cae a reproducir la URL directamente
    desde el CDN de Replicate.
    """
    st.markdown("#### 🎶 Música generada")

    try:
        response = requests.get(output_url, timeout=30)
        response.raise_for_status()
        audio_bytes = response.content
        st.session_state["result_audio_bytes"] = audio_bytes

        st.audio(audio_bytes, format="audio/wav")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="⬇️ Descargar canción",
            data=audio_bytes,
            file_name=f"melodygen_{timestamp}.wav",
            mime="audio/wav",
            use_container_width=True,
        )

    except Exception as e:
        print(f"[show_result] download error: {e}")
        st.audio(output_url)
        st.warning("⚠️ Descarga no disponible, pero puedes escucharla arriba.")

    st.caption(f'💬 Prompt: *"{prompt_text}"*')


def show_main_app():
    """Punto de entrada de la app autenticada: sidebar + enrutamiento."""
    _build_sidebar()

    if st.session_state.get("show_admin"):
        show_admin_panel()
    else:
        show_generation_flow()


# ---------------------------------------------------------------------------
# 6. Enrutamiento
# ---------------------------------------------------------------------------
if not st.session_state["logged_in"]:
    show_auth_page()
else:
    show_main_app()
