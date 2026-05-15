from typing import Tuple

import numpy as np
from scipy import signal


def rms(audio: np.ndarray) -> float:
    return float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))


def _normalize_rms(audio: np.ndarray) -> np.ndarray:
    """Scale audio so its RMS equals 1.0, making the comparison amplitude-independent."""
    r = rms(audio)
    if r < 1e-9:
        return audio
    return audio / r


def compare(off_air: np.ndarray, program: np.ndarray, sample_rate: int) -> Tuple[float, float]:
    """
    Compare two audio arrays using normalised cross-correlation.

    Both inputs are RMS-normalised before comparison so that level differences
    between the off-air receiver and program feed do not distort the score.

    How the cross-correlation works
    --------------------------------
    scipy.signal.correlate(a, b) computes:

        c[k]  =  sum_n  a[n + k] * b[n]

    The output index where c is largest reveals how many samples a leads b:
      * lag > 0  →  a (off_air) leads b (program)   — unusual
      * lag < 0  →  a (off_air) lags  b (program)   — normal: FM is delayed

    Dividing the peak by len(off_air) normalises to [0, 1]:
    - Both signals are unit-RMS, so sum(a²) = n and max c = n (identical content).
    - Score ≈ 1.0  means the same audio is present on both feeds.
    - Score ≈ 0.0  means the feeds carry unrelated audio.

    Returns
    -------
    similarity : float in [0.0, 1.0]
    delay_ms   : float, positive = off_air is delayed behind program
    """
    a = _normalize_rms(off_air).astype(np.float64)
    b = _normalize_rms(program).astype(np.float64)

    corr = signal.correlate(a, b, mode="full", method="auto")
    lags = signal.correlation_lags(len(a), len(b), mode="full")

    peak_idx = int(np.argmax(np.abs(corr)))
    lag_samples = int(lags[peak_idx])

    # Clamp to 1.0 to guard against tiny floating-point overruns
    similarity = min(abs(float(corr[peak_idx])) / len(a), 1.0)

    # Positive lag means off_air leads program; negate so positive = off_air is late
    delay_ms = (-lag_samples / sample_rate) * 1000.0

    return similarity, delay_ms
