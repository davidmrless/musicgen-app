import io
import numpy as np
import soundfile as sf
import librosa

TARGET_SR: int = 32_000


def process_audio(file_bytes: bytes) -> tuple[bytes | None, np.ndarray | None, int | None]:
    """
    Pipeline de carga y preparación de audio.

    Pasos:
        1. Carga desde bytes (formato agnóstico vía soundfile).
        2. Conversión a mono si es estéreo.
        3. Resampleo a TARGET_SR (32 000 Hz) si es necesario.
        4. Exporta a bytes WAV en memoria.

    Retorna:
        (wav_bytes, audio_array, sample_rate)  → éxito
        (None, None, None)                     → cualquier error
    """
    try:
        buffer = io.BytesIO(file_bytes)
        audio, sr = sf.read(buffer, always_2d=False, dtype="float32")

        if audio.ndim == 2:
            audio = audio.mean(axis=1)



        if sr != TARGET_SR:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=TARGET_SR)
            sr = TARGET_SR

        # ── 6. Exportar a bytes WAV ───────────────────────────────────────
        wav_buf = io.BytesIO()
        sf.write(wav_buf, audio, sr, format="WAV", subtype="PCM_16")
        wav_buf.seek(0)
        wav_bytes = wav_buf.read()

        return wav_bytes, audio, sr

    except Exception as e:
        print(f"[audio_processing] process_audio error: {e}")
        return None, None, None


def get_audio_duration(audio: np.ndarray, sr: int) -> float:
    """Retorna la duración del audio en segundos."""
    return len(audio) / sr


def trim_audio(
    audio: np.ndarray,
    sr: int,
    start_sec: float,
    duration: float = 30.0,
) -> tuple[np.ndarray, io.BytesIO]:
    """
    Recorta el audio y lo exporta como WAV en un buffer en memoria.

    Args:
        audio:      Array numpy 1D float32 ya procesado.
        sr:         Sample rate del array.
        start_sec:  Segundo de inicio del recorte.
        duration:   Duración del recorte en segundos (default 30 s).

    Retorna:
        (trimmed_array, wav_bytes_buffer)
        El buffer ya tiene seek(0) aplicado, listo para lectura.
    """
    start_sample = int(start_sec * sr)
    end_sample   = int((start_sec + duration) * sr)

    start_sample = max(0, min(start_sample, len(audio)))
    end_sample   = max(start_sample, min(end_sample, len(audio)))

    trimmed = audio[start_sample:end_sample]

    wav_buffer = io.BytesIO()
    sf.write(wav_buffer, trimmed, sr, format="WAV", subtype="PCM_16")

    wav_buffer.seek(0)

    return trimmed, wav_buffer
