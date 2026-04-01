# vibecoding-dtmf — PRD

**Version:** 0.1
**Status:** Draft
**Last Updated:** 2026-04-01

---

## 1. What We're Building

A native desktop application that lets a child explore DTMF (Dual-Tone Multi-Frequency) signaling interactively. The app shows a 4×4 keypad where pressing and holding any key plays the correct dual-tone audio while the row and column frequencies are always visible. DTMF is a real-world standard — every telephone tone is just two sine waves summed — and this app turns that abstract concept into something a child can hear, see, and understand.

---

## 2. Business Goals

- **Primary:** A child presses a key, hears the correct tone, and can identify the two frequencies that produced it — without any explanation needed.
- **Secondary:** The full 16-key DTMF standard is visible and explorable in one window, including the rarely seen A/B/C/D column.

**Success metrics:**
- Child operates the app without guidance on first encounter.
- All 16 DTMF tones are correct (match ITU-T Q.23 standard frequency pairs).
- Audio starts within 20 ms of press; stops within 20 ms of release.

---

## 3. Target Users

**Primary:** A child (ages 6–12), guided by a developer parent who wants to demonstrate how DTMF works.

**Day 1 user:** Presses buttons, hears tones, notices the frequency numbers change. Asks "why do different buttons sound different?"

**Day 7 user:** Same — this is a demo tool, not a daily app. Day 7 means the parent is showing it again to another person or the child is exploring more systematically.

**Day 30 user:** Revisited occasionally as a curiosity or teaching aid.

---

## 4. MVP Scope

**In scope:**
- 4×4 keypad grid with all 16 DTMF keys (1–9, *, 0, #, A–D)
- Row frequency labels on the left (697, 770, 852, 941 Hz)
- Column frequency labels on the top (1209, 1336, 1477, 1633 Hz)
- Press-and-hold plays the correct DTMF dual-tone
- Release stops the tone immediately
- One tone at a time — new press pre-empts any active tone
- On-the-fly tone generation via numpy + sounddevice (no pre-recorded audio)
- Short fade-in/fade-out (5–10 ms) to prevent click artifacts
- Visible error state if audio device is unavailable at startup

**Explicitly out of scope (v2):**
- Waveform / oscilloscope display — educational bonus, adds pyqtgraph dependency
- Sequence / dialing mode — play a sequence of tones (e.g., dial a phone number)
- Microphone decoder mode — listen for and identify DTMF tones from audio input

---

## 5. High-Level Architecture

```
┌──────────────────────────────────────┐
│            PySide6 Window            │
│  ┌────────────────────────────────┐  │
│  │  KeypadWidget                  │  │
│  │  ┌─────────────────────────┐   │  │
│  │  │  Column freq headers    │   │  │
│  │  │  (1209 / 1336 / 1477 / 1633 Hz) │  │
│  │  ├─────────────────────────┤   │  │
│  │  │  Row label │ Button grid │   │  │
│  │  │  (697 Hz)  │ [1][2][3][A]│   │  │
│  │  │  (770 Hz)  │ [4][5][6][B]│   │  │
│  │  │  (852 Hz)  │ [7][8][9][C]│   │  │
│  │  │  (941 Hz)  │ [*][0][#][D]│   │  │
│  │  └─────────────────────────┘   │  │
│  └───────────────┬────────────────┘  │
│                  │ press / release    │
│  ┌───────────────▼────────────────┐  │
│  │       DTMF Audio Engine        │  │
│  │    numpy (tone generation)     │  │
│  │    sounddevice (playback)      │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
              (no backend, no DB)
```

---

## 6. Conceptual Data Model

Static lookup — no persistence, no user data.

```
DTMFKey (16 entries, defined at module level):
  has: label, row_freq, col_freq, row_index, col_index
  Key rule: each key maps to exactly one (row_freq, col_freq) pair
  Tone formula: sin(2π·row_freq·t) + sin(2π·col_freq·t)
  Key rule: row_freq ∈ {697, 770, 852, 941}; col_freq ∈ {1209, 1336, 1477, 1633}
```

_Implementation: static constant in audio engine module — no schema or migrations._

---

## 7. Feature Index

| Feature | File | Status | Phase |
|---------|------|--------|-------|
| DTMF Audio Engine | `docs/features/audio-engine.md` | not started | 1 |
| Keypad UI | `docs/features/keypad-ui.md` | not started | 2 |

---

## 8. Non-Functional Requirements

- **Performance:** Tone starts within 20 ms of press; stops within 20 ms of release. No glitches or gaps during sustained hold.
- **Accessibility:** Large buttons readable by a child; frequency labels always visible (never hidden in tooltips or shown only on hover).
- **Platform:** Desktop only — Linux, macOS, Windows via PySide6. No mobile requirement.
- **Audio quality:** No audible click artifacts at tone start or stop; tone must match DTMF standard frequencies exactly.

---

## 9. Design Direction

Clean, functional, slightly retro — evokes a telephone keypad or scientific instrument. Large buttons with high contrast. Monospaced font for frequency numbers. Minimal decoration: everything visible serves a purpose.

_Design tokens: PySide6 stylesheet defined in the UI module._

---

## 10. Build Phases

| # | Phase | Type | Features | Demo |
|---|-------|------|---------|------|
| 1 | Audio Engine | systematic | DTMF Audio Engine | Developer calls `play_tone(697, 1209)` and hears the correct tone; calls `stop_tone()` and it stops |
| 2 | Keypad UI | creative | Keypad UI | Child presses and holds any key on the 4×4 grid, hears its DTMF tone, and sees which row and column frequencies produced it |

**Must-haves per phase defined in feature files** (`docs/features/*.md` → Must-Haves section).

---

## 11. Research Areas

| Area | Tier | Status | Notes |
|------|------|--------|-------|
| sounddevice `OutputStream` vs `sd.play()` for while-held | blocking build | open | `OutputStream` with phase-accumulating callback generates samples on demand and stops cleanly; `sd.play()` with a pre-generated long buffer + `sd.stop()` is simpler. Decide at build time based on latency and stop-cleanness. |
