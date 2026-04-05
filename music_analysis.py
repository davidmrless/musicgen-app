import numpy as np
import librosa
import plotly.graph_objects as go

FMIN = librosa.note_to_hz("C2")  # ~65.4 Hz
FMAX = librosa.note_to_hz("C7")  # ~2093 Hz


def get_bpm(audio: np.ndarray, sr: int) -> float | None:
    """
    Estima el BPM del audio usando librosa.beat.beat_track.

    Retorna el tempo como float redondeado a 1 decimal, o None si falla.
    """
    try:
        tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
        bpm = float(np.atleast_1d(tempo)[0])
        return round(bpm, 1)
    except Exception as e:
        print(f"[music_analysis] get_bpm error: {e}")
        return None


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
        if hasattr(librosa, "pyin"):
            f0, voiced_flag, _ = librosa.pyin(
                audio,
                sr=sr,
                fmin=FMIN,
                fmax=FMAX,
            )
        else:
            f0 = librosa.yin(audio, fmin=FMIN, fmax=FMAX, sr=sr)
            voiced_flag = f0 > 0

        hop_length = 512  # default de librosa
        times = librosa.times_like(f0, sr=sr, hop_length=hop_length)

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


_DARK_BG   = "#0e1117"
_FONT_CLR  = "#ffffff"
_DOWNSAMPLE = 4  # Toma 1 de cada N puntos para aligerar el navegador


def create_piano_roll_chart(
    times: np.ndarray,
    frequencies: np.ndarray,
    notes: list,
) -> go.Figure:
    """
    Genera un gráfico de dispersión tipo piano roll con Plotly.

    Args:
        times:       Array de tiempos en segundos.
        frequencies: Array de Hz (NaN donde no hay pitch).
        notes:       Lista de str (nombre de nota) o None por frame sin pitch.

    Retorna:
        go.Figure lista para st.plotly_chart().
    """
    mask = np.array([
        n is not None and not np.isnan(f) and f > 0
        for n, f in zip(notes, frequencies)
    ])

    t_voiced  = times[mask]
    f_voiced  = frequencies[mask]
    n_voiced  = [n for n, m in zip(notes, mask) if m]

    if len(f_voiced) == 0:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title=dict(
                text="🎹 Melodía (No se detectaron notas musicales claras)",
                font=dict(color=_FONT_CLR),
            ),
            paper_bgcolor=_DARK_BG,
            plot_bgcolor=_DARK_BG,
        )
        return empty_fig

    t_ds = t_voiced[::_DOWNSAMPLE]
    f_ds = f_voiced[::_DOWNSAMPLE]
    n_ds = n_voiced[::_DOWNSAMPLE]
    scatter = go.Scatter(
        x=t_ds,
        y=n_ds,
        mode="markers",
        marker=dict(
            size=6,
            color=f_ds,
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(
                title=dict(text="Hz", font=dict(color=_FONT_CLR)),
                tickfont=dict(color=_FONT_CLR),
            ),
        ),
        text=[f"{n} — {f:.1f} Hz" for n, f in zip(n_ds, f_ds)],
        hoverinfo="x+text",
        name="Pitch",
    )

    layout = go.Layout(
        title=dict(
            text="🎹 Melodía detectada",
            font=dict(color=_FONT_CLR, size=18),
        ),
        paper_bgcolor=_DARK_BG,
        plot_bgcolor=_DARK_BG,
        xaxis=dict(
            title="Tiempo (s)",
            showgrid=False,
            color=_FONT_CLR,
            tickfont=dict(color=_FONT_CLR),
        ),
        yaxis=dict(
            title="Nota",
            showgrid=True,
            gridcolor="#2a2d3a",
            color=_FONT_CLR,
            tickfont=dict(color=_FONT_CLR),
        ),
        margin=dict(l=60, r=20, t=50, b=50),
        height=400,
    )

    return go.Figure(data=[scatter], layout=layout)
