# BACKLOG.md — vibecoding-dtmf

Items explicitly deferred during scope, PRD generation, or build.

---

## Feedback

<!-- Entries added via /gsr:feedback -->

---

## Deferred from Scope

| Item | Why Deferred | Revisit When |
|------|-------------|-------------|
| Waveform / oscilloscope display | Educational bonus — shows the dual-sine shape in real time. Adds pyqtgraph or custom painter complexity. | After core app ships and works well |
| Sequence / dialing mode | Play a number sequence (e.g., dial a phone number). Fun extension but out of scope for single-button demo. | After core app ships |
| Microphone decoder mode | Listens for DTMF tones and identifies them. Significant added complexity; separate use case. | Separate project consideration |

---

## Captured During Build

| Item | Context | Priority |
|------|---------|---------|
| | | |

---

## Triage (after final phase)

_Review after all build phases PASS. Categorize each item:_
- **must before launch** → becomes a new build phase
- **v2** → ship it, track separately
- **won't do** → close it

| Item | Decision | Notes |
|------|---------|-------|
| Waveform / oscilloscope display | v2 | Functional app ships without it; adds pyqtgraph + painter complexity |
| Sequence / dialing mode | v2 | Fun extension; ship core first |
| Microphone decoder mode | Won't do | Different use case; separate project |
