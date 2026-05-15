import threading
from collections import deque
from typing import Optional, Tuple

import numpy as np
import sounddevice as sd

from .config import Config


class AudioCapture:
    """
    Captures stereo audio from a sounddevice InputStream into a rolling
    in-memory buffer. The callback thread appends chunks; the main thread
    calls get_channels() to read a snapshot.
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._lock = threading.Lock()
        self._chunks: deque = deque()
        self._total_samples: int = 0
        self._max_samples: int = int(config.chunk_duration * config.sample_rate)
        self._stream: Optional[sd.InputStream] = None

    def start(self) -> None:
        self._stream = sd.InputStream(
            device=self._config.device,
            samplerate=self._config.sample_rate,
            channels=self._config.channels,
            dtype="float32",
            callback=self._callback,
            blocksize=2048,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _callback(
        self,
        indata: np.ndarray,
        frames: int,
        time: object,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            print(f"[AUDIO] {status}", flush=True)
        chunk = indata.copy()
        with self._lock:
            self._chunks.append(chunk)
            self._total_samples += len(chunk)
            # Discard oldest chunks once buffer exceeds the window size
            while self._total_samples - len(self._chunks[0]) >= self._max_samples:
                removed = self._chunks.popleft()
                self._total_samples -= len(removed)

    def get_channels(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Returns (off_air, program) mono arrays covering chunk_duration seconds,
        or (None, None) if the buffer has not filled yet.
        """
        with self._lock:
            if self._total_samples < self._max_samples:
                return None, None
            buf = np.concatenate(list(self._chunks))

        # Trim to exactly max_samples from the most recent end
        buf = buf[-self._max_samples :]
        off_air = buf[:, self._config.off_air_channel]
        program = buf[:, self._config.program_channel]
        return off_air, program
