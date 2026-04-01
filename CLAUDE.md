# vibecoding-dtmf

Interactive DTMF tone explorer — a native desktop app where a child presses keys on a 4×4 keypad and hears the correct dual-tone audio, with row and column frequencies always visible.

---

## References — Where Things Live

- Product context: `docs/PRD.md`
- Feature specs: `docs/features/`
- Tech stack: `docs/techstack.md`
- Progress: `docs/STATE.md`
- Deferred work: `docs/BACKLOG.md`

---

## Code Conventions

- Package manager: `uv` — use `uv add`, `uv run`, `uv sync`
- Formatter/linter: `ruff` — run `ruff check` and `ruff format`
- Type checker: `pyright`
- All function parameters and return types must be annotated
- Use `from __future__ import annotations` for forward references
- Prefer `X | Y` union syntax over `Union[X, Y]`

---

## Learned Rules

<!-- Grows automatically as corrections are made. Each entry dated. -->
