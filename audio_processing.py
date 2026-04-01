import io
import numpy as np
import soundfile as sf
import librosa
import noisereduce as nr

TARGET_SR: int = 32_000  # Hz requeridos por MusicGen-Melody


def process_audio(file_bytes: bytes) -> tuple[np.ndarray | None, int | None]:
    """
    Pipeline de limpieza y normalización de audio.

    Pasos:
        1. Carga desde bytes (formato agnóstico vía soundfile).
        2. Conversión a mono si es estéreo.
        3. Reducción de ruido (noisereduce).
        4. Normalización de amplitud (librosa.util.normalize).
        5. Resampleo a TARGET_SR (32 000 Hz) si es necesario.

    Retorna:
        (audio_array, sample_rate)  → éxito
        (None, None)                → cualquier error
    """
    try:
        # ── 1. Carga desde bytes ──────────────────────────────────────────
        buffer = io.BytesIO(file_bytes)
        audio, sr = sf.read(buffer, always_2d=False, dtype="float32")

        # ── 2. Conversión a mono ──────────────────────────────────────────
        if audio.ndim == 2:
            # shape (samples, channels) → promedio de canales
            audio = audio.mean(axis=1)

        # ── 3. Reducción de ruido ─────────────────────────────────────────
        audio = nr.reduce_noise(y=audio, sr=sr)

        # ── 4. Normalización de amplitud ──────────────────────────────────
        # Escala al rango [-1, 1] evitando distorsión por picos aislados
        audio = librosa.util.normalize(audio)

        # ── 5. Resampleo a 32 000 Hz ──────────────────────────────────────
        if sr != TARGET_SR:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=TARGET_SR)
            sr = TARGET_SR

        return audio, sr

    except Exception as e:
        print(f"[audio_processing] process_audio error: {e}")
        return None, None
