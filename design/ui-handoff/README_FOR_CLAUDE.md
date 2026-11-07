# Sunday League — UI Style Handoff for Claude

## What to use
- `sunday_league_ui_tokens.json` is the source of truth for all design values.
- Do not create CSS. The target is Godot 4, which should use Theme resources and `StyleBoxFlat` styles.
- The three themes are `clubhouse_canteen`, `chalkboard`, and `club_colours_red_white`.
- The layout and screen content are shared by all themes. Only visual tokens change.

## Recommended implementation order
1. Import Barlow Semi Condensed (400, 500, 600, 700) and Caveat (500, 600) from Google Fonts.
2. Create a shared Godot Theme for typography, icon sizing, controls and component metrics.
3. Create three theme variants by overriding colours, panel opacity, radii, borders, shadows and button state colours from the JSON.
4. Build the Club Hub only. Do not design additional screens in this task.
5. Use the current low-poly pitch/ground scene as the background. Do not substitute a stadium render, match-in-progress screenshot, player photography or 3D icon art.
6. Keep the centre of the ground clear; the goal and next-match cards should frame the pitch.
7. Keep the ticker and bottom navigation in one slim strip. Remove any unused navigation slot.
8. Test at 1920x1080 and 1280x720. Keep controls at least 44px high and allow approximately 40% extra text width for translations.

## Fixed Club Hub content
- Club: Oakridge Rovers
- Fans: 30
- Fan approval: 58%
- Cash: £34
- Seats: 24
- Squad: 11 / 11
- Record: W4 D1 L3
- Competition label: Friendlies Only
- Goal: Reach 100 paying supporters
- Progress: 24 / 100
- Next opponent: Riverside United
- Play button: enabled
- Availability line: All 11 players available.
- No date, venue, league or division.
- Ticker (exact copy): “Rumour has it the chairman is eyeing a second-hand scoreboard. Fancy.”
- Suggested tagline: “The changing rooms are technically a shed.”

## Personality and icon rules
- Humour belongs in the tagline, ticker, flavour text and small details.
- Keep all controls, labels, stats and instructions plain and functional.
- Use one consistent family of flat, single-colour SVG outline icons on a 24x24 grid, 2px stroke.
- No photorealistic or 3D-rendered UI assets.
- Do not repeat the club crest or club name in the goal card; they already appear in the top bar.

## Godot styling notes
- Use `StyleBoxFlat` for panel/button fills, borders, radii and shadows.
- Use semi-transparent flat panel fills; do not use backdrop blur/frosted glass.
- Use containers and anchors rather than hard-coded screen-position assumptions wherever possible.
- Implement default, hover, pressed, selected and disabled states for interactive elements.
- `Play Match` is enabled for the supplied 11/11 squad state. If squad size falls below 11, disable it and show the reason directly underneath.
- Treat the JSON as authoritative if any wording or numeric value in a mock-up image differs.
