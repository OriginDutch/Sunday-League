# Sunday League — Game Design Document

> Living document. Only contains what Marcel has decided. Anything not decided is listed under **Open questions**.
> Rule for this project: Claude decides nothing unless Marcel explicitly says Claude may decide.
> Working agreement (2026-11-07): **everything we do, discuss, plan or decide is recorded in this document**, so nothing gets lost.

Last updated: 2026-11-07 (design session 1: economy, stadium, v0.1 scope)

---

## 1. Pitch

A 3D football game where you start as a club with nothing — a field, a few chairs and some balls — and grow step by step from below the bottom of the football pyramid to a world club with a real stadium, a real fanbase and world-class players.

You play the matches yourself (FIFA-style), and between matches you build up the club: stadium, fans, advertising, sponsors.

**Inspiration:** the TikTok series *FC Nowhere* ("the worst club in England") — an underdog club with absurd characters and a stadium that visibly grows.

## 2. Platform & tech

| Item | Decision |
|---|---|
| Platform | Desktop (not browser) |
| Engine | Godot 4 (PoC built on 4.7.2) |
| Language | GDScript in the PoC — **open question**, see §13 |
| Controls | Mouse + keyboard (WASD). Controller is a nice-to-have |

## 3. Tone

Starts unserious, slowly becomes more serious, but stays humorous throughout.

## 4. Structure of a save

- One long save with seasons.
- You start as a club from nothing and grow into a world club with world players.
- You can be relegated, but you **cannot be fired**. There is no trust meter.

## 5. Story & intro

1. Short intro to the game, introducing the characters in your starting squad and what's at stake: growing into a professional football club.
2. You're thrown straight into your first match: a **qualification match to be recognised as a football club**.
3. You always win this match. The intro cutscene has you score 1-0. After that the AI gets close to scoring, but in this match it **never** scores as many goals as you or more.
4. You then join **Non-League 3**.

## 6. The pyramid (fictional, English)

From bottom to top:

1. Non-League 3
2. Non-League 2
3. Non-League 1
4. League 10, League 9, League 8 … down to League 1
5. **"Premier Division"**, where you eventually play for real prizes

By the time you reach it, you're a big club with a real stadium and a real fanbase.

- Every tier has **20 teams → 38 league matches** per season, including Non-League 3.
- On top of league matches: cups, European matches and pre-season.
- League names are open, and so is the exact tier count (see §13).

### Promotion / relegation (leaning, not final)

- Leaning towards **3 up, 3 down**.
- Plus play-offs in which **5 teams from the lower league and 1 team from the upper league** fight for promotion/relegation. Roughly the Dutch system, without period titles.
- Exact play-off rules: open.

### Cups & Europe

- At least **1 cup per tier**, sometimes 2.
- European football via the main cup competition and the first division (exact qualification rules: open).

## 7. Matches

- **Always 11v11 on a full-size pitch.**
- Match length is adjustable. Default: **3 minutes per half**, teams switch sides at half-time → 6 minutes per match.
- **Switching (2026-11-07, revised):**
  - **Q** = the teammate nearest the ball; pressing again quickly cycles to the next nearest.
  - **Automatic switch** when: you pass (→ receiver), a teammate wins the ball, a loose ball is clearly closer (5 m+) to a teammate, or you've been beaten (→ nearest teammate goal-side of the ball carrier).
  - You still control your keeper while he holds the ball, and you take your own set pieces.
- **Passing (2026-11-07):** the passer plays the ball **into the run** of the receiver, and the **receiver comes towards the ball**. Long passes (30 m+) go through the air; the receiver gets under them.
- **Defending (2026-11-07):** more active: a second man covers goal-side of the ball carrier, AI reads and intercepts passes, tighter marking.
- **Team shape (2026-11-07, round 3):** out of possession the team defends as a **layered block**. The back line drops with the ball, midfield and attack keep their distance behind it (compressing when the ball is deep). The defender whose zone the ball carrier enters **steps out** to him.
- **Runs in possession (2026-11-07, round 3):** every few seconds each AI attacker picks a run: **in behind** (along the last line, staying onside), **coming short** (getting free ~9 m from the ball carrier), or **holding** position. Forwards go in behind more, midfielders come short more, defenders mostly hold. Applies to both teams.
- **Dead balls (2026-11-07):** a set piece is a real dead ball. Opponents keep **9.15 m** (throw-in **3 m**) until it's taken.
- Added by Claude (confirm or change): you can't win the ball from **straight behind** by just pressing (a tackle still works).
- **Sound (2026-11-07):** generated in code, no audio files. Kicks, referee whistle (kick-off, goals, set pieces, 2× at half time, 3× at full time), crowd cheer/groan/"ooh", and a crowd murmur that scales with attendance.
- **HUD (2026-11-07):** minimap bottom-right; arrows at the screen edge for teammates out of view.
- **Camera (2026-11-07):** further out by default, and the mouse wheel zooms during a match.
- WASD to move, mouse to aim passes/shots.
- **Player ratings affect the matches you play yourself.**
- Long term: real rules, with referees and linesmen.
- **Weather is a real system you feel in matches.** Example: in a rain match the ball rolls more sluggishly, so it becomes more of a battle for possession. Wind also exists (better balls are less affected by weather and wind).

### Play or autoplay

- You can play every match yourself for potentially higher rewards.
- Or autoplay: the result is a probability calculation based on player ratings.
- Autoplay rewards start at **75%** of playing yourself (tunable).

## 8. Players

- Players have **stats, names, positions and personalities**.
- Personality affects: atmosphere, attracting fans, stats, expectations about playing time, team chemistry ("that kind of thing").
- **Recruitment early on:** a **"Who can play for you" list** of random people: someone from the pub, from the street, a family member, the neighbour across the road, all kinds of random stuff.
- **Around the first League tier** you gradually move over to professional players on small contracts.
- **Recruitment later:** transfers from other clubs in the divisions, with money and contracts.

## 9. Your club

- Create your own club: **name, logo, colours, shirt & pattern, sponsors**.

## 10. Club building (tycoon side)

- Build, attract fans, advertising, attract sponsors.
- Building is done through **upgrades** (not free placement), with a **large list and many options**, so no two saves play the same or end up with the same stadium.
- Long-term stadium includes **trainers, staff, referees, linesmen** and above all **fans**.
- The number of fans grows with your club status, eventually perhaps **thousands, with simple animations**.

## 10a. Stadium & facilities (upgrades)

### What you start with and grow into
- **Very small things first:** one chair, one bench, one ball bag with better balls (roll further, shoot further, less affected by weather and wind), one hand lawnmower for better pitch recovery after bad weather (reduces a randomness factor).
- **Later:** staff slots and staff who **maintain** the basics (they don't upgrade them).
- **Eventually:** stands, floodlights, catering, shops and facilities.

### What upgrades do
- More income, more fans, better match play, better player development, etc.

### Building takes time
- Construction takes time, so you may choose to build during the **off-season**.
- During construction you **lose capacity**, and you see the build progress in phases: **25% → 50% → 75% → 100%**.
- The off-season is an auto-skip of x weeks.

### Location
- The ground grows **in place**, and it sits **in a residential area**.
- There's always enough room to expand, but you can see houses around it, or a car driving past on the nearby road.

### Promotion requirements
- Some tiers require certain stadium upgrades before you can be promoted, so you have something to work towards.
- **Requirements are kept low**: a pretty crappy ground should still be able to play at the highest level.

## 10e. Menus & UI (2026-11-07, in design)

- **Style:** fairly modern, **10–15% goofy**, UX/UI friendly, a clear and logical structure.
- **Language:** everything English for now, **built with other languages in mind** (no hard-coded strings in the long run).
- **Building:** you see directly what you're doing. Hovering e.g. a stand over 20 benches shows how it would look, what it costs and what it adds, before you confirm. Same for buildings like a chip shop.
- **Camera:** can rotate (also while building) so you can see every side of the ground.
- **Sections:** the ground is divided into **9 × 5 × 9 × 5 sections** around the pitch (corners stay open for now). Stands are built **section by section**. Where there's no stand you can still put a standing rail or chairs/benches. **Building zones on top of that** for buildings.
- **Demolishing / replacing:** you get money back **pro rata**. Upgrades **depreciate from 75% to 10% over ~3 seasons**.
- **Build time:** depends on the size of the upgrade (TBD). **Instant for now**; build phases come in a later round.
- **Settings (for now):** volume (separate for music / effects / crowd), match length, camera speed.
- **Navigation:** three mockups made (bottom dock, left sidebar, top tabs) — superseded by the ChatGPT design direction below.

### Design process (2026-11-07)
- **ChatGPT designs the UI; Claude builds it in Godot.** Claude wrote the designer brief: [UI Style Guide & Design Brief](https://claude.ai/artifact/QfV7Z8GDX2vMwBspqv6bkm) (what's decided, screen contents, Godot constraints, deliverables).
- Approach: **find a style first, then expand to more screens.**
- Round 1 (ChatGPT): good structure, but too premium (gold on charcoal, oak crest), photo/3D icon art, ground hidden. Feedback sent.
- Round 2: ground visible, one icon style, consistent numbers; still premium colours. Feedback sent: three colour variants on a frozen layout.
- Round 3: three themes delivered with tokens (`design/ui-handoff/sunday_league_ui_tokens.json` + `README_FOR_CLAUDE.md`): Clubhouse Canteen, Chalkboard, Club Colours (red & white).

### Chosen UI style (Marcel, 2026-11-07)
- **Chalkboard style in Clubhouse Canteen colours:** panel #20372A (93% opacity), border #526D57, text #F5F0DF, muted #C0C9B9, accent #E8D9A8, success #79C68B, warning #E5AE54, danger #D66B61. Full values in the tokens JSON.
- **Fonts:** Barlow Semi Condensed (400–700) for all functional UI; **Caveat** (500–600) for the ticker, taglines **and headings** (club name, "Our Goal", "Next Match") — for now. Stats, buttons and instructions stay in Barlow.
- **Layout:** top stats bar; "Our Goal" card left; "Next Match" card right with **both crests** (so you see home vs away); **slim floating bottom strip** (ticker + navigation on one line, a little above the bottom edge so you still glimpse the ground); centre of the ground kept clear.
- Chalk underlines under headings, chalky progress-bar fill, homemade single-colour crests (SVG, recolourable later) — in `design/ui-handoff/`.
- Mock-up of this style: "Hub · Canteen colours, chalkboard style" on the [Hub mockups canvas](https://claude.ai/artifact/89eq9cBSogTe6xLhRZL9EZ) (has a texture switch).

### Panel texture — still open
- ChatGPT's 512 px texture: even fine grain, reads as felt/noise. **Rejected.**
- Claude's procedural textures (subtle / medium / bold; eraser wipes, haze, ghost strokes; `design/textures/`): **rejected** ("buiten smaak").
- Next: a new ChatGPT round with three directions — A) real photographed chalkboard, B) illustrated/stylised, C) flat panels with chalk details only (outlines, corner marks, doodles). Prompt is ready; waiting for Marcel's ChatGPT limit to reset.


## 10f. 3D assets — first test: The Shed (2026-11-07)
**Why:** test whether Claude can build good 3D models (see §13 "3D assets").

**Brief (Marcel):**
- Asset: *The Shed*, the first covered stand.
- Style: "High quality Low Poly" — references were 7 screenshots: low-poly stadium renders, a red-seat stand, a cable-stayed stand, a real non-league ground, and Halifax-style grounds with containers, bleachers and wooden terraces.
- A first stand has **3 rows**. One section is **11.5 m wide** (full side = 9 sections = 103.5 m, without corners).
- Generic colours for now; club colours must be usable later.
- More detail is better: "het moet als een echt stadion voelen, niet een betonnen bak".
- Construction: **steel frame + corrugated roof**. Seating: **roof + plastic seats**.

**What Claude built** (numbers are Claude's picks, tunable):
- 11.5 m wide, ~5.2 m deep, roof 4.55 m at the front sloping to 4.05 m at the back.
- Raised front walkway (0.45 m), 3 concrete steps (0.85 m deep, 0.42 m rise) with yellow nosings, central gangway with half-steps and a handrail.
- 57 tip-up seats (0.5 m pitch) on pedestals.
- Brick front wall with 4 blank advert boards and a white crush rail.
- 4 front + 4 back steel columns with knee braces, rafters, purlins, eaves beam.
- Corrugated roof (ribbed), corrugated back wall with a door, corrugated side screens on the back half, gutter + downpipes, fascia band (room for the club name later).
- ~2,350 faces, 17 meshes (joined per material → few draw calls).
- Recolourable materials by name: `Club_Primary_Seats`, `Club_Primary_Trim`, `Club_Secondary_Fascia`, `Advert_1..3`.

**Pipeline:** Blender 5.2 (`bpy`) build script, no hand modelling: `tools/blender/build_shed.py` → `assets/models/the_shed.glb` (+ previews with `--render`). In-game preview: `godot -- --shed` puts it on the north side (dev only, no gameplay effect).

**Seen in the first renders and fixed:** roof sheet tilted the wrong way; front wall hid the front row (walkway and steps raised).

**Rules (Marcel, 2026-11-07):**
- Bought per section (11.5 m).
- Adjacent sections join up: the side screen between them is removed (only the outer ends of a run keep a side screen). Not built yet.
- Club colours: buyable upgrade, applied by the player (recolours `Club_Primary_*` / `Club_Secondary_*`).

**Known limits:** colours in Godot look flatter than in Blender (game lighting, not the model); no textures yet (flat colours, matches low-poly).

## 10g. Lighting test (2026-11-07)
**Why:** in-game the stand looked flatter than in Blender; the grass looked neon.

**Marcel's choice:** do options 1–4, behind a dev flag first (compare before it becomes the default); option 5 as an extra dev flag for now (later possibly an in-game graphics setting).
- `--new-light` = options 1–4:
  1. AgX tonemapping (as in the Blender renders), ambient 0.55 → 0.5
  2. SSAO (radius 1.2, intensity 2.2, power 1.6)
  3. Lower, warmer sun (-40°, warm white, energy 1.7), softer shadows (blur 1.6, soft-medium filter), shadow distance 80 → 140 m
  4. Less neon grass (stripes 0.25/0.48/0.20 and 0.21/0.42/0.17)
- `--fancy-light` = 1–4 + option 5: SDFGI global illumination, light glow, faint distance haze.
- **Decided (Marcel, 2026-11-07): fancy is the default** (runs smooth on his RX 9070 XT). `--new-light` and `--old-light` stay as dev flags.
- All numbers are Claude's picks (tunable). Before/after shots in `design/lighting/`.
- Option 5 could not be screenshotted here (software renderer too slow for SDFGI); runs without errors, Marcel judges it on his GPU.
- First `--new-light` attempt was too dark/muddy (ambient 0.38, sun 1.35); brightened.
- Marcel tested both (2026-11-07): leans towards **fancy** — "iets meer helder en voelt wat zonniger". Not yet made the default.

## 10h. Audio — crowd sound (2026-11-07)
- Marcel heard "wind": that was Claude's procedural crowd murmur (looping filtered noise). Verdict: **not usable**.
- Tried: Suno with crowd-ambience prompts → **didn't work**.
- Murmur loop **removed** (Marcel, 2026-11-07: "moet er nu uit"). Then **all** procedural crowd sounds removed too (cheer/groan/ooh; Marcel: "alle ruis geluiden mogen eruit"). Kick + whistle stay (tonal, not noise) unless Marcel says otherwise.
- **First recordings in (2026-11-07):** Marcel supplied Motion Array files. Kept: goal cheers #1 (1, 2, last) and #2 (1–3) → `assets/audio/crowd/cheer_1..6.ogg`; all ball kicks → `kicks/kick_1..7.ogg` (normal) and `kick_big_1..4.ogg` ("goalie kicks").
- How they play (Claude's picks, tunable): kicks at ≥20 m/s use the big set; random pick, slight pitch variation. Goal cheer only on a home goal, random of 6, full volume for 8 s then 4 s fade. Volume scales with attendance (fans/100), with a minimum (see below).
- Kicks re-cut (Marcel: "trappen moet een instant geluid geven"): some clips had 0.2–0.25 s silence in front and the 50 ms fade-in softened the hit. Now cut 2 ms before the transient, 1 ms fade-in, peak-normalised, stored as **.wav** (no decode delay). Cheers stay .ogg.
- Licence: Marcel: the files are royalty free, **repo stays public and the audio goes into git** (2026-11-07). Code still skips missing files.
- Cheers re-cut to Marcel's timings (relative to the first cut): #1 4–10 s soft end, #2 7–13 s, #3 7.25–13.25 s (build-up, no sharp hit, so 7.25), #4 4.5–10.5 s, #5 5–8 s (short); hard start (5 ms), ~1 s fade-out (1.5 s on #1). #6 unchanged (no instruction yet).
- Cheers v3 (Marcel's second round): #1–#3 start and end 0.25 s later, #4 unchanged, #5 starts 0.25 s earlier (4.75–8 s), then moved to 3.75–8 s, #6 now cut too (3.75–11 s). Entry a bit more gradual but still abrupt (fade-in 5 → 50 ms), quicker stop (fade-out 1.0 → 0.6 s; 1.0 s on #1, 0.5 s on #5). Peaks ≤ -1.5 dB, no clipping.
- Minimum cheer volume (Marcel: "zeker, moeten we finetunen"): floor 0.35 of full (≈ -9 dB), Claude's pick.
- Next: real recordings from free/CC0 libraries (Marcel downloads, Claude cuts + loops + builds in). Open: keep the procedural sounds as fallback or remove them.


## 10i. 3D POC #2 — big two-tier stand (2026-11-07)
**Marcel's ask:** a big stand as a POC, including floodlights, stairs, aisles, two tiers, a roof, roof beams, and some people spread over the seats.

**Answers so far:**
- Width: **full long side**, 9 sections = 103.5 m, no corners.
- Roof: **cantilever** (no columns in front of the view).
- Between the tiers: **a row of skyboxes** (glass boxes with balcony).
- Floodlights: **both** — light bar on the roof edge + separate masts.
- Rows: **20 lower / 15 upper**.
- People: **~30% full, mostly in club colours** (low-poly figures).
- Seats: **club name spelled out in the seats** (second colour).
- Back: **simple facade** (cladding + stair cores) for now, to be revisited later.
- Seat text for the POC: **"SUNDAY LEAGUE"** (Marcel). Go-ahead given 2026-11-07.

**What Claude built** (numbers are Claude's picks, tunable):
- 103.5 m wide, ~35 m deep, roof front edge ~26 m high, cantilevered ~36 m from the rear columns (no columns in front of the view); white warren trusses at every section boundary, rear columns + back-stay ties, corrugated roof with a 4 m translucent strip at the front, club-colour fascia.
- Lower tier: 20 rows (0.80 m tread, 0.36 m rise) on a raised walkway behind a pitch-side wall with a club-colour band; 8 stairs with yellow nosings and handrails; cross-aisle + 4 tunnels (see feedback round 1).
- Skybox level: 27 glass boxes (3 per section) with warm ceiling lights, partitions and a bar; balcony with 2 rows of premium seats and a glass balustrade.
- Upper tier: 15 rows (0.85 m tread, 0.55 m rise, steeper), front parapet with a black LED band + adverts, aisles + handrails, rear walkway; "SUNDAY LEAGUE" in white seats (5×7 pixel font, 2 seats × 2 rows per pixel).
- Floodlights: a gantry with 32 lamps along the roof edge + lattice masts (40 m) with 6×4 lamp heads aimed at the centre spot (now 4, see feedback round 1).
- Ends: clad end walls + glazed wind screens up to the roof. Back: simple clad facade (Marcel's choice for now), window band, 3 stair cores with entrances + canopies, "SUNDAY LEAGUE" sign.
- Pitch-side: advert boards + 2 perspex dugouts.
- 6,516 seats (6,354 + 162 premium) and 1,872 fans (29%, fuller in the middle; 65% primary shirts, 15% secondary, 20% other colours; 3 skin tones).
- Note: Claude's estimate before building was ~8,500 seats; with 20 seats per 11.5 m section (aisles take the rest) it is ~6,500.

**How it is built:**
- `tools/blender/build_big_stand.py` → `assets/models/big_stand.glb` (structure, ~22k faces, 2.4 MB) + `big_stand_layout.json` (every seat/fan).
- In Godot `scripts/big_stand.gd` draws seats and fans with MultiMesh + `instanced_parts.gdshader` (part mask in vertex colour, colour per instance). `set_club_colours(primary, secondary)` recolours seats, the club name, club shirts and the `Club_*` materials of the structure live — ready for the club colours upgrade (§10f).
- Dev: `godot -- --bigstand` (north side, 6 m behind the touchline); `--club-colours=C8102E,F2F2F2` to demo recolouring.

**Marcel's feedback round 1 (2026-11-07) and what changed:**
- "Tunnels connect straight onto the seats, not to the stairs — unrealistic." Marcel chose: tunnels on the stairs + a cross-aisle + the stair goes around the tunnel and merges again. Built: a 1.6 m cross-aisle behind row 9 over the full width (rows behind it start 0.54 m higher, with a rail on that edge, open at every stair); 4 tunnels (first on the stairs at x = ±5.75 and ±28.75, moved in round 2) opening onto the cross-aisle; behind it the stair splits into two 0.9 m stairs alongside the tunnel walls, which merge on a landing above the tunnel mouth into one stair again. Steps are now max ~0.3 m (3 steps where the cross-aisle jump is).
- "The floodlight mast stands behind the pitch, not in the corner." Marcel chose: **masts in all 4 corners**. Now a separate model `assets/models/floodlight_mast.glb` (the far-side masts don't belong to the stand), placed 8 m diagonally out from each corner flag, aimed at the centre spot.
- "Everyone wears black trousers." Now 6 trouser colours (jeans, dark, black, grey, beige, light jeans), packed with the skin tone into the instance data.
- Seats now 6,464, fans 1,830 (the tunnel zones took some seats).
- Godot loads BigStand by path (a new class_name made the game fail before the editor rescanned), and a missing import gives a clear message. New models/sounds need `godot --path . --headless --import` (or opening the editor once) after a pull.

**Marcel's feedback round 2 (2026-11-07):** the two tunnels at x = ±5.75 sat close together in the middle (11.5 m apart vs 23 m to the next). Options offered: 2 tunnels at ±17.25, 3 with an extra centre stair, or 4 at ±17.25/±40.25. **Marcel chose 4 at ±17.25 and ±40.25** (spacing 23 / 34.5 / 23 m).

**Modular stands (discussed 2026-11-07):** the POC is one model for the full side; the script is built per 11.5 m section, so it can be split. Marcel:
- The club name only needs to be in **one place**; the player may enter a different text in an input field with a **max number of characters**.
- Tiers are upgradable **per section** (a second tier, maybe a third one day), so sections with different tier counts stand side by side.
- Open: where the one text goes and how big; how the upper tier is reached in a modular build (see below); whether sections replace the chair/bench slots.

**POC verdict (Marcel, 2026-11-07):** "for a POC we now know enough that it is possible." Upper-tier access and the club-name size stay open for the real build. **Next step: design the series of stand stages** (between and above chairs/benches → Shed → big two-tier; how many tiers, how many styles, corners). Claude's proposal is in the chat; nothing decided yet.

**Stand stages discussion (2026-11-07):** Claude proposed a ladder of 10 stages (0 grass/rope … 9 third tier), styles growing with the stage, open corners → corner infill → closed bowl. Marcel: is ~9 stages not too few from a gameplay view? And "styles" should also mean **ground shapes**: rectangular with corners, no corners, Spanish (almost no roof), big rounded corners, fully round/oval, partly cornered. Nothing decided yet.
- Claude's answer: split **stages** (big visual jumps, costly 3D) from **upgrades within a stage** (rows, roof, seat type, LED, heating, scoreboard, skyboxes, kiosk…), and treat stands as a **cross-section profile swept along a path** (straight side, arc for a rounded corner, all arc for an oval), with three separate axes: profile (stage), shape (corners), roof.
- **Decided (Marcel, 2026-11-07):**
  1. Stages + upgrades within a stage: yes in principle. Row counts and the size of the jumps are still to be discussed.
  2. Shape: one shape for the whole stadium (Claude's reading of "dat lijkt me het beste" — to confirm), plus switching individual corners on/off as customisation.
  3. The shape can be changed later (rebuild), from a gameplay point of view.
  4. Career length: **at least 14 seasons, probably 20–25+**.
  - Addition on shapes (Marcel): define a set of **common shapes/setups (presets)** the player chooses from.
- Next topic (Marcel's pick): **rows and jumps per stage**.
- Claude's rows proposal per section (20 seats/row): bleachers 3→5→7, Shed 3→5→8, main stand 10→12→15, modern tier 15→20→25, 2nd tier +10→15→20, 3rd tier +10→15 (~1,200/section max, ~36k + corners). Open questions to Marcel: standing branch, all-seater rule, demolition on a stage jump, size of the jumps.
- Real-world reference (Marcel asked, web research 2026-11-07): small non-league stands ~4 rows; League Two / National League stands ~12–19 rows; Emirates lower tier up to ~row 29, upper tier up to ~row 40; ~25 seats per row between stairs is common. Real ground rules: League Two entry needs >5,000 capacity and >1,000 seats. → Claude's upper tiers are on the low side.
- **Decided (Marcel, 2026-11-07): the lower tier can grow up to 40 rows** — a massive stadium if the player wants it; it's the player's choice, not required. Promotion requirements already exist (§10a, kept low) — the real-world numbers above are reference only.
- **Decided (Marcel, 2026-11-07):**
  - **Standing terraces as a side branch**: yes.
  - **All-seater rule: dropped** (Marcel: too deep into real rules for a semi-arcade game). Instead (2026-11-07):
    - **No seating obligation anywhere** — standing stays standing, also at the top and in Europe; no rail seats.
    - **Standing only on the first (lowest) tier.**
    - Standing vs seating is a **flavour choice**: standing = more atmosphere/fans, less revenue per place; seating = the reverse. (Numbers still open.)
  - **Stage jump**: **1 week demolition, then construction of the new replacement stand starts** (its own build time; how long per type is still open).
  - **Max rows: lower 40 + second 30 + third 20** (90 rows) — the "super stadium" for players who want to and can get there.
  - Marcel asked whether 2 × 40 rows is insane in depth and for real examples (answered in chat: deepest single banks are ~40 m high, e.g. Dortmund's Südtribüne; stacking two 40-row tiers is rare).

**Seen and fixed during the build:** fans too wide (letters unreadable) → slimmer; open gap between back wall and roof → clad up to the roof, glazed end screens; two stacked rows of colourful boards → front wall now concrete + club band; facade sign was mirrored and hidden behind the centre core/columns → mirrored, moved up, narrower.

**Known limits:** the seat text is only partly readable when 30% full (fans in white shirts look like letter pixels, aisles break letters); the rear back-stays cross the facade sign in 3/4 views; Godot shots here use `--new-light` (fancy/SDFGI too slow on the software renderer); stands are not yet in the hub/economy (sections vs slots still open).

## 10b. Economy

### Income
Every income source exists in every tier, but in the lowest tiers the amounts are genuinely tiny (think €1.70 TV money for a whole season: one beer).

| Source | Notes |
|---|---|
| Ticket sales | |
| Concessions (food/drinks) | Choose a brand. More popular brands sell better but need a bigger base investment |
| Merchandise | Choose a brand. More popular brands sell better but need a bigger base investment |
| Sponsors | Some are received better by fans. Longer contracts and contract renewals automatically raise approval |
| Advertising boards | |
| Prize money | |
| TV money | |
| Investors | Cost you a hit to fan approval |
| Transfers | Selling and loaning out players |

- Brand, sponsor and similar choices are **contracts per season (or several seasons)**, not something you manage per match.

### Expenses
- Salaries, stadium building, maintenance, transfers, staff, travel, fines.
- Player performance bonuses.
- Exact list partly open.

### Reference model (draft, 2026-11-07)
- Marcel: "one home match of income" is no fixed unit (depends on capacity, attendance, concessions, sponsors…). Agreed approach: a fixed **reference club per division** (average club at that level); prices are derived from it and then **stay fixed in the game**, so doing better than average lets you build sooner.
- Draft workbook: `design/economy/Sunday_League_economy_model.xlsx` (built by `build_economy_model.py`). Tab *Reference club*: attendance, ticket, spend per visitor, sponsors, TV, prize money per division → income per home match/season. Tab *Stand prices*: per stage → cost per section/place/full ground.
- First try priced stands as "N home matches of all-in income" → exploded at the top (TV/sponsors; ~€530k per place for a third tier). Now priced by **target payback in seasons** from the extra tickets + spend of those places (0.3 season for chairs … 3 seasons for a third tier). Gives ~€12/place for chairs (= v0.1's €12 chair) up to ~€2.4k/place for a third tier.
- All values are Claude's first guesses; nothing decided. Known gap: salaries/expenses are not modelled yet, so top clubs look very rich.
- **v2 (2026-11-07, Marcel: "onderbouwen, dan een middenweg die de gameplay smooth laat lijken"):** every division now has a **real-world column** (English football 2024/25, £, with 20 sources on a *Sources* tab) next to the **game column** (€, middle ground). Proposed mapping: Premier Division = Premier League, League 1 = Championship, League 2 = League One, League 3 = League Two, League 4 = National League, League 5 = NL North/South, League 6–10 = Steps 3–7, Non-League 1–3 = below the official pyramid (estimates only).
  - Middle ground: follows reality where it's smooth; flattens the two real cliffs (National League → League Two central money ~25×, Championship → Premier League ~10–15×). Result: season income grows ~1.9–2.7× per division, 3.6× into the Premier Division.
  - **Accepted for now (Marcel, 2026-11-07):** mapping, game values and the cliff flattening — "voor nu goed, open voor tweaking". Next: expenses (salaries etc.) are still missing.
- **v3 — expenses (2026-11-07, Marcel picked this as next step):** new *Expenses* tab, real vs game, 7 more sources.
  - Real: clubs mostly lose money (avg pre-tax 2024/25: PL −£31.1m, Championship −£15.1m, League One −£5m, League Two −£2.6m); wages/revenue 65% PL, ~96% Championship; pay from £20–40 per game at Step 6 to ~£60k/week in the PL.
  - Game (Claude's proposal): costs as % of the reference club's income — wages, staff, ground running, travel/match costs — leaving a **surplus to build with: 55% at the bottom → 20% at the top**.
  - **Pace finding (open):** surplus ÷ cost per section of the stage you'd build there → ~0.4–1.5 sections per season up to League 5, but 5–40 per season from League 3 up (top income is TV/sponsors, stand prices are priced on tickets). Options discussed with Marcel, nothing decided.
  - Marcel (2026-11-07): transfer fees are not in the model yet and will drain money at the top ("70 miljoen voor een verdediger"). → Transfers as the big money sink higher up; still to be worked out.
  - **Decided (Marcel, 2026-11-07):** the surplus is a **free choice: build the stadium or strengthen the squad**. In the end you need both to some degree — too little capacity squeezes income or blocks promotion (requirements); players not good enough means never getting promoted.
  - **Decided (Marcel, 2026-11-07): player ratings on a 1–99 scale**; 99 is almost unreachable — "a Messi, but even better".
- **v4 — transfers & ratings (2026-11-07, proposal, nothing decided):** new *Transfers* tab, 4 more sources (S28–S31).
  - Real: gross transfer spend summer 2025 — Premier League £3.0bn (~£150m per club), Championship £240m (~£10m per club); below that fees are rare, a £0.6–1.5m non-league fee is a record/outlier. EA FC 26 top ratings: Mbappé 92, Salah 91, Haaland/Rodri/Van Dijk 90.
  - **Value curve (proposal):** value = €4.5m × 1.25^(rating − 80). Exponential so +10 rating ≈ ×9 value: 99 ≈ €312m, 90 ≈ €42m, 80 = €4.5m, 70 ≈ €0.5m, 60 ≈ €52k, 50 ≈ €5.6k, below 40 practically free (fits "amateurs free"). Calibrated to the game economy, not real fees (game top income is flattened).
  - **Avg squad rating per division (Claude's estimate):** NL3 15 → NL1 28 → L10 33 … L5 53 → L4 57 → L3 62 → L2 65 → L1 70 → Premier 80.
  - **Transfer share of surplus (proposal):** 0% at the bottom → 50% League 4 → 80–85% League 1/Premier. Signing = avg + 2 rating.
  - **Result:** pace after transfers ~0.3–1.1 sections per season up to League 4, ~2–6 from League 3 up (was 5–40). Premier: ~2.5 signings of ~82 per season, ~6 sections.
  - Real reference (Transfermarkt, July 2026): young 90+ players are worth €200–220m (Haaland, Yamal, Mbappé); older 90s (Salah, Van Dijk, 30+) far less; Messi ~$17m. Market value ≠ actual fee.
  - **Decided (Marcel, 2026-11-07): age counts in player value** — you can pick up an old star fairly cheaply, but you get less time out of him. Shape and strength of the age factor still open.
  - **Decided (Marcel, 2026-11-07): FIFA-style potentials.** Every player has a current rating and a potential (ceiling).
    - Potential is **visible with light obfuscation** (shown roughly, e.g. a range).
    - Potential **can change**.
    - Growth is driven by **playing time, ratings, training complex, injuries** (among others).
      - "Ratings" here = the **player's own rating, what's left of his stats** (not match grades). Marcel's example: a player who once had 90 potential but now sits at a stats level of 30 will want to stop → a big drop from his peak/potential raises the retirement chance.
    - A player **stops growing around his peak**, which differs per player (one at 27, another at 32).
    - **Retirement:** the older the player, the higher the chance he stops, but it also depends on keeping his rating up, playing time, contract length and injuries.
    - Value now = rating + potential + age (replaces the blunt age multiplier table Claude showed; exact formula in the model, tunable).

### Playing vs autoplay
- One baseline: **playing yourself = 100% of match rewards, autoplay = 75%**.

### Amateur players (non-league)
- In non-league you have no money, so players sometimes get nothing at all: **amateur contract, free to leave**.
- If you think a player is worth it, you can pay a **small fee per match** so he's more likely to stay.

### Running out of money
- You **can't go bankrupt** and lose nothing for now.
- Without money, **players play worse and maintenance gets worse**.
- **Safety net against a death spiral: TBD.** Ideas from Marcel: community intervention, a rich butcher, the municipality, random events that save you.

## 10c. Fan approval

- Fan approval is a core resource, **separate from the number of fans**.
- **Higher approval → more fans and faster growth. Lower approval → slower growth, down to slightly negative.**
- Affected by (so far): investors (negative), sponsors (well-received ones, long contracts and renewals raise it), brand choices.

## 10d. Progression pace

- **Faster at the bottom, slower at the top.**
- Non-league can be an almost free promotion each season, as long as you don't mess up.
- Higher up, the guideline is **2–3 seasons per division**. If you know what you're doing, you can go up every season.

## 11. Proof of concept — status

Built in Godot 4.7.2 / GDScript, all visuals from primitives in code (no assets).

**Verdict (Marcel):** fun, "challenging but not hard". Fine-tuning comes later.

What's in it now (v4):
- **11v11, 4-3-3 for both teams, full-size pitch** (105 x 68 m, goals 7.32 x 2.44, real markings).
- **Two halves of 3 minutes**, teams switch sides at half-time.
- **Simple restarts:** throw-in, corner, goal kick. The ball is placed, the nearest player takes it (the keeper takes goal kicks) and opponents back off 9.15 m.
- **Offside:** judged at the moment the ball is played. Punished when the offside player touches the ball → free kick. No offside from throw-ins, corners and goal kicks.
- Playable with an auto-switching controlled player, WASD + mouse aim, passing (receiver ring turns red if he's offside), charged shots (aim arrow + goal-target marker), tackles.
- AI: one chaser per team, zonal shape that shifts with the ball, picks up attackers entering its zone, support runs that stay onside, passing under pressure, shooting in range. Keepers react with a delay and parry.
- You control your own keeper while he holds the ball (including goal kicks).
- Camera follows ball/player with look-ahead.
- Difficulty values approved by Marcel for now.

## 11b. Milestone v0.1

**Goal:** mainly to prove the club side is fun (a rough PoC #2), and a little bit of being the first real playable version.

**Done when:** you can grow to **100 supporters on chairs and benches who actually show up, pay, cheer and react to what happens**.

| Feature | v0.1 |
|---|---|
| Money | **In**: ticket sales only (concessions later) |
| Visible micro-upgrades (chair, bench, ball bag, lawnmower, …) | **In** |
| "Who can play for you" list | **In** |
| Player names | **In** |
| Fans + fan approval | **In** |
| Save / load | **In** |
| Stats that affect matches | Later |
| Intro + scripted qualification match | Later |
| Club creation (name / colours / logo) | Later |
| Full league season (20 teams, table, fixtures) | Later |
| Play or autoplay choice | Later |
| Amateur contracts / players leaving | Later |
| Weather | Later |
| Promotion | Later |
| Cups | Later |

**Matches in v0.1:** random friendlies.

**Decisions for the v0.1 build (2026-11-07):**
- Upgrades: **chair** (1 seat) and **bench** (several seats). You **pick a slot** for each one along the touchlines.
- New fans come from **winning** and **facilities** (seats), scaled by approval.
- Ticket price is **fixed**.
- Squad: you start with a few people and **recruit from the list to fill 11**. You **can't play until you have 11**. Recruiting is **free**.
- Approval changes with **results, entertainment** (goals, saves, tackles) and **seating** (fans without a seat get grumpier).
- **Autosave after each match.**
- Claude may pick the starting numbers (marked as tunable).

**Fans in v0.1:**
- Fans **actually sit on the chairs and benches** you've placed.
- Fans still come when there's no seat for them, but then **they don't pay**. They only pay for a seat (or a standing place on a stand).
- **Later:** charging "real" entry for regular standing places too.
- Fans cheer, jump, some wander around a little, gather in groups, and react to tackles and saves.
- **Chants (2026-11-07):** speech bubbles above fans ("WHO ARE YA?!", "REF YOU'RE BLIND!", "Is the bar open at half time?"), both idle and reacting to goals, saves, tackles and offside calls.
- **Chairs stack (2026-11-07):** up to **4 chairs per section**, bought one at a time. Per seat that's more expensive than a bench (4 × £12 = £48 vs £40), with the same number of seats.
- **Saving (2026-11-07):** also saves right after buying seating, recruiting, or starting a new game.

## 11c. PoC #2 (v0.1 build) — status

Built on top of the 11v11 PoC.

- **Hub** between matches:
  - top bar with money, fans, approval, seats, squad, record and v0.1 goal progress
  - shop (chair/bench), "Who can play for you" list with Recruit buttons, squad with positions
  - "Play friendly" button, disabled until you have 11
- **Placing seating:** buy → free slots light up (20 per touchline) → click one.
- **Friendlies** against random opponents ("Railway Tavern Athletic", …). Some opponents are a bit quicker than others.
- **Crowd:**
  - every fan is visible: seated (paying) on your chairs/benches, the rest standing for free in small groups along the touchline
  - they breathe/sway and shuffle around a little
  - they jump and cheer on your goals, slump on goals against, and react to saves and tackles
- **Names:** your players carry their names; the controlled player's name is shown above him, and the scorer's name on a goal.
- **Post-match summary:**
  - result, attendance (seated/standing), ticket income
  - fans before/after, approval before/after with the breakdown
  - then autosave
- Save file: `user://save.json` (Windows: `%APPDATA%\Godot\app_userdata\Sunday League\save.json`).

**Starting numbers picked by Claude (tunable, top of `scripts/club_state.gd`):**

| Value | Number |
|---|---|
| Start money / fans / approval | £60 / 5 / 50% |
| Start squad | 4 people |
| List size | 8 |
| Ticket price | £2 per seated fan |
| Chair / bench | £12 (1 seat) / £40 (4 seats) |
| Slots | 20 per touchline (max 160 seats) |
| Fan growth per match | win 6, draw 2.5, loss 0.5, +0.05 per seat, × approval factor (−0.3 … +1.5) |
| Approval per match | win +6, draw +1, loss −5, entertainment up to +6, seating up to −6 |

Simulated pace to 100 paying supporters: about **20 matches** when winning half of them (~2 hours of play), about **30** when winning only 20%. Money is the bottleneck early on.

**Added by Claude without a decision (please confirm or change):**
- Hub camera: WASD/arrows to pan, mouse wheel to zoom (needed to see and pick slots on a 105 m pitch).
- "New game" button in the hub (click twice) that wipes the save.
- Positions follow recruitment order (1st = GK, then LB, CB, …). Placeholder until positions are designed.

**Side effects to be aware of:**
- R (restart match) still works during a friendly, as in the PoC.



| Date | Decision |
|---|---|
| 2026-11-06 | 3D desktop game, Godot 4 |
| 2026-11-06 | Fictional English pyramid |
| 2026-11-06 | Control switches to the player nearest the ball; WASD + mouse; controller nice-to-have |
| 2026-11-06 | Tycoon via upgrades with a large list of options |
| 2026-11-07 | Matches always 11v11, full-size pitch |
| 2026-11-07 | GDD as a markdown file, in English |
| 2026-11-07 | Story intro + scripted qualification match (see §5) |
| 2026-11-07 | Play or autoplay, autoplay at 75% rewards |
| 2026-11-07 | Can be relegated, can't be fired, no trust meter |
| 2026-11-07 | 20 teams / 38 matches in every tier |
| 2026-11-07 | Own club: name, logo, colours, shirt & pattern, sponsors |
| 2026-11-07 | Game title: **Sunday League**; project folder `Desktop\Projects\Sunday League` |
| 2026-11-07 | Economy: income/expense sources, contracts per season, no bankruptcy (see §10b) |
| 2026-11-07 | Play 100% / autoplay 75% as the single baseline |
| 2026-11-07 | Fan approval as a core resource, separate from fan count (§10c) |
| 2026-11-07 | Pace: fast through non-league, 2–3 seasons per division higher up (§10d) |
| 2026-11-07 | Stadium: tiny upgrades first, grows in place in a residential area, build time, low promotion requirements (§10a) |
| 2026-11-07 | Weather is a real match system; construction in visible phases with capacity loss; "Who can play for you" recruitment list |
| 2026-11-07 | v0.1 scope and done-criterion (§11b); random friendlies, ticket sales only, fans pay only for a seat |
| 2026-11-07 | v0.1 build: chair + bench, pick a slot, growth from winning + facilities, fixed ticket price, recruit to 11 (free, can't play short), approval from results/entertainment/seating, autosave after match |
| 2026-11-07 | Working agreement: everything discussed/planned/decided goes into the GDD |
| 2026-11-07 | UI: ChatGPT designs, Claude builds; chosen style = Chalkboard style in Clubhouse Canteen colours, Barlow + Caveat (Caveat also for headings for now), slim floating bottom strip, both crests in Next Match |
| 2026-11-07 | Panel texture: ChatGPT grain and Claude's procedural versions rejected; new ChatGPT round with 3 directions pending |
| 2026-11-07 | 3D test asset The Shed: "High quality Low Poly", 3 rows, 11.5 m sections (9 per side = 103.5 m), steel + corrugated roof, plastic seats, generic colours with recolourable club materials (§10f) |
| 2026-11-07 | Stands bought per section; side screen disappears between adjacent sections; club colours are a buyable upgrade you apply yourself (§10f) |
| 2026-11-07 | Workflow: Claude commits + pushes, Marcel pulls manually (no auto-pull for now) |
| 2026-11-07 | Surplus = free choice between stadium and squad (both needed); player ratings 1–99, 99 near-impossible |
| 2026-11-07 | Economy reference model v2 (real vs game, cliffs flattened) accepted for now, open for tweaking (§10b) |
| 2026-11-07 | Economy model v4: Transfers tab + 1–99 rating value curve (proposal, §10b) |
| 2026-11-07 | Player value depends on age too: old stars cheap but short-lived (§10b) |
| 2026-11-07 | FIFA-style potentials: visible with light obfuscation, can change, growth from playing time/ratings/training complex/injuries, per-player peak 27–32, retirement chance rises with age (§10b) |
| 2026-11-07 | Lower tier can grow up to 40 rows (player's choice); max 40+30+20 = super stadium; standing branch (first tier only, no all-seater rule, standing = atmosphere vs seats = revenue); stage jump = 1 week demolition then build |
| 2026-11-07 | Stands: stages + upgrades within stages; one stadium shape + per-corner on/off; shape changeable later; career ≥14 seasons, likely 20–25+ |
| 2026-11-07 | Big stand POC: full side, cantilever, skyboxes, floodlight bar + masts, 20/15 rows, ~30% fans in club colours, club name in seats, simple facade (§10i) |
| 2026-11-07 | Fancy lighting is the default; audio goes into the public repo (royalty free); minimum cheer volume |
| 2026-11-07 | Lighting: options 1–4 behind `--new-light`, option 5 behind `--fancy-light`; old lighting stays default until Marcel compares (§10g) |
| 2026-11-07 | Menus/UI: style, English with i18n in mind, live build preview, rotatable camera, 9×5×9×5 sections, pro-rata demolish refund (75%→10% over ~3 seasons), instant build for now, settings list |
| 2026-11-07 | Playtest round 3: layered defensive block, step-out, attacking runs (in behind / come short / hold) |
| 2026-11-07 | Playtest round 2: Q nearest+cycle, 4 auto-switch rules, receiver comes to the ball, active defending, real dead balls, stackable chairs, save after purchases, sound, minimap + edge arrows, chants |
| 2026-11-07 | Playtest fixes: auto-switch only on your passes, Q = nearest to mouse, passes into the run, camera further out + wheel zoom |
| 2026-11-07 | PoC: simple restarts (throw-in, corner, goal kick), 4-3-3, halves + switching sides, offside |

## 13. Open questions

**Name**
- Other things already use the name "Sunday League": a browser football/club-management game (github MrPavian/sunday-league), Steam game *Sunday League Manager: Horse & Spoon* (2025), an itch.io game *Sunday League Football* (2018), a board game. Fine as working title; worth deciding before going public.

**Tech**
- GDScript (as in the PoC) or C#? Switching later means a rewrite.
- Art style: UI decided (§10e). 3D direction from Marcel: "High quality Low Poly" (§10f); final verdict waits on The Shed test.

**Pyramid**
- League names.
- Exact tier count: is League 1 the "Premier Division", or does the Premier Division sit above League 1?
- Play-off rules (leaning described in §6).
- Exact European qualification rules.
- In which tiers there are 2 cups instead of 1.

**Matches**
- Which player stats you feel when playing yourself (speed, shooting, passing, keeping, stamina, …).
- Camera height / zoom on the full-size pitch.
- Fouls, free kicks for fouls, penalties, cards.

**Players**
- Which stats exist (open for now).
- How personalities work in detail (open for now; the effects are listed in §8).
- Growth, ageing, retirement: direction decided (potentials, §10b); exact numbers (growth speed, decline per year, retirement odds) still open.

**Later (Marcel, 2026-11-07)**
- Stamina / sprint bar.

**3D assets (raised 2026-11-07)**
- Marcel will pay for a month of ChatGPT only if Claude or ChatGPT can build a good set of 3D models (stadium parts, shops, other assets). First test: Claude builds **The Shed** (see §10f). Verdict pending — Marcel judges the renders + in-game shot.
- Decided (Marcel, 2026-11-07): stands are **bought per 11.5 m section**; when sections stand side by side, the **side screen between them disappears**; **club colours are a buyable upgrade** that you apply yourself.
- Not decided: how sections replace the current chair/bench slots, corners, bigger stands (more rows, second tier).

**Not discussed yet** (here so they don't get lost)
- Economy: safety net (see §10b), exact expense list, performance bonuses.
- Stadium upgrade list: full categories, costs and effects (§10a has the direction).
- Off-season length (x weeks).
- How fans are counted and what they do for you.
- Training, staff roles, youth.
- Season calendar (pre-season, cups, Europe).
- Save system.
