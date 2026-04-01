import io
import os
import replicate
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Configura el token globalmente para el cliente de Replicate
os.environ.setdefault("REPLICATE_API_TOKEN", os.environ.get("REPLICATE_API_TOKEN", ""))

# Modelo y costo estimado por generación
_MODEL      = "meta/musicgen"
_MODEL_VER  = "melody"
_DURATION   = 30
_COST_USD   = 0.0035  # Ajustar según métricas reales de facturación


def generate_music(wav_bytes: bytes, prompt: str) -> tuple[bool, str | None, float]:
    """
    Llama a MusicGen-Melody en Replicate para generar audio a partir de
    una melodía de referencia (WAV) y un prompt de texto.

    Args:
        wav_bytes: Bytes del archivo WAV de melodía de referencia.
        prompt:    Descripción textual del estilo musical deseado.

    Retorna:
        (True,  output_url, estimated_cost)  → éxito
        (False, None,       0.0)             → error
    """
    try:
        melody_buffer = io.BytesIO(wav_bytes)

        output = replicate.run(
            f"{_MODEL}",
            input={
                "melody":        melody_buffer,
                "prompt":        prompt,
                "duration":      _DURATION,
                "model_version": _MODEL_VER,
            },
        )

        # replicate.run() puede retornar una lista de URLs o una URL directa
        if isinstance(output, list):
            url = output[0]
        else:
            url = str(output)

        return True, url, _COST_USD

    except Exception as e:
        st.error(f"❌ Error al generar música: {e}")
        print(f"[replicate_client] generate_music error: {e}")
        return False, None, 0.0
