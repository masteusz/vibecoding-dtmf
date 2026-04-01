# Feature: Keypad UI

**Phase:** 2
**Type:** creative
**Status:** not started

---

## Purpose

The visual front end. Displays a 4×4 grid of DTMF buttons surrounded by frequency labels — column high frequencies across the top, row low frequencies on the left. Pressing a button triggers tone playback; releasing stops it. The layout makes the two-frequency structure of DTMF immediately visible without explanation.

---

## User Story / Flow

1. Child opens the app — window appears with the full 4×4 keypad and all frequency labels.
2. Child presses a button with the mouse (or keyboard key).
3. The button visually activates (highlights/depresses).
4. The DTMF tone for that key plays.
5. Child releases — button returns to default state; tone stops.
6. Child presses a different button while holding another — previous button deactivates, new one activates; tone changes.
7. If audio is unavailable: an error message is visible at the top; all buttons are disabled.

---

## States

| State | What the user sees |
|-------|-------------------|
| Idle | 4×4 grid with all buttons in default state; frequency labels visible |
| Key held | Pressed button highlighted; tone playing |
| Transitioning | Previous button snaps to idle; new button activates (simultaneous) |
| Audio error | Error banner at top of window; all buttons disabled and visually grayed out |

---

## Business Rules & Edge Cases

- **One active key at a time.** When a new key is pressed while another is held, the previous button returns to idle and the new one activates immediately — no overlap.
- **Mouse press-and-hold.** Tone plays for the duration of the mouse button hold; releasing the mouse (anywhere, including outside the button) stops the tone.
- **Keyboard mapping.** Keys 0–9, `*`, `#` map to their labeled buttons. Keys A–D map to the A/B/C/D column. Keyboard hold triggers same press-and-hold behavior as mouse.
- **No key repeat.** If OS sends repeated `keydown` events while a key is held, ignore repeats for the same key — don't restart the tone.
- **Button size.** Buttons must be large enough for a child to use comfortably with a mouse — minimum ~60×60 px.
- **Frequency labels always visible.** Not hidden in tooltips or revealed only on hover.
- **Window size.** App window must fit entirely on a typical desktop (1280×800 or larger) without scrolling.

---

## Data Needs

- `DTMF_KEYS` table from audio engine module — used to build the button grid (label, row_index, col_index)
- Row frequency labels: 697, 770, 852, 941 Hz (derived from key table)
- Column frequency labels: 1209, 1336, 1477, 1633 Hz (derived from key table)
- Audio engine instance — `play_tone()` / `stop_tone()` interface

---

## UX Description

- **Layout:** Column frequency labels across the top row. Row frequency labels in a left column. 4×4 button grid in the remaining space.
- **Typography:** Monospaced font for Hz numbers (e.g., "1209 Hz", "697 Hz"). Large, bold font for key labels (1, 2, A, *, etc.).
- **Visual style:** Clean, slightly retro — evokes a telephone keypad or signal generator. High contrast. No decoration beyond what serves readability.
- **Active state:** Pressed button visually distinct (e.g., depressed appearance, color change, or border highlight).
- **Error state:** Prominent red/amber banner at the top of the window; buttons grayed out.

---

## Must-Haves

_Defined now, verified at phase completion._

### Truths (observable behaviors)
- [ ] All 16 DTMF keys are visible and labeled (1–9, *, 0, #, A–D)
- [ ] Row frequencies are labeled on the left (697, 770, 852, 941 Hz)
- [ ] Column frequencies are labeled on the top (1209, 1336, 1477, 1633 Hz)
- [ ] Pressing and holding a button plays its tone; releasing stops it
- [ ] Pressing a second button while holding the first: first stops, second starts immediately
- [ ] Releasing the mouse outside the button still stops the tone
- [ ] Keyboard keys (0–9, *, #, A–D) trigger the same behavior as clicking
- [ ] Audio error is shown as a visible label; all buttons are disabled
- [ ] Window fits on a 1280×800 screen without scrolling

### Artifacts (files that must exist with real implementation)
- [ ] Main application entry point — creates the window, initializes audio engine, handles audio error
- [ ] Keypad widget — renders column headers, row labels, and 4×4 button grid using `DTMF_KEYS`
- [ ] Key button widget — handles press/release signals, visual active state, communicates with audio engine

### Key Links (critical connections)
- [ ] Keypad widget imports `DTMF_KEYS` from audio engine module to build grid
- [ ] Key button widget calls `play_tone(row_freq, col_freq)` on press
- [ ] Key button widget calls `stop_tone()` on release
- [ ] Main entry point catches audio initialization errors and passes them to the keypad widget for display

---

## Known Pitfalls

| Pitfall | Why It Happens | How to Avoid | Warning Signs |
|---------|---------------|-------------|--------------|
| Mouse release outside button leaves tone stuck | User presses, drags cursor off button, releases — `mouseReleaseEvent` doesn't fire on the button | Connect to window-level mouse release, or use `mousePressEvent` + global `mouseReleaseEvent` on the widget | Tone plays indefinitely after user releases mouse off-button |
| OS key-repeat triggers tone restart | OS sends repeated `keydown` events while key is held | Track currently-active keyboard key; ignore `keyPressEvent` for same key if already active | Audible rapid micro-restarts during keyboard hold |
| Keyboard focus lost mid-hold | Window loses focus while key is held — `keyReleaseEvent` never fires | On `focusOutEvent`, call `stop_tone()` and clear active state | Tone stuck after alt-tabbing away |
| Buttons too small for a child | Default button sizing for a 4×4 grid in a small window | Set explicit minimum button size (≥60×60 px) and minimum window size | Buttons look correct in dev but frustrating to hit for a child |

---

## Decision Log

| Date | Decision | Rationale |
|------|---------|-----------|
| 2026-04-01 | PySide6 GUI framework | User-specified; correct choice for native desktop window on Linux/macOS/Windows |
| 2026-04-01 | Frequency labels always visible (not tooltip/hover) | Core educational goal — child must see the numbers without any interaction |

---

## Related Features

- DTMF Audio Engine (`docs/features/audio-engine.md`) — provides `play_tone()`, `stop_tone()`, and `DTMF_KEYS`; must be complete before this feature can be built
