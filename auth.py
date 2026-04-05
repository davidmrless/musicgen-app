import os
import bcrypt
from dotenv import load_dotenv
from database import get_client, get_user_by_username, reset_credits_if_new_day

load_dotenv()

INVITE_CODE: str = os.environ.get("INVITE_CODE", "")


def hash_password(password: str) -> str:
    """Hashea una contraseña en texto plano usando bcrypt. Retorna el hash como str."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verifica que password coincida con el hash almacenado. Retorna bool."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def register_user(
    username: str,
    email: str,
    password: str,
    invite_code: str,
) -> tuple[bool, str]:
    """
    Registra un nuevo usuario si el invite_code es válido.

    Retorna:
        (True,  "Registro exitoso")            → éxito
        (False, "<mensaje de error>")          → fallo
    """
    if invite_code != INVITE_CODE:
        return False, "Código de invitación incorrecto."

    password_hash = hash_password(password)

    try:
        client = get_client()
        response = (
            client.table("users")
            .insert({
                "username": username,
                "email": email,
                "password_hash": password_hash,
            })
            .execute()
        )
        if response.data:
            return True, "Registro exitoso."
        return False, "No se pudo crear el usuario. Intenta de nuevo."
    except Exception as e:
        error_msg = str(e).lower()
        if "unique" in error_msg or "duplicate" in error_msg:
            if "username" in error_msg:
                return False, "Ese nombre de usuario ya está en uso."
            if "email" in error_msg:
                return False, "Ese correo electrónico ya está registrado."
        return False, f"Error al registrar: {e}"


def login_user(
    username: str,
    password: str,
) -> tuple[bool, dict | None, str]:
    """
    Autentica a un usuario.

    Retorna:
        (True,  user_dict, "OK")                    → éxito
        (False, None,      "Usuario no encontrado") → usuario inexistente
        (False, None,      "Contraseña incorrecta") → credencial inválida
    """
    user = get_user_by_username(username)

    if user is None:
        return False, None, "Usuario no encontrado."

    if not verify_password(password, user["password_hash"]):
        return False, None, "Contraseña incorrecta."

    user = reset_credits_if_new_day(user)

    return True, user, "OK"
