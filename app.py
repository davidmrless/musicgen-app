import streamlit as st
from dotenv import load_dotenv

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
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------------------------------------------------------------------
# 4. Vistas (placeholders — se implementan en prompts posteriores)
# ---------------------------------------------------------------------------

def show_auth_page():
    pass


def show_main_app():
    pass


# ---------------------------------------------------------------------------
# 5. Enrutamiento
# ---------------------------------------------------------------------------
if not st.session_state["logged_in"]:
    show_auth_page()
else:
    show_main_app()
