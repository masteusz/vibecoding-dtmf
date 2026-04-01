from __future__ import annotations

import time
import threading
from dataclasses import dataclass

import numpy as np
import sounddevice as sd

SAMPLE_RATE: int = 44100
FADE_SAMPLES: int = int(SAMPLE_RATE * 0.008)  # 8 ms fade-in / fade-out


class AudioInitError(Exception):
    """Raised when no audio output device is available."""


@dataclass(frozen=True)
class DTMFKey:
    label: str
    row_freq: float
    col_freq: float
    row_index: int
    col_index: int


DTMF_KEYS: list[DTMFKey] = [
    DTMFKey("1", 697.0, 1209.0, 0, 0),
    DTMFKey("2", 697.0, 1336.0, 0, 1),
    DTMFKey("3", 697.0, 1477.0, 0, 2),
    DTMFKey("A", 697.0, 1633.0, 0, 3),
    DTMFKey("4", 770.0, 1209.0, 1, 0),
    DTMFKey("5", 770.0, 1336.0, 1, 1),
    DTMFKey("6", 770.0, 1477.0, 1, 2),
    DTMFKey("B", 770.0, 1633.0, 1, 3),
    DTMFKey("7", 852.0, 1209.0, 2, 0),
    DTMFKey("8", 852.0, 1336.0, 2, 1),
    DTMFKey("9", 852.0, 1477.0, 2, 2),
    DTMFKey("C", 852.0, 1633.0, 2, 3),
    DTMFKey("*", 941.0, 1209.0, 3, 0),
    DTMFKey("0", 941.0, 1336.0, 3, 1),
    DTMFKey("#", 941.0, 1477.0, 3, 2),
    DTMFKey("D", 941.0, 1633.0, 3, 3),
]


class _DtmfAudioEngine:
    """Plays a single DTMF tone at a time via sounddevice OutputStream."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stream: sd.OutputStream | None = None
        self._row_phase: float = 0.0
        self._col_phase: float = 0.0
        self._active_freqs: tuple[float, float] | None = None
        self._stopping: bool = False
        self._fade_in_pos: int = 0
        self._fade_out_pos: int = 0
        self._row_freq: float = 0.0
        self._col_freq: float = 0.0

        # Verify a device is available at startup
        try:
            info = sd.query_devices(kind="output")
            if info is None:
                raise AudioInitError("No audio output device available")
        except sd.PortAudioError as exc:
            raise AudioInitError(f"Audio device initialisation failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def play_tone(self, row_freq: float, col_freq: float) -> None:
        """Start playing a DTMF tone. Stops the current tone first if needed."""
        with self._lock:
            if self._active_freqs == (row_freq, col_freq):
                # OS key-repeat guard: same tone already playing, ignore
                return
            self._stop_stream_locked()
            self._row_freq = row_freq
            self._col_freq = col_freq
            self._row_phase = 0.0
            self._col_phase = 0.0
            self._stopping = False
            self._fade_in_pos = 0
            self._fade_out_pos = 0
            self._active_freqs = (row_freq, col_freq)
            self._stream = sd.OutputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                callback=self._callback,
            )
            self._stream.start()

    def stop_tone(self) -> None:
        """Fade out and stop the active tone."""
        with self._lock:
            if self._stream is None:
                return
            self._stopping = True
            self._fade_out_pos = 0
        # Close the stream from a background thread after the fade (8 ms) plus
        # enough time for the hardware output buffer to drain (50 ms total).
        # This avoids a click from CallbackStop cutting the stream mid-buffer.
        threading.Thread(target=self._close_after_fade, daemon=True).start()

    def _close_after_fade(self) -> None:
        time.sleep(0.05)
        with self._lock:
            if self._stopping and self._stream is not None:
                self._stop_stream_locked()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _stop_stream_locked(self) -> None:
        """Close the current stream immediately (call while holding _lock)."""
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        self._active_freqs = None
        self._stopping = False

    def _callback(
        self,
        outdata: np.ndarray,
        frames: int,
        _time: object,
        _status: sd.CallbackFlags,
    ) -> None:
        """sounddevice callback — runs on the audio thread."""
        n = np.arange(frames, dtype=np.float64)
        two_pi = 2.0 * np.pi

        row_freq = self._row_freq
        col_freq = self._col_freq
        row_phase = self._row_phase
        col_phase = self._col_phase

        row_inc = two_pi * row_freq / SAMPLE_RATE
        col_inc = two_pi * col_freq / SAMPLE_RATE

        row_wave = np.sin(row_phase + n * row_inc)
        col_wave = np.sin(col_phase + n * col_inc)
        samples = (row_wave + col_wave) * 0.4  # 0.4 keeps sum within ±1

        # Accumulate phase (mod 2π to avoid float drift over long holds)
        self._row_phase = (row_phase + frames * row_inc) % two_pi
        self._col_phase = (col_phase + frames * col_inc) % two_pi

        # Fade-in: apply to the very first FADE_SAMPLES of the stream
        fade_in_pos = self._fade_in_pos
        if fade_in_pos < FADE_SAMPLES:
            fade_end = min(frames, FADE_SAMPLES - fade_in_pos)
            ramp = np.linspace(
                fade_in_pos / FADE_SAMPLES,
                (fade_in_pos + fade_end) / FADE_SAMPLES,
                fade_end,
            )
            samples[:fade_end] *= ramp
            self._fade_in_pos = fade_in_pos + fade_end

        # Fade-out — no CallbackStop; stream stays open and outputs zeros until
        # _close_after_fade() closes it, ensuring the hardware buffer drains.
        if self._stopping:
            pos = self._fade_out_pos
            remaining = FADE_SAMPLES - pos
            if remaining <= 0:
                # Fade complete — output silence until the stream is closed
                outdata.fill(0.0)
                return
            fade_frames = min(frames, remaining)
            ramp = np.linspace(
                1.0 - pos / FADE_SAMPLES,
                1.0 - (pos + fade_frames) / FADE_SAMPLES,
                fade_frames,
            )
            samples[:fade_frames] *= ramp
            if fade_frames < frames:
                samples[fade_frames:] = 0.0
            self._fade_out_pos = pos + fade_frames

        outdata[:] = samples.reshape(-1, 1).astype(np.float32)


# Module-level singleton — initialised lazily on first use
_engine: _DtmfAudioEngine | None = None
_engine_lock = threading.Lock()


def _get_engine() -> _DtmfAudioEngine:
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = _DtmfAudioEngine()
        return _engine


def play_tone(row_freq: float, col_freq: float) -> None:
    """Start playing the DTMF tone for (row_freq, col_freq)."""
    _get_engine().play_tone(row_freq, col_freq)


def stop_tone() -> None:
    """Stop the currently playing tone."""
    _get_engine().stop_tone()
