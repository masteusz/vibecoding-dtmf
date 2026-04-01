# Feature: DTMF Audio Engine

**Phase:** 1
**Type:** systematic
**Status:** not started

---

## Purpose

Generates and plays DTMF tones on demand. Each tone is the sum of two sine waves (row frequency + column frequency) produced at runtime at 44100 Hz with a short fade-in/fade-out envelope. This module is the audio foundation — the Keypad UI calls it directly on each press and release.

---

## User Story / Flow

1. App starts — audio engine initializes and confirms device availability.
2. User presses a key — Keypad UI calls `play_tone(row_freq, col_freq)`.
3. Engine starts generating samples continuously; tone plays immediately.
4. User holds the key — engine keeps generating samples via callback.
5. User releases — Keypad UI calls `stop_tone()`.
6. Engine applies fade-out (5–10 ms) and closes the stream.

---

## States

| State | What the user sees / hears |
|-------|--------------------------|
| Idle | Silence; no stream active |
| Playing | Continuous DTMF tone for the active (row_freq, col_freq) pair |
| Transitioning | Previous tone fades out; new tone fades in (within ~10 ms total) |
| Error | Audio device unavailable — surfaced to the UI as an error message |

---

## Business Rules & Edge Cases

- **One tone at a time.** `play_tone()` while a stream is active must stop the previous stream before starting the new one.
- **Fade-in/fade-out must be 5–10 ms.** Prevents audible click artifacts at start and stop.
- **On-the-fly generation only.** No pre-rendered audio files or long pre-generated buffers.
- **Phase continuity.** The sine wave phase must be accumulated across callback calls — not reset to 0 each call — to avoid discontinuity clicks mid-hold.
- **Audio device failure at startup** must be surfaced as a clear error to the caller, not silently swallowed.
- **Indefinite hold.** No fixed duration limit — the stream generates samples until `stop_tone()` is called.

---

## Data Needs

- `row_freq` (float, Hz) — one of 697, 770, 852, 941
- `col_freq` (float, Hz) — one of 1209, 1336, 1477, 1633
- Sample rate: 44100 Hz (constant)
- DTMF key table: 16 entries mapping labels → (row_freq, col_freq, row_index, col_index)
  - Source: defined as a constant in this module; consumed by the Keypad UI

---

## UX Description

No direct visual UX — this is a backend audio module. Its behavior is perceived entirely through the Keypad UI.

---

## Must-Haves

_Defined now, verified at phase completion._

### Truths (observable behaviors)
- [ ] `play_tone(row_freq, col_freq)` starts audible tone within 20 ms
- [ ] `stop_tone()` stops the tone within 20 ms
- [ ] Calling `play_tone()` while a tone is playing stops the previous tone and starts the new one
- [ ] Tone is perceptibly correct (dual-sine sum; no harmonics or distortion)
- [ ] No audible click at start or stop
- [ ] Tone continues indefinitely while held — no timeout, no gap
- [ ] If no audio device is available, initialization raises or returns a clear error

### Artifacts (files that must exist with real implementation)
- [ ] Audio engine module (`dtmf/audio.py` or similar) exporting `play_tone(row_freq, col_freq)`, `stop_tone()`, and `DTMF_KEYS` table
- [ ] `DTMF_KEYS` — list of 16 `DTMFKey` entries with `label`, `row_freq`, `col_freq`, `row_index`, `col_index`

### Key Links (critical connections)
- [ ] Keypad UI imports and calls `play_tone()` / `stop_tone()` from this module
- [ ] `DTMF_KEYS` is imported by the Keypad UI to build the button grid

---

## Known Pitfalls

| Pitfall | Why It Happens | How to Avoid | Warning Signs |
|---------|---------------|-------------|--------------|
| Phase discontinuity clicks mid-hold | Buffer callback restarts sine phase at 0 each call instead of continuing | Accumulate phase across calls: `phase += 2π·freq·(n/sample_rate)` | Audible periodic ticking during sustained hold |
| Click at stream start/stop | Abrupt amplitude change at 0 crossing | Apply linear fade-in (first 5–10 ms) and fade-out (last 5–10 ms) | Pop or click at key press or release |
| Stream not closed on error | Exception in callback or init leaves PortAudio stream open | Use `try/finally` or context manager; always close stream | Audio device locked; next run fails to open stream |
| Blocking audio callback | Calling numpy operations more expensive than needed inside the callback | Keep callback minimal: generate samples with `np.sin`, apply envelope, return | Buffer underruns (`xrun` warnings in stderr), stuttering audio |
| OS key-repeat during hold | OS sends repeated `keydown` events; each triggers `play_tone()` causing micro-restarts | Track active freq pair; skip `play_tone()` if same pair already playing | Rapid clicking/stuttering sound during sustained hold |

---

## Decision Log

| Date | Decision | Rationale |
|------|---------|-----------|
| 2026-04-01 | Hand-rolled numpy tone generation, no `dtmf` library | Math is trivial (two sin calls); no library needed; fewer dependencies |
| 2026-04-01 | sounddevice backend | User-specified; correct choice for direct audio output in Python |
| TBD | `OutputStream` callback vs `sd.play()` | Decide at build time — see Research Areas in PRD |

---

## Related Features

- Keypad UI (`docs/features/keypad-ui.md`) — the only consumer of this module; calls `play_tone()` / `stop_tone()` on button press/release
