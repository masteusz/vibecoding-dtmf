from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from dtmf.audio import (
    DTMF_KEYS,
    FADE_SAMPLES,
    SAMPLE_RATE,
    AudioInitError,
    _DtmfAudioEngine,
)


# ---------------------------------------------------------------------------
# DTMF_KEYS table
# ---------------------------------------------------------------------------

EXPECTED_ROW_FREQS = {697.0, 770.0, 852.0, 941.0}
EXPECTED_COL_FREQS = {1209.0, 1336.0, 1477.0, 1633.0}


def test_dtmf_keys_has_16_entries() -> None:
    assert len(DTMF_KEYS) == 16


def test_dtmf_keys_row_freqs_are_valid() -> None:
    for key in DTMF_KEYS:
        assert key.row_freq in EXPECTED_ROW_FREQS


def test_dtmf_keys_col_freqs_are_valid() -> None:
    for key in DTMF_KEYS:
        assert key.col_freq in EXPECTED_COL_FREQS


def test_dtmf_keys_row_col_indices_in_range() -> None:
    for key in DTMF_KEYS:
        assert 0 <= key.row_index <= 3
        assert 0 <= key.col_index <= 3


def test_dtmf_keys_all_labels_unique() -> None:
    labels = [k.label for k in DTMF_KEYS]
    assert len(labels) == len(set(labels))


def test_dtmf_keys_covers_full_grid() -> None:
    """Every (row_index, col_index) pair in the 4×4 grid exists exactly once."""
    pairs = {(k.row_index, k.col_index) for k in DTMF_KEYS}
    expected = {(r, c) for r in range(4) for c in range(4)}
    assert pairs == expected


# ---------------------------------------------------------------------------
# Helpers for engine tests
# ---------------------------------------------------------------------------


def _make_engine() -> _DtmfAudioEngine:
    """Return a _DtmfAudioEngine with sounddevice mocked out."""
    with patch("dtmf.audio.sd.query_devices", return_value={"name": "mock device"}):
        return _DtmfAudioEngine()


def _make_outdata(frames: int) -> np.ndarray:
    return np.zeros((frames, 1), dtype=np.float32)


# ---------------------------------------------------------------------------
# AudioInitError
# ---------------------------------------------------------------------------


def test_audio_init_error_on_no_device() -> None:
    import sounddevice as sd

    with patch(
        "dtmf.audio.sd.query_devices", side_effect=sd.PortAudioError("no device")
    ):
        with pytest.raises(AudioInitError):
            _DtmfAudioEngine()


def test_audio_init_error_on_none_device() -> None:
    with patch("dtmf.audio.sd.query_devices", return_value=None):
        with pytest.raises(AudioInitError):
            _DtmfAudioEngine()


# ---------------------------------------------------------------------------
# play_tone / stop_tone
# ---------------------------------------------------------------------------


def test_play_tone_opens_stream() -> None:
    engine = _make_engine()
    mock_stream = MagicMock()

    with patch("dtmf.audio.sd.OutputStream", return_value=mock_stream):
        engine.play_tone(697.0, 1209.0)

    mock_stream.start.assert_called_once()
    assert engine._active_freqs == (697.0, 1209.0)


def test_play_tone_stops_previous_stream_before_starting_new() -> None:
    engine = _make_engine()
    first_stream = MagicMock()
    second_stream = MagicMock()

    with patch("dtmf.audio.sd.OutputStream", side_effect=[first_stream, second_stream]):
        engine.play_tone(697.0, 1209.0)
        engine.play_tone(770.0, 1336.0)

    first_stream.stop.assert_called_once()
    first_stream.close.assert_called_once()
    second_stream.start.assert_called_once()


def test_stop_tone_sets_stopping_flag() -> None:
    engine = _make_engine()
    mock_stream = MagicMock()

    with patch("dtmf.audio.sd.OutputStream", return_value=mock_stream):
        engine.play_tone(697.0, 1209.0)

    with patch("dtmf.audio.threading.Thread"):
        engine.stop_tone()

    assert engine._stopping is True


def test_stop_tone_noop_when_no_stream() -> None:
    engine = _make_engine()
    engine.stop_tone()  # Should not raise


# ---------------------------------------------------------------------------
# OS key-repeat guard
# ---------------------------------------------------------------------------


def test_play_tone_ignores_duplicate_call_for_same_freq_pair() -> None:
    engine = _make_engine()
    mock_stream = MagicMock()

    with patch("dtmf.audio.sd.OutputStream", return_value=mock_stream) as mock_ctor:
        engine.play_tone(697.0, 1209.0)
        engine.play_tone(697.0, 1209.0)  # duplicate — same pair

    assert mock_ctor.call_count == 1  # stream created only once


# ---------------------------------------------------------------------------
# Callback: fade-in envelope
# ---------------------------------------------------------------------------


def test_callback_applies_fade_in_at_stream_start() -> None:
    engine = _make_engine()
    engine._row_freq = 697.0
    engine._col_freq = 1209.0

    frames = FADE_SAMPLES
    outdata = _make_outdata(frames)
    engine._callback(outdata, frames, None, None)  # type: ignore[arg-type]

    # First sample should be near 0 (faded in from silence)
    assert abs(float(outdata[0, 0])) < 0.05
    # Last sample should be at full amplitude (fade-in complete)
    assert abs(float(outdata[-1, 0])) > 0.0


def test_callback_no_fade_in_after_first_chunk() -> None:
    engine = _make_engine()
    engine._row_freq = 697.0
    engine._col_freq = 1209.0
    engine._fade_in_pos = FADE_SAMPLES  # already past fade-in

    frames = 256
    outdata = _make_outdata(frames)
    engine._callback(outdata, frames, None, None)  # type: ignore[arg-type]

    # Output should have non-trivial amplitude (no fade suppression)
    assert np.max(np.abs(outdata)) > 0.1


# ---------------------------------------------------------------------------
# Callback: phase accumulation
# ---------------------------------------------------------------------------


def test_callback_accumulates_phase_across_calls() -> None:
    engine = _make_engine()
    engine._row_freq = 697.0
    engine._col_freq = 1209.0
    engine._fade_in_pos = FADE_SAMPLES  # skip fade-in

    frames = 256
    out1 = _make_outdata(frames)
    engine._callback(out1, frames, None, None)  # type: ignore[arg-type]
    phase_after_first = engine._row_phase

    out2 = _make_outdata(frames)
    engine._callback(out2, frames, None, None)  # type: ignore[arg-type]
    phase_after_second = engine._row_phase

    assert phase_after_first != 0.0
    assert phase_after_second != phase_after_first


# ---------------------------------------------------------------------------
# Constants sanity
# ---------------------------------------------------------------------------


def test_sample_rate_is_44100() -> None:
    assert SAMPLE_RATE == 44100


def test_fade_samples_between_5_and_10_ms() -> None:
    min_samples = int(SAMPLE_RATE * 0.005)
    max_samples = int(SAMPLE_RATE * 0.010)
    assert min_samples <= FADE_SAMPLES <= max_samples
