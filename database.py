import os
from datetime import date
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_KEY: str = os.environ["SUPABASE_KEY"]


def get_client() -> Client:
    """Retorna un cliente Supabase inicializado con las credenciales del entorno."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_user_by_username(username: str) -> dict | None:
    """Busca un usuario por su username. Retorna el dict del primer resultado o None."""
    try:
        client = get_client()
        response = (
            client.table("users")
            .select("*")
            .eq("username", username)
            .limit(1)
            .execute()
        )
        data = response.data
        return data[0] if data else None
    except Exception as e:
        print(f"[database] get_user_by_username error: {e}")
        return None


def update_credits(user_id: str, new_count: int, new_date: str) -> dict | None:
    """
    Actualiza credits_used_today y last_credit_reset para el usuario dado.
    new_date debe ser un string ISO 8601 (YYYY-MM-DD).
    """
    try:
        client = get_client()
        response = (
            client.table("users")
            .update({
                "credits_used_today": new_count,
                "last_credit_reset": new_date,
            })
            .eq("id", user_id)
            .execute()
        )
        data = response.data
        return data[0] if data else None
    except Exception as e:
        print(f"[database] update_credits error: {e}")
        return None


def reset_credits_if_new_day(user: dict) -> dict:
    """
    Compara last_credit_reset con la fecha actual.
    Si son distintas, resetea credits_used_today a 0 y actualiza la fecha.
    Retorna el dict del usuario con los valores ya actualizados.
    """
    try:
        today = date.today().isoformat()          # "YYYY-MM-DD"
        last_reset = user.get("last_credit_reset", today)

        if last_reset != today:
            updated = update_credits(user["id"], 0, today)
            if updated:
                return updated
            user["credits_used_today"] = 0
            user["last_credit_reset"] = today

        return user
    except Exception as e:
        print(f"[database] reset_credits_if_new_day error: {e}")
        return user


def log_generation(
    user_id: str,
    prompt: str,
    cost: float,
    success: bool,
) -> dict | None:
    """Inserta un registro en generation_log. Retorna la fila creada o None."""
    try:
        client = get_client()
        response = (
            client.table("generation_log")
            .insert({
                "user_id": user_id,
                "prompt_text": prompt,
                "replicate_cost_usd": cost,
                "success": success,
            })
            .execute()
        )
        data = response.data
        return data[0] if data else None
    except Exception as e:
        print(f"[database] log_generation error: {e}")
        return None


def get_all_stats() -> list[dict] | None:
    """
    Retorna todos los registros de generation_log con el username del usuario
    incluido, ordenados por fecha descendente.

    Supabase soporta joins implícitos mediante la sintaxis de foreign-key:
    'generation_log(*, users(username))'
    """
    try:
        client = get_client()
        response = (
            client.table("generation_log")
            .select("*, users(username)")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"[database] get_all_stats error: {e}")
        return None
