# Tech Stack — vibecoding-dtmf

---

## Core Stack

| Layer | Technology | Version | Why |
|-------|-----------|---------|-----|
| Language | Python | 3.13 | User-specified; appropriate for desktop + audio scripting |
| GUI framework | PySide6 | latest | User-specified; native desktop window on Linux/macOS/Windows |
| Audio output | sounddevice | latest | User-specified; direct audio output with low-latency PortAudio backend |
| Signal generation | numpy | latest | Fast sine wave generation; standard scientific Python |
| Package manager | uv | latest | Fast, modern Python package manager |
| Linter/formatter | ruff | latest | Fast, all-in-one Python linter and formatter |
| Type checker | pyright | latest | Static type checking |

_No database, no auth, no hosting — single local desktop app._

---

## Project-Wide Skills

_Skills that apply to every feature in this project._

<!-- None currently installed. -->

---

## Tech Decisions

| Decision | Choice | Why |
|---------|--------|-----|
| GUI framework | PySide6 | User-specified; cross-platform native desktop, Qt bindings for Python |
| Audio backend | sounddevice | User-specified; direct PortAudio access, low latency, suitable for real-time tone generation |
| Tone generation | Hand-rolled numpy (no `dtmf` library) | Math is trivial (two sin calls); avoids unnecessary dependency |
| No pre-recorded audio | On-the-fly numpy generation only | Keeps project clean; makes the math visible; no large asset files |
| Full 16-key grid | 4×4 (all A/B/C/D) not 12-key phone layout | Shows all 8 frequencies, making the educational structure fully visible |
| Tone behavior | Play while held | Tactile and interactive; matches real telephone feel |

---

## Research Areas — Blocking Build

| Area | Status | Notes |
|------|--------|-------|
| sounddevice `OutputStream` callback vs `sd.play()` for while-held | open | `OutputStream` with phase accumulator: clean stop, continuous generation. `sd.play()` with pre-generated buffer: simpler but stop latency depends on buffer size. Resolve at start of Phase 1. |
