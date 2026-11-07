# Sunday League — UI: Clubhouse Noticeboard (2026-11-07)

Chosen by Marcel: noticeboard style, club colours on the accents, light default, simple dark mode as an option.

- `sunday_league_ui_tokens_v2.json` — tokens (light/dark, fixed, club examples + rules). Replaces the chalkboard tokens in `design/ui-handoff/` for the build.
- Full spec (components, layout, motion, open questions): https://claude.ai/artifact/JbPtKYncdTQhGp42vJkJR3
- Mock-ups (canvas, page "Round 4"): https://claude.ai/artifact/DVUtGedEbLXL7v6A2fPP2m
- `mockups/` — the canvas source files (`.dc.html`). They only render inside the canvas (they use its runtime and uploaded screenshots); kept here as reference/backup.
- `generators/` — the Python scripts that generated the mock-ups (`python screens.py` writes the round-4 screens, `python league.py` the league table: it simulates 8 rounds so the table is consistent).
- League table (canvas page "Round 5"): mini table on the Next Match card, full table as a pinned A4 sheet, zone lines per division (`LT_Full_Zones.dc.html` = middle division, `LT_Full_Zones_Bottom.dc.html` = Non-League 3).
