# Sunday League — UI: Clubhouse Noticeboard (2026-11-07)

Chosen by Marcel: noticeboard style, club colours on the accents, light default, simple dark mode as an option.

- `sunday_league_ui_tokens_v2.json` — tokens (light/dark, fixed, club examples + rules). Replaces the chalkboard tokens in `design/ui-handoff/` for the build.
- Full spec (components, layout, motion, open questions): https://claude.ai/artifact/JbPtKYncdTQhGp42vJkJR3
- Mock-ups (canvas, page "Round 4"): https://claude.ai/artifact/DVUtGedEbLXL7v6A2fPP2m
- `mockups/` — the canvas source files (`.dc.html`). They only render inside the canvas (they use its runtime and uploaded screenshots); kept here as reference/backup.
- `generators/` — the Python scripts that generated the mock-ups (`python screens.py` writes the round-4 screens).
