# vibecoding-dtmf — Scope

**Date:** 2026-04-01
**Status:** Complete → feeds into `/gsr:prd`

---

## Project Foundations

**Goal:** Let a child explore DTMF tones interactively. Success = kid presses any key, hears the correct dual-tone audio, and can see how the row and column frequencies pair to produce it.

**Vision:** A single desktop window with a 4×4 keypad grid. Column headers show the four high frequencies (1209, 1336, 1477, 1633 Hz); row labels show the four low frequencies (697, 770, 852, 941 Hz). Pressing and holding any button plays its DTMF tone for as long as it's held. Releasing stops the tone. Clean, no clutter.

**Target User:** A child, guided by a developer parent. The app must be immediately understandable — press a button, hear a sound, see the frequencies involved.

**Why:** DTMF is an elegant real-world standard (every phone tone is just two sine waves added together). Making it tactile and visible turns an abstract concept into something a kid can genuinely experience and understand.

**What It Does:** Displays a 16-key DTMF keypad with labeled row/column frequencies. On press-and-hold, auto-generates and plays the correct DTMF dual-tone (sum of two sine waves via numpy + sounddevice). On release, the tone stops.

---

## Navigation & Screens

Single window only:

| Screen | Description |
|--------|-------------|
| Main Window | 4×4 keypad grid with row frequency labels (left) and column frequency labels (top). No other screens or dialogs. |

---

## Core Concepts

**DTMF = two sine waves summed.** Each key is defined by exactly one row frequency and one column frequency. The tone is `sin(2π·f_row·t) + sin(2π·f_col·t)`.

**Frequency grid:**

|           | 1209 Hz | 1336 Hz | 1477 Hz | 1633 Hz |
|-----------|---------|---------|---------|---------|
| **697 Hz** | 1       | 2       | 3       | A       |
| **770 Hz** | 4       | 5       | 6       | B       |
| **852 Hz** | 7       | 8       | 9       | C       |
| **941 Hz** | * (star)| 0       | # (hash)| D       |

**Play-while-held.** Tone starts on mouse/key press, stops on release. Mimics a real phone handset.

**One tone at a time.** If a new key is pressed while another is held, the previous stream stops and the new one starts immediately.

**On-the-fly generation.** Tones are not pre-recorded. They are generated at runtime using numpy at 44100 Hz sample rate. A short linear fade-in/fade-out (5–10 ms) prevents audible clicks at start/stop.

---

## Data Model (entity-level)

One static lookup table — no persistence, no user data.

**DTMF Key Table** (16 entries, defined at module level):

| Field       | Type  | Notes                              |
|-------------|-------|------------------------------------|
| `label`     | str   | Display text on button ("1"–"9", "*", "0", "#", "A"–"D") |
| `row_freq`  | float | Low-group frequency in Hz (697, 770, 852, 941) |
| `col_freq`  | float | High-group frequency in Hz (1209, 1336, 1477, 1633) |
| `row_index` | int   | Grid row (0–3)                     |
| `col_index` | int   | Grid column (0–3)                  |

---

## Edge Cases & Empty States

| Scenario | Handling |
|----------|----------|
| Simultaneous key presses (mouse + keyboard or fast clicking) | One tone at a time — new press stops any active stream before starting the new one |
| Audio device unavailable at startup | Show a visible error label in the window ("Audio unavailable: [reason]"); buttons are disabled |
| Very short press (tap, not hold) | The fade-in/fade-out (5–10 ms) ensures even a quick click produces an audible tone without a click artifact |
| Button held indefinitely | Stream generates samples continuously via callback; no fixed duration limit |

---

## Research Areas

| Area | Tier | Notes |
|------|------|-------|
| sounddevice OutputStream vs `play()` for while-held | blocking build | For while-held playback, `OutputStream` with a phase-accumulating callback is the correct approach — it generates samples on demand and can be stopped cleanly. `sd.play()` with a pre-generated long buffer + `sd.stop()` is a valid simpler alternative. Decide at build time. |

---

## v2 Backlog

| Feature | Why Deferred |
|---------|-------------|
| Waveform / oscilloscope display | Educational bonus — shows the dual-sine shape in real time. Not needed for core demo; adds complexity (need pyqtgraph or custom painter). |
| Sequence / dialing mode | Play a number sequence (e.g., dial a phone number). Fun extension but out of scope for single-button demo. |
| Microphone decoder mode | Listens for DTMF tones and identifies them. Significant added complexity; separate use case. |

---

## Competitive Positioning

Most DTMF demo apps are web-based tone generators with no educational framing. This app differentiates by:

1. **Explicit frequency headers** — row and column Hz values are always visible, not hidden in tooltips or shown only on press.
2. **Full 16-key grid** — shows the complete DTMF standard (including A/B/C/D), not just the phone subset.
3. **Play-while-held** — matches real telephone behavior, more tactile and intuitive for a child.
4. **Native desktop app** — no browser, no latency from web audio API, direct audio output via sounddevice.

---

## Resolved Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Keypad size | 16-key (full DTMF 4×4) | Shows all 8 frequencies in the grid, making the educational structure visible. The 12-key phone layout hides the 4th column. |
| Tone playback mode | Play while held | More tactile and interactive for a kid; matches real phone feel. |
| Tone generation | Hand-rolled numpy (no `dtmf` library) | The math is trivial (two sin calls); removing the dependency keeps the project clean. |
| Audio backend | sounddevice | User-specified; correct choice for direct audio output with Python. |
| GUI framework | PySide6 | User-specified; correct choice for a native desktop window. |
