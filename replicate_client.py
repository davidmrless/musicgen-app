import io
import os
import replicate
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Configura el token globalmente para el cliente de Replicate
os.environ.setdefault("REPLICATE_API_TOKEN", os.environ.get("REPLICATE_API_TOKEN", ""))

# Modelo y costo estimado por generación
_MODEL      = "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb"
_MODEL_VER  = "stereo-melody-large"
_DURATION   = 30
_COST_USD   = 0.0035  # Ajustar según métricas reales de facturación


def generate_music(
    prompt: str,
    wav_bytes: bytes | None = None,
) -> tuple[bool, str | None, float]:
    """
    Llama a MusicGen en Replicate para generar audio.

    Puede operar en dos modos:
      - Text-to-Music: solo prompt (wav_bytes=None)
      - Melody-conditioned: prompt + wav_bytes de referencia

    Args:
        prompt:    Descripción textual del estilo musical deseado.
        wav_bytes: (Opcional) Bytes WAV de melodía de referencia.

    Retorna:
        (True,  output_url, estimated_cost)  → éxito
        (False, None,       0.0)             → error
    """
    try:
        api_input: dict = {
            "prompt":        prompt,
            "duration":      _DURATION,
            "model_version": _MODEL_VER,
        }

        if wav_bytes is not None:
            api_input["input_audio"] = io.BytesIO(wav_bytes)

        output = replicate.run(_MODEL, input=api_input)

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
