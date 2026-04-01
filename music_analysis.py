import numpy as np
import librosa

FMIN = librosa.note_to_hz("C2")  # ~65.4 Hz
FMAX = librosa.note_to_hz("C7")  # ~2093 Hz

# ---------------------------------------------------------------------------
# 1. Detección de BPM
# ---------------------------------------------------------------------------

def get_bpm(audio: np.ndarray, sr: int) -> float | None:
    """
    Estima el BPM del audio usando librosa.beat.beat_track.

    Retorna el tempo como float redondeado a 1 decimal, o None si falla.
    """
    try:
        tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
        # beat_track puede devolver un array en versiones recientes de librosa
        bpm = float(np.atleast_1d(tempo)[0])
        return round(bpm, 1)
    except Exception as e:
        print(f"[music_analysis] get_bpm error: {e}")
        return None


# ---------------------------------------------------------------------------
# 2. Extracción de curva de tono (pitch)
# ---------------------------------------------------------------------------

def get_pitch_curve(
    audio: np.ndarray,
    sr: int,
) -> tuple[np.ndarray, np.ndarray, list] | tuple[None, None, None]:
    """
    Extrae la frecuencia fundamental (F0) cuadro a cuadro usando pYIN.

    Usa librosa.pyin cuando está disponible (más robusto); si no, cae
    a librosa.yin con la misma configuración.

    Retorna:
        (times, frequencies, note_names)
            - times:       array de tiempos en segundos (float64)
            - frequencies: array de Hz; NaN/0 donde no hay pitch detectado
            - note_names:  lista de str o None por cuadro sin pitch
        (None, None, None) si ocurre un error.
    """
    try:
        # ── pYIN (probabilístico, preferable) ─────────────────────────────
        if hasattr(librosa, "pyin"):
            f0, voiced_flag, _ = librosa.pyin(
                audio,
                sr=sr,
                fmin=FMIN,
                fmax=FMAX,
            )
        else:
            # Fallback a YIN determinístico
            f0 = librosa.yin(audio, fmin=FMIN, fmax=FMAX, sr=sr)
            voiced_flag = f0 > 0

        # ── Eje de tiempos alineado al número de cuadros ──────────────────
        hop_length = 512  # default de librosa
        times = librosa.times_like(f0, sr=sr, hop_length=hop_length)

        # ── Convertir Hz → nombres de nota (None donde no hay voz) ────────
        note_names: list[str | None] = []
        for freq, voiced in zip(f0, voiced_flag):
            if voiced and not (np.isnan(freq) or freq == 0):
                note_names.append(librosa.hz_to_note(freq))
            else:
                note_names.append(None)

        return times, f0, note_names

    except Exception as e:
        print(f"[music_analysis] get_pitch_curve error: {e}")
        return None, None, None
