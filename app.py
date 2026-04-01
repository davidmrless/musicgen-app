import streamlit as st
from dotenv import load_dotenv
from auth import login_user, register_user
from admin import show_admin_panel

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

        # ── Métricas de créditos ──────────────────────────────────────────
        used      = st.session_state["credits"]
        remaining = max(0, CREDIT_LIMIT - used)
        col1, col2 = st.columns(2)
        col1.metric("Usados hoy",   used)
        col2.metric("Disponibles",  remaining)

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
    """Placeholder — se implementa en el Prompt 7.2."""
    pass


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
