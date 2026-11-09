# Sunday League — Game Design Document

> Living document. Only contains what Marcel has decided. Anything not decided is listed under **Open questions**.
> Rule for this project: Claude decides nothing unless Marcel explicitly says Claude may decide.
> Working agreement (2026-11-07): **everything we do, discuss, plan or decide is recorded in this document**, so nothing gets lost.

Last updated: 2026-11-08 (pitch grass texture, §10j)

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
| Controls | Mouse + keyboard (WASD) and an Xbox-style controller in matches (2026-11-08); menus/hub by controller later |

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

### Promotion / relegation (Marcel, 2026-11-07)

- **1st–2nd promote directly; 19th–20th are relegated directly.**
- **Play-offs:** **3rd–7th** of a division plus the **18th of the division above** fight for one last promotion/relegation spot. That makes 3 up / 3 down in total. Roughly the Dutch system, without period titles.
- **Per division the lines can be switched off:** the bottom division (Non-League 3) has no relegation and no 18th-place play-off; the top division (Premier Division) has no promotion and no 3rd–7th play-offs. Later: European places as extra lines on the table.
- Open: play-off format (bracket, one or two legs, home advantage).
- **Next step chosen (2026-11-08, Marcel let Claude pick between promotion/relegation and a better stand tier): promotion/relegation.** Marcel's answers:
  - **Play-off format (Marcel, 2026-11-08): three rounds, every tie over two legs. The higher-placed club hosts the second leg** (official EFL/KNVB rule; Marcel, 2026-11-08). **The 18th of the division above counts as the highest** (it's from a higher division), then 3rd, 4th … 7th. So: A 7th home first, B 6th home first, D 3rd home first; in C and the final the lower-placed club starts at home.
    - Round 1: **A = 7th v 4th**, **B = 6th v 5th**.
    - Round 2: **C = winner A v winner B**; **D = 18th (of the division above) v 3rd**.
    - Round 3 (final): **C v D**.
    - The winner goes up (or, if it's the 18th, stays up). **If the 18th loses anywhere, they are relegated.**
  - **Divisions stay as listed for now: 14** (Non-League 3 → 2 → 1, League 10 → 1, Premier Division).
  - **Level after two legs: extra time + penalties** (Marcel: "C is het devies" — also needed later for cups and European ties). No away goals.
  - **Play-offs in the first 3 weeks of the 10-week off-season**, one round per week (both legs that week); the off-season is equally long for everyone.
  - **You play your own play-off matches**; the other play-offs are simulated.
  - **Not enough seats for the division you'd go up to → your place goes to the next team** (Marcel, 2026-11-08). Claude's seat proposal (to enter): NL2 10 · NL1 20 · L10 40 · L9 60 · L8 100 · L7 150 · L6 300 · L5 600 · L4 1,000 · L3 2,000 · L2 3,000 · L1 4,000 · Premier 5,000 — **OK for now (Marcel)**.
  - **Extra time = 2 × a third of a half** (OK). **Penalties: you take your own (aim + power); keeping is chance** (your keeper dives at random). **Sudden death after 5 each** (OK).
  - **Difficulty: the same in every division for now** (until the player system exists).
  - **Money per division from the economy model's game column** (ticket, spend per visitor, sponsor, prize money, costs).
  - **Promotion requirements now, as simple seat counts** (Claude proposes numbers, Marcel approves).
- **Built (2026-11-08):**
  - `scripts/pyramid.gd`: all 14 divisions with fictional clubs (pub teams in Non-League, town names from League 10 up). Other divisions' seasons are simulated from club strength when yours ends. Play-off bracket exactly as above; AI ties are simulated (two legs, extra time, penalties). Moves: top 2 eligible up, play-off winner up (unless it's the 18th of the division above: it stays there), 19th/20th down, 18th down unless it won the play-offs below. A club without enough seats is skipped (top 2 and play-offs).
  - Your season: after the last league match the tables are fixed. 3rd–7th (with enough seats) → play-offs in weeks 43–45. 18th (not in Non-League 3) → you play in the division below's play-offs (as the "18" seed against their 3rd). "Start season N+1" only appears when your play-offs are over; then everyone moves and you start in your new division.
  - **Extra time**: in a second leg that is level on aggregate after 2 halves. Two halves of a third of a half each; sides switch at the extra-time break. HUD says "Extra time".
  - **Penalties** (still level after extra time): camera behind the taker at the far goal. Your kicks: aim with the mouse (pad: left stick left/right), hold RMB (pad: B) for power and release. More power = faster, higher and less accurate (full power can go over the bar). Their kicks: random spot and power. **Both keepers guess at random** (left / stay / right). A keeper who guesses right still can't reach the corners. Alternating, first five each (ends early when one side can't catch up), then sudden death. Kickers rotate, most attacking players first. Who kicks first is a coin toss.
  - **Money per division** (`ClubState.DIV_ECON`): ticket, tea hut spend per visitor, sponsor, prize money, plus a cost factor on pitch hire / referee / kit / travel / league fee (Non-League 3 = 1×, Premier = ~25,400×). Match subs stay £1 per player.
  - Hub: the division name in the stat bar and table title; zone lines per division (promotion with the seat requirement, play-offs, 18th, relegation); the Next Match card shows your play-off leg (first-leg score, what's at stake), then the expected outcome ("Promoted to …", "Not enough seats …", "Relegated to …") with "Start season N+1"; a welcome line in week 1 of the new season; Coming up shows the next play-off leg and "Promotion needs N seats". The post-match card shows the round, the leg and the aggregate ("Through to the final", "won 4–3 on penalties").
  - Dev: `tools/dev/pyramid_test.gd` (headless: denied without seats, promotion, play-offs, relegation, save/load, 10 seasons in a row) and `-- --playoff-test --menu-skip` (forces a level second leg → extra time → penalties, screenshots in /tmp).
  - Not yet: cup ties, away goals (not wanted), difficulty per division, a nicer shootout presentation (kick list with ticks/crosses).

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
- The off-season is an auto-skip of **10 weeks** (starting point, §10a build times).

### Location
- The ground grows **in place**, and it sits **in a residential area**.
- There's always enough room to expand, but you can see houses around it, or a car driving past on the nearby road.

### The world around the ground (Marcel, 2026-11-09) — mockup stage
- **Marcel:** build a world around the stadium out to the fog (~400 m): **a real English neighbourhood**; water is Claude's pick; **static for now, but with movement in mind** (streets/towpath as future routes); **the neighbourhood is static** (doesn't grow with the club); **home ground only** for now.
- **Mockup v1** (night of 2026-11-08/09): a street grid. **Rejected** — Marcel (2026-11-09): "Maak het niet te vierkant. Het moet geen raster van huizen worden."
- **Decisions (Marcel, 2026-11-09):**
  - **Water:** Claude's pick, an **English canal** (towpath, lock, humpback bridges, narrowboats later for movement — their route is fixed).
  - **Static neighbourhood vs growing stadium → option A:** the neighbourhood really is static. The houses start at the edge of the max-stadium reserve plus a plaza ("with a second or third ring the facade needs breathing room"). So a small stadium sits in a roomy ground.
  - **What fills the reserve early on:** car parks, lots of trees, a park, a training pitch.
  - **Performance:** a few house variants, instanced, simple LOD from ~200 m — built in Blender like the stands.
- **Mockup v2** (`tools/blender/build_town.py [--max] --render …`, fog via `tools/blender/fog_composite.py`, renders `design/world/v2_*.png`):
  - **Reserve:** a superellipse (rounded oval), 150 × 128 m half sizes, palisade fence, gate on the West side. The max stadium (pitch + ~70 m stands) fits with a 23–25 m plaza at mid-side.
  - **Ring road** round the reserve; its West side is the **High Road** with the **pub** opposite the gate.
  - **Streets:** curved roads, crescents (West and South), a close with a turning circle. Houses are placed **along the streets** and follow the bends (collision grid keeps them off roads, water and each other). Victorian **terraces** in runs of 6–16 with ginnels between them, near the ground; **1930s semis** (bay windows, hipped roofs, driveways) further out; mixed streets in between. Parked cars on terrace streets, lamp posts, avenue trees on the main roads.
  - **Canal** winds across the East side: towpath on the stadium side, a **lock** with a lock keeper's cottage (South-East), **two humpback bridges**, moored narrowboats.
  - **The rec + church** (North-West), **allotments** (South-East), leftover land green with tree clumps, thick woods at the edge (~400–430 m).
  - **Early variant:** car parks by the gate, a **park with a pond** at the North end, a **training pitch** at the South end, a tree belt inside the fence; a short main stand (tunnel) + a short Shed.
  - **Max variant:** a paved plaza with a tree row along the fence and tree islands in the corners; the two-tier POC stand on all four sides (the reserve leaves room for a 3rd tier).
  - Nothing in the game yet.
- **Feedback on v2 (Marcel, 2026-11-09):** good direction, not there yet. Look at real small British towns: **narrow streets, houses close together** — too much distance now. Maybe **fake depth** in the houses (agreed: discuss with the houses; per §crowd notes no normal maps → real geometry: inset windows/doors, sills, bays).
  - Claude's research: carriageway 24 ft (7.3 m) is the old byelaw standard (we have 7 m); terraces sit on the pavement or behind a ~1.8 m front yard; long narrow back yards with an **alley** behind; a ginnel through the row is often built over on the first floor. Parallel streets ~40 m apart instead of 60–80 m, little leftover green. **Kenilworth Road (Luton)** as the "close" reference: the away entrance is cut into a terrace, fans climb steel stairs above back gardens.
- **New process (Marcel):** first a **line plan** (2D top view: roads as lines, blocks, zones, facilities, scale bar), improve that together, then a mockup like v2.
- **The reserve (Marcel, confirmed):** lots of room at first, kept for the stadium later. It must fit **every stadium shape** the player can pick later (rectangular with corners, rounded corners, oval — see stand stages discussion) → the biggest is the full rectangle with filled corners (~250 × 210 m incl. stands); the rest fits inside. Early on the reserve is **in use**: facilities, a small car park + access road, so the ground has life. The village is built **tight around that** (less round, comes close). When the stadium grows, facilities move into the stands.
- **Facilities list** (Claude's proposal, Marcel picks): gatehouse with turnstiles, ticket booth, away entrance, chip van/burger van, tea hut, clubhouse with bar, 2–3 merchandise tents, programme seller, toilet block, groundsman's shed, changing rooms, boardroom/portakabin, small car park (~30–50), access road, team bus spot, bike racks, club sign, flagpoles, advertising boards on the street-side fence, **floodlight masts** (Marcel: "vergeet die niet"; GDD: 4 corners, 8 m diagonally out — later on rounded/oval shapes they move onto the corner stands or become a roof light bar, to discuss).
- **Floodlight masts (Marcel, 2026-11-09):** masts go **~15 m diagonally out** from the corner flag (was 8 m) — clear of every side/end stand, also a 2nd ring; only a corner stand takes that spot. A mast **moves to the roof (light bar on the roof edge)** automatically, **per corner**, when (a) a stand is built in that corner (closed, rounded, oval) or (b) the roof of a neighbouring stand gets high enough to shade the lamps. The move is **free** (floodlights stay a paid upgrade once). Mixed setups (masts on the open side, roof bars elsewhere) are real (e.g. Fratton Park).
- **Plan v1** (`tools/plan/world_plan.py`): Marcel asked for a self-review + a 5-person panel (for / against / neutral / critical / reserved). Verdict: back to a grid and a square, the ground "not in use" (small boxes in a huge field), assumptions (home end), no growth shown, no walkways, unreadable on a phone. → split the work: ground first, then the plot edge, then the village.
- **Decided (Marcel, 2026-11-09):** **North = home end / hard core.** Fans come **out of the streets: every junction on the ground's edge is an approach route.**
- **Plan v2** (`tools/plan/world_plan_v2.py` → `design/world/plan_v2.png` + `plan_v2_growth.png`):
  - The plot is **irregular** (holds the max line, which marks "everything inside is temporary"); a **car-park lobe** in the South-West sits outside the max line and stays; the East side is tight (houses' yards on the fence).
  - Approaches: **Gate Street junction** (West) → gate arch, tickets, programmes, merch tents, home turnstiles behind the main stand; **High Road / Mill Lane junction** (North-West, with the **pub for the hard core**) and **Chapel Row junction** (North) → the home end with chip van, tea hut, toilets, home-end turnstiles; **South Street / Canal Street junction** (South-East) → away gate, segregated walk to 23–24 + corner, away coach bay on South Street.
  - Compact: facilities sit right behind the stands, beige walkways/concourses connect them; clubhouse + beer garden between the West gate and the home approach; changing rooms, boardroom, team bus at the tunnel via a service road from the car park; groundsman South-West; temporary training pitch at the South end; kickabout green + trees on the East side; tree belts along North and South fences.
  - **Growth strip:** early (all outside) → 2nd ring ~35 m (turnstiles, changing rooms, boardroom, kiosks, toilets, groundsman go into the stands; training pitch gone; clubhouse, merch, chip van still outside) → max (everything inside the stands, clubhouse = bar in the main stand; outside: car park, coach bay, village; masts → roof bars; corners only if the shape closes them).
- **Feedback on plan v2 (Marcel):** pub literally on the street; the plot ran over High Road + North Street; paths didn't connect (road, each other, stadium); facilities on paths; coach bay over front gardens/houses; far too much space between houses + tiny footprints ("the problem isn't the path"); max line ignored the **facade** (offices, stair cores stick out). Claude's panel had missed most of it → plan scripts now **check themselves** (nothing on a street/house/path/mast, every path end connects) before drawing.
- **Decided (Marcel, 2026-11-09):**
  - **Paying area = option A:** a fence tight round the stands; kiosks + toilets inside; clubhouse, merch, tickets, car park outside.
  - **Masts stay at 15 m; roads and paths go round them.** Mill Lane approach becomes a **plaza**. Roomy early on is fine, but filled "well and healthily".
  - **Pubs belong to the terraces:** corner houses at junctions, several allowed (hard core at High Road/Mill Lane, main gate, away pub at Canal/South Street…).
  - **Facade zone:** ~10 m beyond the max stands on N/E/S, ~20 m on the West (club building). Max line = stands max + facade zone.
  - **Facilities grow with the division.** Grow: clubhouse, offices/boardroom, club shop (tents → shop), changing rooms, ticket office, groundsman, car park. Fixed: chip van, tea hut, flags, club sign, bike racks. **3 sizes** to start (≈ 13–9 / 8–5 / 4–1, to fine-tune). Each grower gets a **plot at its biggest size**; the small building sits in it, the rest is usable filler (grass, benches, a few spaces, a terrace).
- **Plan v3** (`tools/plan/world_plan_v3.py [--six]` → `plan_v3_min.png`, `plan_v3_max.png`, `_six` variants, `plan_v3_ends_5_vs_6.png`): same village round **min (13th division)** and **max (1st division)**. Houses drawn as front garden · house + outrigger · yard · alley (5 m wide, ~19 m plot), back-to-back blocks, ginnels; 5 corner pubs. Plot with a North-West bulge (home plaza + clubhouse, stays) and a South-West lobe (car park + groundsman, stays); everything inside the max line is temporary. Min: paying fence with 4 turnstile points (West, NW + N for the home end, away SE), home-end kiosks inside, away kiosk + wc in the pen, growth plots dashed. Max: stands + closed corners, club building in the West facade, stair cores, turnstiles in the facade, forecourt ring.
- **Open: a 6th section on the ends** (Claude: yes — 5 × 11.5 = 57.5 m leaves ~8 m dead space each side; 6 → ~2.4 m, same as the long sides; downside: no middle section, section numbers shift (North 18–23, South 24–29, away 24+25)). Marcel to decide.
- **Feedback on plan v3 (Marcel):** North Street still ran over the plot (the self-check never tested the plot against the streets — Claude had reported "0 errors"); no bridges between Canal Street and Wharf Street. Claude's own review also found: unreachable land over the canal, empty block middles, no car-park entrance, max turnstiles drawn inside the stands, seams between stand blocks.
- **Decided (Marcel, 2026-11-09):**
  - **6 sections per end** (North 18–23, South 24–29; away = 24 + 25). Code change still to do (ClubState.SECTIONS_SHORT, hub cards, tests).
  - **Segregation grows with the division:** amateur (13–9) free to walk round the paying area, only the away pen fenced off (non-league fans even swap ends at half-time); semi-pro (8–5) away fully separate with its own entrance, the rest mostly open (maybe the main stand apart); pro (4–1) every stand its own turnstiles + concourse, ticket valid for one stand.
  - **Bridges:** 2 humpback bridges (North Street and South Street run on to Wharf Street) + a footbridge at the lock.
  - **Empty block middles** become **courts with garages / workshops**, reached through an arch in the terrace (Claude picked this of the two options; Marcel can still choose closer streets instead).
- **Plan v4** (`tools/plan/world_plan_v4.py [--five]` → `plan_v4_min.png`, `plan_v4_max.png`): the above, North Street moved off the plot, max stands drawn as one closed bowl, per-stand turnstiles in the facade. **Self-check now covers:** houses (not on streets, the plot or the canal), the plot against the streets, buildings (inside the plot, not on streets/paths/masts/stands/each other), paths (inside the plot, not through masts/stands, both ends connected), the coach bay (not on houses, carriageway or plot), court lanes (not through houses), canal crossings (bridges only), every street reachable from High Road. Not covered: how it looks (drawing errors like the hole bug — checked by eye).
- **Plan v4 feedback (Marcel):** a row of houses at the back of Shelley Street; the crooked houses at a bend are fine ("vrij normaal"). Claude's must-fixes: the car park entrance (forgotten after v3) and a coach bay that was 2.2 m wide (needs ~3.5 m). Marcel's compromise: **move South Street + Shelley Street a few metres out** (bay fits on the ground side of the pavement, fence untouched; Canal Street one house longer, Lock Lane one shorter, houses where the garages were → Keats Street runs on to Canal Street).
- **Natural (Marcel):** "not always flat, not always rectangular, not always perfectly round; a path isn't always exactly x m wide". Applied in plan v5: carriageways 7.0–7.4 m (main) / 5.8–6.6 m (back streets), pavements 1.2–2.2 m per street; per terrace a width of 4.6–5.8 m, front garden 0–2.5 m, house 7.5–9 m deep, yard 5–10 m; paths bend gently and swell/narrow (ends stay where they connect); the fence has small inward kinks (straight at the gates). **Height:** the land falls gently towards the canal (~+3.5 m in the West to −1.2 m at the canal), the lock steps the water down (+0.4 → −1.4 m), the ground is levelled at ±0.
- **Plan v5** (`tools/plan/world_plan_v5.py [--five]` → `plan_v5_min.png`, `plan_v5_max.png`): the above + car park entrance (dropped kerb + gate from Car Park Lane, in the self-check) + coach bay 3.5 m on South Street's ground side.
- **Plan v5 finish (Marcel: "dan zijn we er denk ik"):** Car Park Lane now bends smoothly out of High Road; Albert Street runs on to the Car Park Lane / Lower Road crossing (the vague workshop corner became two rows of houses); every T-junction's side street runs half a street width into the street it meets (no bitten-out corners); house collision uses the full plot width.
- **3D mockup v1** (`tools/blender/build_world3d.py [--max] --render …`, renders `design/world/3d_v1/`): built straight from world plan v5 (same streets, house plots, plot, facilities, heights). Terrain with the ground levelled at 0 and a 7 m bank inside the fence, terraces per plot (house + outrigger, walled yard, alley, front wall), canal water levels from the terrain (lock ~1.8 m), min stage with the real stand models + masts, max stage as a closed bowl (rough). Known: a black patch by the clubhouse plaza (max), two street cameras badly placed, the max bowl is massing only.
- **Bigger village (Marcel, 2026-11-09):** wants it to feel like a **real village/town** → option **B now**: ~**1.5 × 1.5 km** round the ground (≈4,000–6,000 homes, ~12k people), knowing the match camera only sees to the fog (400 m). **Everything** a town that size has: supermarket, church, flats, school(s), station + railway, park + bandstand, cemetery, sports fields, petrol station, GP/pharmacy, fire station, village hall, library, fish & chips/takeaways, bus stops. The ground sits **fairly central — it "happened" to grow there**. The plan-v5 area may shift if that fits better; **the stadium layout stays**. The **canal runs through the whole village** (with the mill).
  - Claude's approach: the town grows in layers — old core (church, green, High Street) → Victorian terraces (the ground on an old brickworks) → Edwardian infill → 1930s semis → post-war estate with flats → new-build cul-de-sacs, plus industrial by the railway. Main roads + landmarks by hand, streets inside each layer filled by rules per layer, same self-check.
  - **Village plan v1** (`tools/plan/village_plan_v1.py` → `design/world/village_v1.png`): step 1 = layers, main roads (London Road A-road, High Street, Mill Road, bypass…), canal + 2 locks, railway + station (Station Road continues Gate Street: fans walk from the station to the main gate), all landmarks, bus stops, the fog circle. No houses yet.
- **Village plan v2** (Marcel asked for a wireframe of the whole village → A: a 2D line drawing; `tools/plan/village_plan_v2.py` → `design/world/village_v2.png` + zooms core / east / new build): every street + building outline over 1.5 km. Blocks between main roads are split per layer, a street runs along every layer seam, then each layer fills its pieces by its own rules (old core: wandering lanes + cottages; Victorian/Edwardian: parallel streets with a bend + cross streets, terraces; 1930s: curving streets, semis; post-war: loop road + slab flats in open green; new build: wiggly spine with bent cul-de-sacs + turning heads, detached; industrial: spine + sheds). The plan-v5 area round the ground is kept as it is. Two railway bridges added to the main roads (Bridge Road by the station, Moor Lane by the industrial estate) — without them the new-build area beyond the railway had no way in. Streets that don't join the network are dropped before houses go in. Self-check: no building on a street / canal / railway / landmark / the ground, no generated street over canal or railway. Result: ~5,200 homes, 10 blocks of flats, 8 sheds.
- **Feedback on village plan v2 (Marcel):** "wtf zijn die straten" — the core was spaghetti; it felt like the rest was built *round* what we had, with no regard for where roads already are, how roads join, how houses stand. Claude agreed: every block was filled on its own with clipped lines, nothing joined the v5 streets, there were no junction rules, and the check only tested collisions ("0 errors" on something plainly wrong).
- **Village plan v3** (`tools/plan/village_plan_v3.py` → `village_v3.png` + zooms core / join; Marcel: "Bouw v3"): the town **grows from what exists**. Seeds = the main roads + every v5 street; v5 streets carry straight on out of the v5 area until they meet a street; streets along both sides of the canal and the railway; then blocks are split by a new street only when it meets streets at both ends with a real T (65–115°), ≥ 28 m from other junctions (or lined up as a crossroads), bend flat at the ends; split across when a block is too long, along when too deep, until it holds two plot rows back to back (per layer); a street may run off the map edge (the town carries on) or end at a park / station / mill; new build gets cul-de-sacs with turning heads in leftover big blocks. Houses take their type from the layer at each plot, so the High Street in the core gets shops. **The check now also measures village sense:** junction angles, junction spacing, crossings without a junction, loose ends — plus the collision checks. Result ~5,000 homes, 228 High Street shops, 162 generated streets, 44 cul-de-sacs. Remaining: 2 junctions sharper than 60°, 6 junction pairs 9–24 m apart (canal/railway side streets), a few still-empty blocks (round the cemetery/supermarket band, between core and ground, industrial), few flats.
- **Village plan v4** (`tools/plan/village_plan_v4.py` → `village_v4.png` + zooms core / canal; from Marcel's v3 feedback "kruispunt in het water / heel veel lege ruimte" and the panel): **no junction on or within 30 m of a bridge** (canal/railway side streets bend away and meet the main road square-on ~32 m from the crossing); **no street doubling a main road** (side-street stretches running parallel within 45 m are dropped); side streets that end nowhere are linked to the nearest street, cut back to their last crossing, or end as a cul-de-sac; new streets may meet v5 streets across the v5 margin; **every block gets a use**: big leftovers → park / playing field while public green < 13 %, mid-size → a mews court (lane + houses), leftovers behind houses → **back gardens** of the nearest house (split per house, as in a real town), only pieces with no houses round them → garages / allotments / play area. **Green is marked as green** (green fills + italic labels; trees left out of the plan, Marcel: "10-15 klinkt goed, bomen weggelaten"). Denser estate (flats 48×13) and industrial (sheds 44×30). Supermarket and school drawn with their own grounds. Result: ~5,200 homes, 223 High Street shops, 169 generated streets, 52 cul-de-sacs, 116 mews, public green 13.7 %, blocks used 98.7 % (0 blocks under 85 %). Remaining check items: 1 junction pair 24 m apart (limit 25), 1 junction within 25 m of a bridge. Known weak spots: four big blocks the splitter couldn't cross became large playing fields (east of the estate, by the cemetery, by the fire station, round Victoria Park); back gardens are deep in places west of the High Street; the industrial estate is still loose.
- **Rethink after v4** (Marcel: "opnieuw tekenen vanaf wat we al hadden, dan kan je het beter opvullen en plannen ipv pleisters plakken"): no more growing blind and patching leftovers. Order: fixed (ground v5, canal, railway, main roads) → **skeleton** (districts, district streets, parks, industry, landmarks with grounds) → Marcel reviews → fill per district. The v3/v4 checks and house placement stay. Marcel's answers: **park 1** behind / next to the church, **with the cemetery** (cemetery moves there); **park 2** on the canal east of the terraces at the south stand (where v4 had the big green east of the estate); **industry below the railway**, at the bottom of the picture (= game-west), not in the town; **garden depth** Victorian / old core 10–15 m, 1930s 20–30 m, new build 8–12 m; districts: Claude proposes.
- **Village skeleton v1** (`tools/plan/village_skeleton_v1.py` → `village_skeleton_v1.png` + zooms park 1 / park 2 / industry; proposal, not decided): districts from the v1 layers with the industrial layer moved below the railway (the old works between London Road and the railway become Edwardian + infill); 13 district streets (Brickfield Road, Grove Road, Kingsway, Park Avenue, Moorside, School Lane, Lock Lane, Back Lane, Railway Terrace, Foundry Lane, Southfield Road, Rectory Road, the industrial estate entrance) linking the main roads; park 1 = church + churchyard + cemetery (paths cross, lychgate) + park to the canal (pond, playground, diagonal paths); park 2 = canal park (perimeter path, pond, bandstand, playground, bowling green, kickabout pitch); industrial estate with one way in off Moor Lane, a loop with yards either side, green buffer along Moor Lane; petrol station on London Road. Check: 0 errors (district street ends on a street at ≥ 60°, nothing over canal / railway / ground, nothing on a street, no junction within 30 m of a bridge). **Public green only 6.0 %** (target 10–15 %); five dashed green OPTIONS for Marcel: a canal greenway +0.7 %, b rec ground below the railway +0.5 %, c rec ground in the north new build +0.7 %, d park 2 grows towards London Road +0.7 %, e cricket ground on the old cemetery site +1.2 % — all five together ≈ 9.8 %.
- **Away end (Marcel, 2026-11-09): fixed on the South stand, its East end** ("like the Kooi stadium"). The player picks the size: 1 or 2 of the 5 South sections (section 23, then 24), those plus the South-East corner, or only the corner. → **One away entrance, baked in at the South-East.** (Alternatives that were on the table: an away gate per side; one gate + a segregated corridor round the ground.)

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
- **In-game build step 1 (Marcel agreed 2026-11-07):** calendar + construction mechanic + bleachers as the first new stage; Shed and the rest step by step after that.
- **Calendar decisions (Marcel, 2026-11-07):**
  - A week is **not** one match: cup, European and pre-season matches can fall in the same week, and fixture spacing can put **two league matches in one week**.
  - Straight to a **full season: 19 home, 19 away**, always a return match. Roughly half of your home matches fall in the first half of the season, the other half in the second half; same for away matches.
  - **Fixtures (decided 2026-11-07):** you never play the same opponent home *and* away in the first half of the season; the second half has the return matches, but **not** as a literal reversed copy of the first-half order.
  - **Away matches: you play them yourself, in a seeded away ground per club** (decided).
  - Season: 42 weeks + 10 weeks off-season; other league matches simulated so there's a real table (Claude's proposal, not objected).
- **Build order step 1 (Marcel OK, 2026-11-07):** block 1 sections of 11.5 m (benches/chairs, ad board + rope, dugouts) → block 2 calendar + league (20 teams, fixtures, table, simulated matches, 42+10 weeks) → block 3 away matches in a **simple seeded away ground first** (benches/chairs/bleachers/trees/fences by division) → block 4 building (bleachers stage, closed sections, rush build). Marcel can pull and test after each block.
- **Block 1 built (2026-11-07):** 28 sections of 11.5 m (9 per touchline, 5 behind each goal, end sections 2.5 m further back to clear the nets). Each section = 5 spots of 2 m (a bench, or up to 4 chairs — same rules and prices as v0.1) = 20 seats in a row + 1.5 m aisle. Pitchside per section: blank ad board ("YOUR AD HERE" until sponsors exist) at 1.4 m, rope at 2.2 m; standing fans between rope and seats (3.0 m); seats at 4.0 m. Dugouts in front of the middle far-side section (no board there; standing fans keep clear). Old saves start a new game (save version 2). Screens: `design/hub/sections_*.png`. Dev: `--hub-test --fill-test`.
- **Block 2 built (2026-11-07):** `scripts/league.gd` (loaded by path, no class_name). 20 teams (you = "Your club", placeholder until club naming exists; 19 generated pub-team names, unique first part). First half = one round robin (circle method) with venues balanced to 9–10 home matches per team; second half = the returns with venues swapped, in a new shuffled order (never the same pairing straight after the break). 38 rounds over **42 weeks: 3 double weeks + 7 empty weeks** (later: cup/Europe/international breaks). Other matches simulated (Poisson goals from team strength 0.92–1.08, home advantage; tunable). Team strength also sets the opponent's speed in your match (was random per friendly). After round 38: hub shows the final position and **Start season N+1** (skips the 10-week off-season; same division and teams for now — promotion/relegation not built). Hub: season/week + league position in the top bar, NEXT MATCH, full table. Away matches (placeholder until block 3): played at your ground, no crowd, no ticket income, no seating effect on approval. Save version 3 (older saves start fresh). Dev: `--hub-test` checks fixtures + a full simulated season; `--sim-rounds=N`.
- **Promotion/relegation:** not in this step; can be a next step (Marcel, 2026-11-07).
- **Match feel feedback (Marcel, 2026-11-07, after block 2):** passing is still bad — passes often don't arrive, are too slow or inaccurate. It's better to win the ball, run through opponents and shoot in the far corner (won 10-0). Claude's diagnosis + options in chat; nothing changed yet.
- **Hub camera (Marcel asked, 2026-11-07):** free look between matches + reset. Built: WASD/arrows pan relative to the view, wheel zoom (down to near ground level), Q/E rotate, R/F tilt, hold right/middle mouse + drag to orbit and tilt (a right click without dragging still cancels placing), C or the "Reset camera" button resets. Controls are Claude's pick, tunable.
- **Match feel (Marcel, 2026-11-07):** fix passing and the solo-play balance **now, before block 3**. **One fixed difficulty level for now**, built so that more difficulty levels can be added later.
- **Match feel round 1 built (2026-11-07), all tunable:**
  - Passing: passes arrive at ~13 m/s (was 7: slow, easy to cut out); **receiver assist** — while your pass is on its way your receiver runs to the meeting point himself, your input takes over once he has it; the intended receiver controls the ball from 1.1 m (was 0.7/0.85). AI-vs-AI pass completion went from ~55% to ~63–70% (4–6 headless matches each), interceptions roughly halved.
  - Solo balance moved into **difficulty levels** (`DIFFICULTY_LEVELS` in main.gd, only "normal" for now): your speed bonus 1.10 → 1.04, your dribble speed 0.92 → 0.88 (= AI), your steal time 0.3 → 0.5 s, AI steal time vs you 1.2 → 0.8 s, your tackle success 85% → 70%, AI tackle 55% → 60% and 0.7 → 1.0 attempts/s near you, AI shot error 1.6 → 1.4, their keeper reaction 0.28 → 0.18 s, dive 7.0 → 8.0 m/s, reach 0.80 → 0.88 m, parry 60% → 50%.
  - Keeper shot test (their keeper): goals per on-target shot low/mid/high power went from ~29/47/56% to ~10/19/50%. Hard shots into the corner still go in about half the time.
  - Dev: `--fast=N` runs headless tests N× faster with the same 1/60 s step; a `completed` pass stat.
- **Block 3 built (2026-11-07), simple first version:** every opponent has a **seeded away ground** (seed = club name, so the same club always has the same ground): a few benches/chairs around halfway on the far side (sometimes a bench or two behind a goal), a clubhouse with the club name behind a corner (random colour/size), sometimes hedges, extra trees, ~30% of the ad boards carry the home club's name. Size grows with team strength (and later with level). Home fans 6–18 + up to 25 by size, in red; **20% of your fans travel along** (tunable), standing together behind the near touchline in green. Home fans cheer for the other side (your goal = they slump). Still no ticket income away. Your own ground (furniture, blank boards) comes back in the hub and at home matches. Dev: `--away-view="Club Name"`. Screens: `design/hub/away_*.png`.
- **Feedback after match feel round 1 (Marcel, 2026-11-07):** the passing changes are a big improvement — "ik wil daadwerkelijk passen nu". Holding Shift to sprint will hurt hands (everyone sprints all the time) — Marcel suggests **sprint as default** (open, Claude's proposal in chat). **Q switching** went wrong when you keep switching: you end up further from the ball.
  - **Q fixed (2026-11-07):** Q now always picks the teammate nearest to where the ball is going (other than the one you control), recomputed on every press, so repeated presses bounce between the two nearest instead of walking away. The 1.2 s cycle list is gone.
- **Sprint is the default (Marcel OK, 2026-11-07): hold Shift to walk** (for close control / waiting for an opponent). Built.
- **Haze (Marcel, 2026-11-07):** a noticeable haze over the game, mostly with the zoomed-out hub camera. Cause: the fancy light's exponential fog (density 0.0025, bluish) starts right at the camera — at 90–150 m (zoomed-out hub view) that's ~20–30% fog over the whole pitch. Fix proposal in chat (depth fog that only starts far away).
  - **Built (Marcel: "we proberen de nieuwe setting"):** depth fog, nothing up to 120 m, building up to 400 m (tunable `FOG_BEGIN`/`FOG_END`). Screen: `design/lighting/depth_fog_hub.png`.
- **Block 4 built (2026-11-07):** building per section with time.
  - **Open bleachers** as the first new stage (procedural in Godot for now, no Blender asset): 3 rows × 20 = 60 seats, **£1,800** per section (≈ £30/place, from the economy model's Stand prices tab), **1 week**. **+2 rows** (→ 5 → 7) for £1,200, **½ week** (half the stage time). Rush: +50% cost for 75% of the time. Placing bleachers on a section with chairs/benches removes them and adds **1 week demolition** (stage jump rule; not rushed).
  - A section under construction is **closed**: fence, half-built frame and a sign with the ready date; its seats don't count. Chairs can't go on a bleacher section or a building site.
  - Time = absolute weeks (52 per year: 42 season + 10 off-season). Builds finish when you're back in the hub after enough match weeks; "Start season" skips the off-season, so builds started there finish over the summer.
  - Hub: BUILD (per section) shop with costs/times, UNDER CONSTRUCTION list. Fans can sit on the bleachers.
  - The model's Stand prices tab listed older build times for modern tier / 2nd / 3rd tier (8/12/16 wk); **aligned to the accepted 6/8/12** (Marcel OK, 2026-11-07).
  - Screens: `design/hub/bleachers_*.png`, `design/hub/construction.png`. Dev: `--hub-test` runs a build test.
- **More dev cheats (Marcel picked, 2026-11-07):** in the F1 panel: squad full, approval 100% / 0%, construction +1 week, next match as win 3-0 / draw 1-1 / loss 0-3 without playing, view the away ground of every club in turn (+ back to my ground). In a match: F3 goal for you, F4 goal for them, **F5 free camera** (pauses the match, hub camera controls, F5 to play on). Not built: "simulate rest of season" (not picked).
- **Bleachers connect (Marcel, 2026-11-07):** the ~1.3 m aisle between sections looked like loose stands. Decided: **a stair in the gap only where two bleacher sections meet** ("trap aan de zijden waar ze connecten"). Built: two steps per row up to the lower of the two sections; the taller one gets a sloped side rail above that. A lone section has no side stair. Screens: `design/hub/bleachers_connected*.png`.
- **Dev cheats (Marcel asked, 2026-11-07):** more fans, more money, instant building, finish match early. Built: **F1 in the hub** toggles a DEV CHEATS panel at the top (+£10,000, +100 fans, finish all construction now); **F2 in a match** ends it now with the current score. `--cheats` opens the panel at start. Marcel asked for more ideas — Claude's list in chat, nothing extra built.
- **Visual polish (Marcel, 2026-11-07):** the stands keep getting better; the other models/textures lag behind — textures too flat, need more dimension. **Art direction decided: stylised** (clean low-poly with good materials and light). Claude's proposed order: grass → shared material shader (noise/roughness/grime) → surroundings (residential area) → players. Marcel offered to have Claude Design make textures from Claude's prompt; discussion in chat.
- **Full stands visible (Marcel, 2026-11-08: 1,300 seats sold out but the stands looked half empty → "ik wil ze zeker wél zien"):** the money was right (1,300 seated, 2 standing); only 220 fans were ever drawn (`MAX_VISIBLE_FANS`, each fan a separate animated node). Now **every occupied seat gets a fan**, drawn as one MultiMesh (`scripts/seated_crowd.gd` + `crowd.gdshader`, same seated figure as the big stand POC): idle sway, bounce on a goal for us, heads down on a goal against (shader uniforms; home fans at an away ground react the other way). Standing fans stay separate figures, capped at 220. Chant bubbles also pop up from seated fans. Screen: `design/hub/crowd_full.png`.
- **Bunching fix (Marcel, 2026-11-08: "die spelers bunchen lekker", 3 teammates on one spot):** measured with a new `--bunch-test` logger (3+ teammates within 2.5 m) in AI-vs-AI matches — it happened all match long. Causes: (1) defending trio in a line behind the ball carrier (chaser jockeying at 1.6 m, zone owner stepping out at 2.5 m and the second presser covering at 4.5 m, all goal-side); (2) several players coming short ("show") to the same spot near the ball carrier. Fix (tunable): teammates that aren't chasing/receiving/pressing keep ~4 m room (`SEPARATION_RADIUS`/`STRENGTH`); the second presser covers 3 m towards the middle (`COVER_SIDE`); max 2 players come short at once (`MAX_SHOW_RUNNERS`). Result: bunching in ~1% of samples instead of constantly. Side effect: AI-vs-AI steals went down (~6 per team per match instead of ~13); the chaser's pressure on you is unchanged — Marcel to judge the feel.
- **Player & fan models + animations (Marcel, 2026-11-08):** next visual step after the grass. Decided: **Claude builds them himself** (Blender script, like the stands); proportions **realistic-ish**; kits with **shirt numbers** (names only if it doesn't get too cluttered with text); **faces, hair, and beard growth for older players**. Plan (Claude): one rigged base player first + idle/jog/sprint preview for Marcel to judge the style, then kick/pass/tackle/celebrate/keeper animations, then simplified fans (seated + standing, shader-animated for thousands).
- **Base player, style preview (2026-11-08, for Marcel's verdict; not in the game yet):** `tools/blender/build_player.py` → `assets/models/player.glb`. ~1.80 m, realistic-ish proportions, low-poly flat-shaded, rigid-skinned to a 24-bone armature (each body part 100% on one bone). Materials Shirt / Shorts / Socks / Boots / Skin / Hair / Eyes (recoloured per team/player in Godot). Face: nose, eyes, brows, ears, mouth line. Hair variants as separate objects (Short, Buzz, Quiff, Long) + Beard, toggled per player. Animations: idle, jog, sprint (keyframed by script; Claude fixed a bent-knee stance after the first render). Shirt numbers planned as Label3D on the back (crisp, per player, no textures). Previews: `design/3d/player/views.png`, `faces.png`, `jog.gif`, `sprint.gif`.
- **Player v1 feedback (Marcel, 2026-11-08):** head far too small; neck too long; height OK but legs/arms too thin; hair stops too high; beards don't always fit; shoulders/neck too round and flat. **v2 (Claude):** head ~30% bigger (≈1/5.7 of the height, still "realistic-ish"), neck shorter and thicker, thicker arms/legs/hands, torso as one closed shape with squarer shoulders sloping into the neck, smaller square deltoids; hair and beard are now shells of the same (left/right-symmetric) head shape, so they always fit — hair runs down to the ears at the sides and the nape at the back; the beard covers jaw/chin/sideburns with the mouth free.
- **Player v2 in-match view (2026-11-08):** Marcel asked to see the sprint from the regular camera. `build_player.py --game-view` renders jog/sprint from the real match camera (zoom 1.0, fov 48°, 25 m up / 21 m back) → `design/3d/player/sprint_gamecam.gif`, `jog_gamecam.gif`. At zoom 1.0 a player is ~20 px tall at 540p: silhouette and run cycle read, face/beard don't.
- **Player variety (Marcel, 2026-11-08), decided:**
  - The in-match zoom is free, so players can be seen up close → **full detail by default**; a simpler LOD only if performance needs it or the difference isn't visible.
  - **Height 1.50–2.15 m** (Marcel's range, Claude to confirm — real pros run ~1.53 m to ~2.08–2.10 m, average ~1.83).
  - **Build via sliders/randomness** (not a few presets): width, muscle, thickness etc.
  - **Beards grow with age** (a 17-year-old doesn't have a 33-year-old's beard).
  - **~50 hairstyles, ~10 beard styles.**
  - Order (variety first vs. remaining animations + game integration first): Marcel has no preference — open.
- **Player in the game (2026-11-08, Marcel: start with animations + integration, then variety):**
  - New actions in `build_player.py`: **shoot, pass** (side-foot, smaller swing), **slide** (tackle), **celebrate** (loop, fists up + jumps), **dive_left / dive_right** (keeper), **catch** (keeper, ball tucked into the chest). Contact sheet `design/3d/player/actions.png` (`--poses`). Fixed on the way: the hips "bob" went forwards/backwards instead of up.
  - `player.gd` now instances `assets/models/player.glb` instead of the cylinder figure. Locomotion idle / jog / sprint with playback speed matched to the run speed (jog 6 m/s, sprint 8.4 m/s natural); one-shots: pass/shoot on every kick, slide on a tackle, keeper dive when he flies sideways, catch while he holds the ball, the scoring team celebrates during the goal pause. Stun keeps a small wobble.
  - Kit recolour per team via material overrides (Shirt, Socks = shirt colour; white shorts; black boots); keepers get gloves. Skin/hair colour, one of the 4 hairstyles and a 30% beard chance are still random per player (real variety is the next step).
  - **Shirt numbers** on the back: bold Work Sans `Label3D` on the chest bone (follows the animation), dark or white by shirt brightness. Keeper 1, then 2–11 in formation order. **No names** for now — Marcel can say if he wants them tried.
  - Dev: `--zoom=Z` and `--shot-after=S` for screenshots. Footage: `design/3d/player/match_zoom0.5.mp4`, `match_zoom1.0.mp4`, `lineup_ingame.png`.
- **Player variety, built (2026-11-08):** `scripts/player_look.gd` rolls a look per player from a seed (squad name for your players, `<opponent>#<slot>` for theirs), so the same player always looks the same.
  - **Height** 1.50–2.15 m on a bell curve (mean 1.81, sd 0.07); keepers +6 cm, centre-backs +3 cm. Purely visual for now (whether height affects headers/keepers is **open**). The head grows a bit less than the body on tall players.
  - **Build** via random sliders: shoulder width, muscle (arm/leg thickness, chest depth), belly (grows slightly after 29). Done in `scripts/body_shape.gd`, a SkeletonModifier3D on top of the animations.
  - **Skin** blends between 7 tones; **hair colour** weighted (mostly dark, some blond/ginger); **grey** creeps in from 31 for ~half the players.
  - **51 hairstyles + bald** (`design/3d/player/hairstyles.png`): crops, buzz cuts, fades (flat-top, high-top, curls, twists, spikes), quiffs, side parts, slick back, curtains, spiky, curly ×3, afros ×4, cornrows ×2, twists, dreads ×3, medium/bob/long ×5, mullet, man bun, top knot, ponytail, mohawk, faux hawk, receding/horseshoe/thin crown. Thinning styles get likelier with age, long hair a bit rarer. As Claude said: ~15 base shapes with variations, so a few look alike.
  - **10 beard styles × 3 growth stages** (stubble / short / full; `beards.png`): full, boxed, chinstrap, mutton chops, goatee, van dyke, moustache, horseshoe, long, circle. **Grows with age**: under 19 at most a bit of fluff, then stubble → short → full by ~31; ~30% are clean-shaven. Stubble is tinted towards the skin.
  - The squad has no ages yet, so ages are rolled from the seed (17–36) until the player system gives real ones (`squad[i]["age"]` is used when present).
  - Previews: `variety_lineup.png`, `variety_ageing.png` (same player at 17–37), `variety_ingame.png`. All detail stays at full zoom — no LOD needed so far.
- **Player follow-ups (Marcel, 2026-11-08):**
  - Height stays purely visual for now; **a later step** gives it gameplay meaning (e.g. headers — there are no headers yet).
  - **Names on shirts: "soon", not yet.**
  - Marcel tests the hairstyles/beards in-game and screenshots the ones he doesn't like.
- **Fans v2 — Marcel's wishes (2026-11-08, in discussion, nothing built yet):** the current fans read as blobs. Less detailed than players but more than now; bodies simpler but **not boxy**. Reuse hair/beards, with a much higher chance of "normal" styles (no spikes everywhere). Fans stand up to cheer; some stand and jump, wave arms or clap. A stadium section can be marked as **"harde kern"** (hard core): flags appear there, a small chance per place that grows in higher divisions with more fans. Maybe scarves held up or twirled. Claude asked to lay out his limits first.
- **Fans v2 — Marcel's answers (2026-11-08):**
  - Crowd mostly men, plus women (~10%) and children (~20%) — Marcel's guesses, to check against real demographics (Claude found UK surveys: women ~8–14%, up to 23% at some clubs; ~13% of season tickets went to youngsters in 2009-10).
  - Clothing: club shirt, club sweater or random clothes; far higher club-wear chance in the hard core.
  - **Weather is coming** (not in yet). With temperature: fans in coats when cold; players maybe long sleeves / gloves.
  - **Hard core:** multiple sections allowed, free, no limit, purely visual for now.
  - **Flags** use the club colours, and later the patterns/colours from the planned **shirt editor** and the crest from a possible **logo editor**; on top of that seeded variations.
  - **Scarves** everywhere, higher chance in the hard core; fewer in warm weather (more shirts then).
  - **Away fans:** not yet — goes into the **stadium editor**.
  - **Standing up:** goal → everyone; big chance → some; hard core → always a share standing (Claude's proposal, agreed).
- **Fans v2 — round 2 (Marcel, 2026-11-08):** coats + beanies are built now behind a temperature setting (default mild, cheat to test cold) until weather exists. **Beanies when cold; caps now and then in normal weather, more often when very sunny.** Flags: club colours + seeded patterns (+ sometimes the current crest) until the shirt editor exists — OK. Hard core is a per-section toggle in the Stadium tab — OK. Marcel thought the standing-fan cap was gone: only the seated cap was removed (0a4e60a); standing fans are still capped at 220 → disappears with fans v2.
- **Fans v2 — go (Marcel, 2026-11-08: "Helemaal akkoord"):** crowd **~15% women, ~12% children**. Glasses ~12% of fans, sunglasses only in sunny weather; **no glasses for players**. Order: fan model + animations as a GIF for Marcel to check first, then into the game (hard-core toggle, flags, scarves, temperature cheat).
- **Fans v2 step 1 built (2026-11-08) — test scene only, not in the game yet:**
  - `tools/blender/build_fan.py` → `assets/crowd/fans.json`: low-poly man / woman / child (6–8-sided round tubes, no boxes), the player's skeleton, head, hair and beard builders. 21 "normal" hairstyles (14 men, 7 women, 7 children) + bald; fewer, bigger curls. Every body carries all accessories (coat, long sleeves, neck scarf, cap, beanie, glasses, sunglasses, stubble/beard/goatee/moustache, scarf held up, twirled scarf, flag); the shader switches them on per fan, so they cost no extra variants. ~1,300–1,450 triangles per body incl. hidden accessories, hair 50–950.
  - 14 baked clips (24 fps, bone matrices in a texture): sit_idle, sit_clap, stand_up, sit_down, stand_idle, cheer_jump, cheer_arms, clap_stand, fist_pump, scarf_up, scarf_twirl, flag_wave, despair_sit (face in hands), despair_stand (hands on head). Children are scaled down with a bigger head and lifted onto the seat while sitting (feet dangle).
  - `scripts/fan_crowd.gd` + `fan_crowd.gdshader`: one MultiMesh per body+hair combination; per-fan data = clips + start time + accessories + palette. Reactions: goal → everyone up (jump 35%, arms 25%, fist pump 15%, clap; scarf up/twirl when they have a scarf; flags keep waving), sit down after ~9 s; chance/save → ~35% of sitters stand up, others clap seated, 3.5 s; conceded → face in hands / hands on head, 4.5 s.
  - Rolls: 15% women, 12% children; club wear 40% (hard core 80%, 30% of it a club sweater); coats 75% cold / 18% mild / 0 sunny; scarves 35/15/5% (hard core 80/50/20%); beanies when cold (hard core mostly club colour), caps 6% mild / 25% sunny; sunglasses 25% sunny, otherwise glasses 12%; men: stubble 25%, beard 15%, goatee 7%, moustache 5%; grey hair from 45; hard core: 60% always standing, flags only there (8 patterns: plain, stripes ×2, halves, diagonal, cross, crest on plain/stripes).
  - Dev: `godot --path . --script tools/dev/fan_test.gd [-- cold|mild|sunny]`. Footage `design/3d/fans/fans_v2_test.mp4` (calm → chance → goal → conceded), `fans_v2_calm.png`, `fans_v2_goal.png`.
  - Note for exporting later: `assets/crowd/fans.json` is not a Godot resource → add `*.json` to the export include filter.
  - **Flags fix (Marcel: "op de kop en naar beneden ☠️", "iets groter en dynamischer"):** the pole pointed down out of the hand (wrong bone direction) → now up; pole 2.35 m, cloth 1.55 × 1.0 m (was 1.1 × 0.7), travelling waves + flutter, big side-to-side sweeps with the body twisting along; flag wavers and scarf holders each get their own rhythm. Round 2 (Marcel: people stood *through* their seats; flags should at least go round in a figure 8 and bend, "dit is ass 😂"): standing fans now step ~0.32 m forward off the seat into the leg room; flags sweep a figure 8 (side to side once, up/down twice per loop, 1.7 s) and the cloth drags behind the pole (the further from the pole, the older the frame it follows) on top of the waves. Video updated: `design/3d/fans/fans_v2_test.mp4`.
  - Round 3 feedback (Marcel): better but not natural yet. Real flags are held **more upright than sideways**, **circle above or in front of the person**, and the **cloth follows the pole** much more closely. Marcel offered reference footage; Claude proposed: a separate flag bone driving the pole on a circular path, both hands on the pole via IK in Blender (baked), cloth trailing the tip with a much smaller lag. Waiting for reference + go.
  - Flag style (Marcel): **the classic ultra flag** — circling above the head. Marcel looks for footage (probably stadium crowds).
  - Reference: Marcel's video (Vålerenga flag waver, Aug 2024). Seen in it: long pole held low with both hands, near upright, the tip circling a cone above/in front; the cloth hangs from the top of the pole and trails the rotation; body leans back.
  - **Flag v3 built:** the pole is its own bone (child of the hips) circling a cone — centre 14° forward, radius 18°, so at most ~4° backwards over the people behind and ~18° sideways; 1 circle per 1.7 s; both hands on the pole via IK (baked in Blender): bottom hand at the belly, top hand at the chin; body leans back and twists along. Pole 3.0 m above the bottom hand, cloth 1.9 × 1.3 m on the top of the pole, so it flies above the heads. The cloth trails the tip (small lag) + waves. Marcel's rule: **the pole and the animation must never clip through people**; the cloth may touch someone. Clip `design/3d/fans/fans_v2_flags_close.mp4`; Blender check `--flag-preview [--close]`.
  - Flag v4 (Marcel: "veel beter", but too uniform, too close together, all turning the same way at the same moment, cloth like a thin metal plate — no cloth physics needed): every fan's random rhythm now comes from its position (instance ids repeated across the per-variant MultiMeshes, so flags were in sync); half circle clockwise (`flag_wave_cw`), half counter-clockwise, own speed (±20%) and phase; flag wavers at least **2.6 m** apart (closer ones clap instead); the cloth bends: slow billow + travelling waves + flutter growing towards the free end, the free end sags a bit and lags further behind the pole.
  - Flag v5 (Marcel: "nog iets minder metalen plaat, we komen echt dichtbij"): stronger billow (0.45), bigger waves + ripples running down the cloth, the free end sags *and lifts* over time, the far corners fold in a bit, more lag at the free end.
  - Flag v6 — routines (Marcel: alternate per waver — start with 4 figure 8s, then a circle, then figure 8s again; everything must chain smoothly): I had switched to circles in v3 after the reference without asking — corrected. The tip now follows routines: **4 × figure 8 + 1 circle** or **3 × figure 8 + 1 circle**, each clockwise or counter-clockwise (4 clips: `flag_8x4`, `flag_8x4_cw`, `flag_8x3`, `flag_8x3_cw`), one shape per 40 frames (1.7 s), looping. The 8 (side to side, half as deep front-to-back) and the circle share one point with the same speed and direction, so they flow into each other without a jump (checked: max 4° pole turn per frame everywhere, also at the seams). Each waver picks a routine and starts at their own moment. fans.json is now ~4.3 MB.
  - **Flags approved (Marcel, 2026-11-08: "Ja! We zijn er").** Percentages (3% per hard-core place, 2.6 m apart) are starting values, tuned later. → on to step 2: fans into the game.
- **Fans v2 step 2 — in the game (2026-11-08):**
  - `grounds.spawn_crowd` now uses `FanCrowd` for everyone; the old figures (`fan.gd`, `seated_crowd.gd`, `crowd.gdshader`) are gone. **Every fan is drawn, no cap:** the seats fill first, the rest stands in two rows between the rope and the seats on all four sides (not in front of the dugouts; at an away ground the near side middle is kept for your travelling fans, up to 120 of them in their own crowd in your colours).
  - Seated fans sit on the plank, standing ones (incl. the hard core) stand on the footboard in front of it — the real bleacher leg room matches the 0.32 m step.
  - **Hard core:** Stadium tab → new "Fans" category → "Hard core" card (free); click sections to switch them on/off (keeps toggling until Esc); hard-core sections light up in club green while picking. Saved in the club (`hardcore`). Flag chance per hard-core place: 3% × (1 + attendance / 5,000), capped at ×3, flag wavers ≥ 2.6 m apart.
  - **Temperature** lives in the club (`temperature`: mild by default) until weather exists.
  - Dev cheats (F1): "Weather: mild/cold/sunny" (cycles), "Max stadium" (7-row bleachers on all 28 sections), "Sell out" (fans = seats + 1,200). Dev flags: `--crowd-max` (max stadium, hard core on sections 18–20 and 23–24, sold out, home match) and `--temp=cold|mild|sunny`.
  - Max stadium sold out = **4,998 fans drawn** (3,920 seats + standing), ~1,450 triangles each incl. hidden accessories ≈ 7 M triangles. **Performance unmeasured — Marcel tests fps** with Max stadium + Sell out. If it's too heavy: a simpler fan for far-away stands, only then. Screenshot `design/3d/fans/fans_v2_ingame_full.png`.
- **Crowd performance plan (agreed with Marcel, 2026-11-08 — to do after his fps test or once stadiums grow past ~5,000):** 5,000 fans ≈ 7 M triangles is fine; 50,000 would be ~70 M — too much, even for Marcel's RX 9070 XT (practical budget ~10–30 M triangles per frame at 60 fps; average PCs a half to a third of that). How FIFA-style games manage (techniques, not EA's exact numbers): detail tiers, flat "impostor" cards far away, detail in textures, few unique models + instancing, GPU-baked animation, aggressive culling, a fixed crowd budget. We already have instancing + GPU animation. Plan, biggest win first:
  1. **Per-section crowds (culling):** one MultiMesh group per section, so stands outside the camera aren't drawn (big win in the match camera; nothing when the whole ground is in view).
  2. **LOD:** far sections switch to a simple fan (~150–250 triangles); the farthest maybe impostor cards.
  3. **Drop hidden accessories:** split meshes so fans don't carry invisible coats/beards/flags (~half the triangles now).
  4. **Shared vertices (indexed mesh):** flat shading via derivatives allows it, ~3× less vertex work.
  5. **A crowd budget:** detail drops before the fps does.
  Detail-in-textures (normal maps) doesn't fit the low-poly look — the geometry *is* the style.
- **FPS test (Marcel, 2026-11-08, RX 9070 XT):** Max stadium + sold out (~5,000 fans) — from **144 fps to ~105–108 fps**: "not bad". With vsync off: **122–126 fps** (~8 ms per frame) — **fully zoomed out, so the whole stadium in view: the worst case**. → ~9.5 ms per frame; the crowd plan stays parked until stadiums grow past ~5,000 (an average PC would be around half that fps).
- **FPS overlay (Marcel, 2026-11-08: couldn't find Godot's Monitors tab → "bouw maar in"):** **` (the key left of 1)** anywhere shows fps, ms per frame, triangles, draw calls, fans drawn and vsync state (top right); **Shift+`** turns vsync on/off (to see the real headroom). Was F8/F9 — but F8 stops the game when it runs inside the Godot editor (Marcel: "F8 sluit de game :D"). Dev flag `--fps` starts with it on. Listed in the F1 cheat panel.
- **Saves (Marcel, 2026-11-07):** saves don't matter yet — old saves may simply reset. **Marcel says when a save starts to matter.**
- **Currency:** stays **£** in-game; the sign is just a sign (Marcel). Model numbers in € are used as-is.
- **Sections vs slots (Marcel, 2026-11-07):** move from the 40 small slots to the **~11.5 m sections** of the stand POC (benches/chairs look odd otherwise) — work out what fits in 11.5 m. Also think about the **edges: ad boards, fences/rails, facilities, player dugouts** and similar. Proposal (Claude): 9 sections per long side, 5 per short side; per section 10 m seating + 1.2 m aisle = 5 benches or 20 chairs in a row (20 seats); pitchside layer with ad board + barrier (rope → fence → rail); dugouts fixed in front of the middle section of the main side.
  - **Facilities (decided, Marcel 2026-11-07):** with no stands yet they **take space from chairs**; once your stands are high and big enough they go **under or into the stand**.
- **Build times (Marcel, 2026-11-07: "voelt best goed"), per section, tunable:** chairs/benches instant · bleachers 1 wk · The Shed 2 · main stand 4 · modern tier 6 · 2nd tier 8 · 3rd tier 12 weeks. Extra rows within a stage = half the stage time; corner section ×1.2; +1 week demolition on a stage jump. A section under construction is **closed** (no income from those places).
  - **No limit** on how many sections you build at once (money is the limit) — decided.
  - **Rush build** — decided in principle: pay **+50% cost for 75% of the build time** (Marcel's numbers, tunable).
  - **Off-season: 10 weeks** as a starting point (Marcel, 2026-11-07). Real 2025 reference: PL ~11.5 wk, Championship ~14 wk between last and first match. Effect: everything up to a 2nd tier (8 wk) fits in one summer; a 3rd tier (12 wk) spills 2 weeks into the season, or just fits with rush build (9 wk).
- **Settings (for now):** volume (separate for music / effects / crowd), match length, camera speed.
- **Navigation:** three mockups made (bottom dock, left sidebar, top tabs) — superseded by the ChatGPT design direction below.

### Design process (2026-11-07)
- **ChatGPT designs the UI; Claude builds it in Godot.** Claude wrote the designer brief: [UI Style Guide & Design Brief](https://claude.ai/artifact/QfV7Z8GDX2vMwBspqv6bkm) (what's decided, screen contents, Godot constraints, deliverables).
- Approach: **find a style first, then expand to more screens.**
- Round 1 (ChatGPT): good structure, but too premium (gold on charcoal, oak crest), photo/3D icon art, ground hidden. Feedback sent.
- Round 2: ground visible, one icon style, consistent numbers; still premium colours. Feedback sent: three colour variants on a frozen layout.
- Round 3: three themes delivered with tokens (`design/ui-handoff/sunday_league_ui_tokens.json` + `README_FOR_CLAUDE.md`): Clubhouse Canteen, Chalkboard, Club Colours (red & white).

### Chosen UI style (Marcel, 2026-11-07, revised same day)
- **Clubhouse Noticeboard with club colours.** Panels are paper on a noticeboard: paper strips (top bar, bottom strip), a yellow sticky note ("Our Goal"), a ruled index card with a pin ("Next Match"), small stat tags, tape and pins, each slightly rotated. Marcel: "Clean en toch licht goofy".
- **Club colours drive the accents only:** tape, pins, Play button, selected nav tab, index-card stripe, pen accents ("vs", "Friendly", stat icons) and the own crest. Paper and the sticky note stay as they are. Works for any colour pair (tested red/white and blue/yellow): a light secondary colour falls back to the primary where it would vanish on paper.
- **Light mode is the default. Dark mode is an option:** white/cream surfaces become dark (#25292D / #2C3135), text on them inverts to cream; sticky note, tape, pins, button and selected tab stay unchanged. Club colours used as *text* get a lighter tint in dark mode (e.g. #FF7A83, #8FAEF2) so they stay readable.
- **Fonts:** Kalam (headings, club name, notes, ticker, flavour) + Work Sans (everything functional: stats, buttons, labels).
- **Layout (unchanged):** top bar with stats; "Our Goal" left; "Next Match" right with **both crests**; slim floating bottom strip (ticker + navigation); centre of the ground kept clear.
- **Spec:** [UI Spec v2 (Clubhouse Noticeboard)](https://claude.ai/artifact/JbPtKYncdTQhGp42vJkJR3) — tokens, club-colour rules, component specs, layout and motion notes. Mock-ups: [UI style round canvas](https://claude.ai/artifact/DVUtGedEbLXL7v6A2fPP2m), page "Round 3".
- Claude took over the designer role from ChatGPT for this round (same brief).

### How we got there (2026-11-07)
- First pick was *Chalkboard style in Clubhouse Canteen colours* (Barlow + Caveat). Panel textures for it were tried and rejected: ChatGPT's 512 px grain ("felt/noise"), Claude's procedural textures ("buiten smaak"), then Claude's Flat / A photographic board / B illustrated / C flat + chalk details. Conclusion (Marcel): chalkboard doesn't really work; a full board texture fights "fairly modern".
- Four concepts with free colours/fonts on the same Hub: Matchday Programme, **Clubhouse Noticeboard** (picked), Scoreboard, Sticker Album.
- Dark mode: "dark paper" and "evening (dimmed paper)" takes didn't work; the simple invert version did.

### UI decisions (Marcel, 2026-11-07)
- **Navigation:** 5 items in the bottom strip — **Club** (the hub, selected when you're there), Stadium, Recruitment, Squad, Finances.
- **Build mode:** the preview card (cost, refund, what it adds, Build it / Cancel) **floats beside the 3D ghost**; the **catalogue and the bottom strip stay visible** while building; removals are marked red with "£x back"; Esc stops building.
- **Camera in hub/build:** **Q/E rotate + hold right mouse**, as already built in the hub camera.
- **All "Now" screens mocked up** in noticeboard style, club colours red/white, light: main menu, hub, hub with Play disabled (squad 9/11), recruitment, squad, settings (as a modal over the hub, incl. Light/Dark), post-match summary (+ one dark check), in-match HUD, build preview, build replace, component sheet — canvas page "Round 4". The in-match controls hint uses the real bindings from `main.gd` (dev keys left out).

### League table (Marcel, 2026-11-07)
- **Hub:** the Next Match index card gets a **mini table** under the fixture: 2 teams above, your club, 2 below (Pos, Team, P, Pts), your row marked with a club-colour **highlighter stroke**, and a "Full table →" link in pen style.
- **Full table:** a modal over the hub — an A4 ruled sheet pinned to the board (pin, slight rotation, margin line), header in Kalam ("League table — Season 1"), numbers in Work Sans with tabular figures, columns #, Team, P, W, D, L, GD, Pts, close button top right.
- **Zone lines** (dashed pen lines, Kalam labels in the right margin): "Promotion ↑" under 2nd, a "Play-offs" bracket over 3rd–7th ("+ 18th of the division above"), "Play-off ↕" around 18th, "Relegation ↓" above 19th. Switched on/off per division (see §6). Mock-ups: canvas page "Round 5".

### UI build — round 1 (2026-11-08, Marcel: "Ja! Dat mag zeker")
- Built in Godot: `scripts/ui_kit.gd` (tokens → paper, sticky note, ruled index card with club stripe, tape, pins, primary/link/icon buttons, nav items, stat tags, progress bar, highlighter) and a new `scripts/hub.gd`. Fonts Kalam + Work Sans (variable) in `assets/fonts/` (OFL), icons + crests as SVG in `assets/ui/icons/` (from the design generators).
- Hub = top bar (crest, club name + tagline, stat tags: fans, approval, cash, seats, squad, league position, week/season) + bottom strip (ticker + nav). Tabs: **Club** (Our Goal note + Next Match card with both crests, Play, squad-short warning, mini table + "Full table →"), **Stadium** (build catalogue: Seating = chair/bench, Stands = bleachers/rows incl. rush; unaffordable cards show "£x short"; under-construction list), **Recruitment** (note + candidate cards), **Squad** (table). Full league table as a pinned A4 sheet with zone lines (bottom division: promotion + play-offs only). Dev cheats (F1) as a card.
- Laid out in design pixels (1920×1080) on a board scaled to the window. 2D MSAA on (rotated paper needs it).
- Claude's picks (Marcel can overrule): **club colours = the current green** (Main.HOME_SHIRT) with the spec's club-colour rules (green tape/pins/button/accents; button text follows the contrast rule → ink on green). **Finances** tab shown but disabled until it's built.
- **Round 1b (same day):** post-match summary as a pinned index card (score line with crests, home team left; Attendance / Money / Fans columns; approval breakdown; "Back to the club") + an "Elsewhere today" sticky note with the other results. In-match HUD: score chip top left (3-letter names, crests, score pill, half + clock), big messages (GOAL!, HALF TIME…) on a sticky note, toasts as a paper tag, shot power on paper, controls hint on a paper strip (real bindings only; dev keys are in the F1 panel), minimap as an index card in club/ink dots.
- **Round 1c (Marcel: "Je mag het allemaal afmaken"):**
  - **Main menu** (the game now starts here): title on taped paper, Continue (club · season · week · seats), Start a new club (asks twice when a save exists), Settings, Quit; club-news note; v0.1 tag. The top bar's quit icon goes back to the menu (and saves).
  - **Settings** (modal from the top bar or the menu, saved in `user://settings.json`): Music / Effects / Crowd volume (audio buses; no music exists yet), match length 1–10 min per half (default 3), camera speed (hub/build camera 0.5×–1.5×), **Light / Dark** (dark rebuilds hub + HUD live).
  - **Build preview card** beside the hovered spot while placing: where (side · section · spot), price, you pay, cash after, adds (seats before → after, £ per home match when filled, ready time/date, demolition warning), left click / Esc hints.
  - **Formation card** (4-3-3 sketch) next to the Squad table; empty positions faded.
  - Player name tag in Work Sans, ink on a paper outline; edge arrows in club colour.
- Dev flags: `--settings`, `--preview=item,idx`, `--hub-tab=Name`, `--table`; dev flags that need the hub skip the menu.
- Screens: `design/ui-noticeboard/game/*.png`.
- Not done / open: a real 3D ghost of the item while placing (now: the yellow marker), tooltip/hover states polish, edge-arrow name tags, the Squad "selected player" note, UI scale setting.
- Screens: `design/ui-noticeboard/game/hub_*.png`.

### UI open points
- UI-scale setting (100/125/150%): at 1280×720 uniform scaling makes 14 px text ~9 px.
- Dark base colour (neutral #25292D, warmer, or club-tinted); club-colour swatches next to the club name.
- Flavour copy on the mock-ups (chairman notes, "Signed!" stamp, man of the match etc.): proposal, keep / rewrite / cut.
- **Gameplay idea (Marcel): an in-game "evening mode"** (evening/floodlit matches or hub), with the UI switching to dark mode alongside it. Not decided.

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


## 10h2. The Shed + main stand for real (2026-11-08)
- **Marcel's choices:** next stages after the bleachers are **The Shed** (3 → 5 → 8 rows, ~£5,600 per section from the economy model) and **the main stand** (10 → 12 → 15 rows, ~£50k per section, 4 weeks), so Premier's 5,000 seats are reachable. Corners stay empty for now (to discuss after this).
- **A roof gives (Marcel): more approval, a higher ticket price per covered seat, and fewer fans staying away in bad weather** (the last one once weather exists). Numbers still to agree.
- **Main stand brief (Marcel):** classic English for this tier (roof on columns in front of the seats), concrete terrace + steel trusses + corrugated roof, plastic seats in club colour, simple rear facade with entrances, **players' tunnel in the middle section**. Scoreboard and floodlights are **paid upgrades** later.
- Built (renders only, not in the game yet): `tools/blender/build_shed.py --rows 3|5|8` (roof rises with the rows; `--render-set` for previews) and new `tools/blender/build_main_stand.py --rows 10|12|15 [--tunnel]` (`--render-set full|rows`). Main stand section: 1.5 m paddock walkway, 0.80 m rows, two front columns per section (5.75 m apart, continuous along the side), trussed rafters, deep fascia for a club name later, brick ground floor with windows/doors + cladding at the back, side screens as separate objects (hidden between neighbours). Tunnel section: the first 4 rows make way for a concrete tunnel block with an extendable white canopy with club-colour bands. Renders: `design/3d/the_shed/rows_3_5_8_*.png`, `design/3d/main_stand/*.png`.
- **Feedback round 1 (Marcel, 2026-11-08):**
  - **20 seats per row in the models** (Marcel chose B): gangway 1.0 m instead of 1.2 m, so what you see = what the game counts (bleachers, prices and promotion seat counts all use 20).
  - **Access:** The Shed from the front (walkway + middle gangway; the fake back door is gone). Main stand: a **stair core at the back of every section** up to the rear walkway behind the top row, then down the gangways to your row.
  - **Tunnel section starts above the tunnel over its full width** (no seats with a blocked view): the first 4 rows make way for a podium (dressing rooms, small windows, club band) with the tunnel in it and a rail along its edge.
  - **Slimmer tunnel canopy** (2.3 m wide, ~2.4 m high).
  - Gangways now have real treads (half-height front + full back per row); the black "holes" were the gangway steps hidden inside the row blocks.
  - **Side walls between neighbours:** equal sections: none. **Unequal sections: only the strip between the lower and the higher roof**, drawn by the taller section (both build scripts take the neighbours' row counts; the game will pick the strip per neighbour). Open end: full side screen.
  - Roof numbers agreed: **approval: fans under a roof count 1.5× for the seating part**; **ticket +25% in The Shed, +50% in the main stand** on top of the division price; weather effect once weather exists.
  - Seat positions per variant are exported as `*_seats.json` next to the .glb for the crowd. Seats are real geometry in the model for now; fps is watched (Marcel).

- **In the game (2026-11-08/09):**
  - **Names (Marcel):** the camera side is the main side, **"West"**; opposite **East**; the ends **North** (−x) and **South** (+x). Only names changed. **Dug-outs and the tunnel are on West** (middle section).
  - **Stages per section** (`ClubState.STAGES`): bleachers 3/5/7 (£30/place, 1 wk, rows ½ wk) · **The Shed 3/5/8** (£5,600 per 3 rows ≈ £93/place, 2 wk, rows 1 wk, ticket ×1.25) · **Main stand 10/12/15** (£250/place = £50k, 4 wk, rows 2 wk, ticket ×1.5). Prices fixed, not per division (finetune later). **Skipping stages is fine** (money is the limit). Changing stage = **1 week demolition** first; the old stand is gone (no seats) while the new one goes up. Rush (+50% cost, 75% time) is now **one switch** above the stand cards (8 cards didn't fit on screen).
  - **Tunnel:** only when the **middle West section is a main stand**; that section has 4 rows fewer (the tunnel podium).
  - **Covered seats fill first, dearest stand first** (Marcel); ticket income per seat type; approval: a fan under a roof counts 1.5× for the seating part (`COVERED_APPROVAL` 0.5).
  - Models: 9 variants in `assets/models/the_shed_N.glb` / `main_stand_N[_tunnel].glb`, each with `*_seats.json` (seat positions + roof profile). Placed 2.9 m behind the line. The game builds the side walls per neighbour from the profiles (full at an open end or next to bleachers, none between equal ones, the strip between the roofs between unequal ones). Fans sit on the real seats.
  - **Match camera (Marcel, option B "only what really blocks the view"):** `stand_clip.gdshader` + the fan shader don't draw anything on the West side above the sight line from the camera to the near touchline; `main.gd` updates the global `stand_clip` every frame (follows camera and zoom); off in the hub and for penalties.
  - **Match camera, round 2 (Marcel 2026-11-09, option 2):** the strict sight-line rule left the back of the West roof in view (a "roof carpet" at the bottom of the screen). Now also **everything on the West side above 3 m** (`STAND_CAP`) is left out in matches: roof, columns above 3 m, upper rows; fans whose body would stick out above it aren't drawn at all (no cut heads). You see the front rows of fans, the tunnel and the touchline (`design/3d/stands_ingame/match_west_cap.png`).
  - **Flags under a roof (Marcel 2026-11-09: "vlaggen komen door het dak"):** a flag reaches ~5.4 m above the fan's feet, so in a roofed stand a fan only gets a flag where the row has ≥ 5.6 m to the roof (`FLAG_HEADROOM`, from the roof profile). In practice: The Shed 3/5 rows none, 8 rows the front row; main stand 10 rows the first 3 rows, 15 rows the first 8. The others wave scarves.
  - **No stair towers (Marcel 2026-11-09, option A):** the 14 towers behind the main stands stuck out far too much; the stairs are inside the stand now, the back is a flat facade with doors and windows.
  - Dev: `-- --stands-demo` (every stand type around the ground; `--stands-match` starts a home match with 2,500 fans), `tools/dev/stands_test.gd` (costs, times, demolition, tunnel seats, covered-first tickets, approval, save/load).

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

## 10j. Pitch grass texture (2026-11-08)
**Why:** first real texture test for the pitch (flat stripe colours until now).

**Brief (Marcel):** seamless top-down grass, stylised (not photoreal), 1024×1024, short well-kept grass with subtle blade detail, mid green #4F8A3A–#5E9A45, no stripes/lines/shadows/perspective, flat lighting, plus a greyscale height map.

**How it was made:** procedural (Python), no image AI: periodic noise + ~95k tapered blades drawn with wrap-around, so it tiles perfectly. Three variants made (A_fine, B_clumpy, C_soft).

**Marcel's choices (2026-11-08):**
- **B_clumpy** (bigger blades, visible clumps), with **softer blade outlines**. Darkest pixels end up at #487F35, a little under the #4F8A3A floor of the brief; without outlines the blades disappeared in the narrow colour range.
- Height map: 16-bit + 8-bit + a normal map (OpenGL/+Y, Godot convention).
- Files in `assets/textures/pitch/`: `grass_B_clumpy_albedo.png`, `_height16.png`, `_height8.png`, `_normal.png`, plus `gen.py` (the generator: `python gen.py B_clumpy`).
- In-game: pitch stripes **and** the surrounding grass get the texture, in **all** light modes (incl. `--old-light`).
- Stripes: Marcel wants to compare two tint modes → `GRASS_TINT_MODE` in `scripts/main.gd`:
  - `"match"` (default for now): tint compensated so the pitch averages the old flat stripe/surround colours, blade detail on top.
  - `"multiply"`: old colours used as-is as tint → texture × colour, a much darker pitch.

**Wiring (Claude's picks, tunable):** `_grass_mat()` in `main.gd` — world-space triplanar UVs (texture runs on across the separate stripe boxes), `GRASS_TILE_M = 5.0` m per repeat, anisotropic filtering, normal map on. Height map not used in-game yet (parallax would cost performance; only needed if the normal map is not enough).

- **Fix (2026-11-08):** Marcel saw noise when zoomed out. Cause: the textures were imported **without mipmaps**, so far away the GPU sampled random texels. Albedo + normal now import with mipmaps and VRAM compression (normal map as normal map).

**Open:** which tint mode wins; tile size; whether the height map gets used.

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
    - **Growth per season (Marcel, 2026-11-07, direction):** work in **percentages of the potential, with a cap and a floor** — a great season can't give e.g. +24 in one season, but a 89/93 player with a monster season shouldn't get 0 either. Exact numbers open (Claude proposal pending).
      - **Accepted (Marcel: "de cijfers ogen goed"), tunable:** growth = gap (potential − rating) × base% × playing time × form × training complex × RNG, then cap/floor.
        - base% by age: ≤21 35%, 22–24 25%, 25 → peak 15%
        - playing time ×0.3 (never plays) → ×1.0 (regular starter); form (avg match grade) ×0.7 → ×1.4 (monster season); training complex ×1.0 → ×1.3; RNG ×0.8–1.2
        - cap +8 per season; floor +1 when playing regularly, +2 in a monster season; never above potential
        - examples: 19y 68→88 good regular season → +8 (76); same player benched → +2; 26y 89→93 monster season → +2 (91)
      - **Decline after the peak: same approach. Accepted for now (Marcel: "mag voor nu blijven"), tunable:** decline = current rating × base% × playing time × form × training complex × RNG, then cap/floor.
        - base% by **years past his own peak** (not age): 0–2 y 1%, 3–4 y 2.5%, 5–6 y 4%, 7+ y 6%
        - playing time: regular starter ×0.7, bench ×1.3; form: monster season ×0.6, bad season ×1.3; training complex ×1.0 → ×0.8; RNG ×0.8–1.2
        - cap −10 per season; floor 0 in the first 2 years past peak, then at least −1
        - examples: 1 y past peak, 90, monster season → 0; 4 y past, 88, regular → −2; 6 y past, 84, benched + bad → −8
      - **Retirement chance — accepted to try (Marcel: "oogt goed, gaan we proberen"), tunable:** chance = base by age + modifiers, clamped 0–95%.
        - base by age: ≤30 0%, 31–32 5%, 33 10%, 34 20%, 35 35%, 36 50%, 37 65%, 38+ 80%
        - **drop below his highest rating ever (decided, not potential):** +1.5 pp per point below that peak, first 5 points free
        - playing time: regular starter −5, rotation 0, bench +10; contract: years left −10, expiring/none +10; long injury this season (>3 months) +10, only from age 31
        - examples: 33y 86 (peak 88) regular, 1 y contract → 0%; 34y 82 (peak 85) regular, expiring, long injury → 35%; 35y 76 (peak 88) bench, expiring → ~66%; 37y 70 (peak 90) bench, expiring → 95%
        - **Timing (decided):** the player **announces it somewhere halfway through the season** ("this is my last season"), giving you time to find a replacement. He **can stop during a contract by mutual agreement**.
        - **Decided (Marcel, 2026-11-07):** he always **announces it as soon as it's decided**, then **plays the season out, unless he gets injured** (then he stops right away).
        - **Decided:** you **can refuse** his request to stop, but then **he plays worse (morale)**. **Light version (decided, Marcel 2026-11-07):** refusing gives him one flag, **"unhappy"**: form ×0.8 (tunable) until his contract ends, and his retirement chance stays high. No morale meters or talks. A full morale system can come later if morale shows up elsewhere (e.g. complaints about playing time).
      - **Injuries (decided, Marcel 2026-11-07): no direct rating/potential hit.** Injured time counts as **not playing**: growth stalls for young players (already a big punishment), veterans decline faster (as if benched).
    - **Decided:** **playing well = faster growth**, with a bit of **RNG**.
    - A player **stops growing around his peak**, which differs per player (one at 27, another at 32).
    - **Retirement:** the older the player, the higher the chance he stops, but it also depends on keeping his rating up, playing time, contract length and injuries.
    - Value now = rating + potential + age (replaces the blunt age multiplier table Claude showed; exact formula in the model, tunable).

### Controller support (2026-11-08)
- **Marcel's choices:** controller support after all ("nice-to-have" → now): **matches first** (hub and menus stay mouse for now), **FIFA-style aiming**, **Xbox** buttons, **FIFA-like layout**.
- **Built:** A pass · hold B shoot (power) · X tackle · LB switch player · LT walk (sprint stays the default; a half-tilted stick also walks) · right stick up/down zoom · Start pause (new: freezes the match, Start again to play on) · after the match A/Start = back to the club.
  - Aiming: passes go to the teammate the left stick points at (or the way you face with the stick centred), with the same arrow + pass ring as the mouse; a shot always goes at the goal, stick up/down picks the far/near side (goal marker as with the mouse); keeper kicks, corners and throw-ins follow the stick.
  - Whatever you touched last is in charge: use the pad and the hint at the bottom switches to the pad buttons; touch the mouse/keyboard and it switches back. Keyboard + mouse work exactly as before.
  - Dev: `--pad-test` plays a match with fake controller input (stick, walk, pass, pause, switching back to the keyboard) and prints the results.
  - Not tested with a real controller (none here) — Marcel tests.
  - **Marcel tested (2026-11-08): "Controller voelt best goed!!"** Later: more passing options, e.g. **Y = lob pass**.

### Pass types (2026-11-08)
- **Marcel's choices:** the real FIFA layout ("fifa knoppen kennen we") instead of Claude's first proposal; power is automatic for now; **no error margin yet** (comes with player ratings); cross and chip shot in; headers not yet (next step).
- **Double tap like FIFA (Marcel chose this over Claude's advice; tested 2026-11-08: "valt echt reuze mee, lekker zo laten"):** every pad pass has a short wind-up (`PASS_WINDUP` 0.18 s) between pressing and the kick; a second tap in that window upgrades it. Tunable/revertible if it feels sluggish.
- **Pad (Xbox):**

  | Button | Pass |
  |---|---|
  | A | ground pass |
  | A A | lofted ground pass (half-high: **max ~1.5 m up to ~18 m, rising to ~2 m at 25 m**, Marcel 2026-11-08; further than that the ball's speed caps it and it climbs a bit more) |
  | X | lob (top ~3–8 m); **from the flank in their half (outside the box width) a cross** to the teammate in/near the box closest to the penalty spot (or into the box if nobody's there) |
  | Y | through-ball along the ground, into the space ahead of the most forward teammate in the aim direction |
  | Y Y | lofted through-ball (half-high, **max ~2 m**, Marcel 2026-11-08) |
  | LB + Y | through-ball over the top (high) |
  | LB + B (hold) | chip shot: high, slower, drops just under the bar |

  Without the ball: **A = standing tackle**, **X = sliding tackle**, LB = switch player; with the ball LB is the modifier.
- **Tackles (Marcel 2026-11-08, "precies wat je zegt"):** standing tackle (A / **Space**): a small step in (no lunge), reach 1.5 m, 60% of a slide's chance; miss and you're still on your feet. Sliding tackle (X / **C**, was Space): lunge as before; miss (fail on contact, or slide into nothing) and you're on the floor for 0.5 s. The floor time on a slide into nothing is for your player only; the AI's tackles are unchanged. Later: fouls/cards, more likely from a slide.
- **Quick shot (Marcel chose option B):** release B / RMB within ~0.14 s = a tap = a shot at **60% power**; holding works as before (0–100%, shot on release). Also for penalties and the chip. FIFA works differently (the shot starts on press, power is how long you hold during the wind-up, a tap ≈ 1 of 4 bars; B B = low driven shot), kept in mind for later.
- **Mouse/keyboard (Marcel: controller is the standard, keyboard combos Claude's choice):** instant, no wind-up. Space = standing tackle, C = sliding tackle. LMB pass · **middle mouse** lofted pass · **E** lob/cross · **F** through-ball · **Ctrl+F** lofted through · **Shift+F** over the top · **Ctrl + hold RMB** chip.
- Receivers run onto through-balls; once a through-ball has gone past the meeting point they chase it. Your own receiver waits under a high ball instead of running at it while it's overhead.
- Throw-ins stay throws whatever button. The AI doesn't use the new pass types yet (Marcel: now or later is both fine).
- Ball gravity is 22 (not 9.81), so heights are set by flight time: 0.7 s ≈ 1.3 m, 1.0 s ≈ 2.8 m, 1.4 s ≈ 5.4 m.
- Dev: `-- --tackle-test --menu-skip` (standing vs sliding tackle success and floor time, tap vs held shot). `-- --pass-test2 --menu-skip` plays every pass type with fake pad buttons and prints height, flight and who gets it (opponents frozen; `--pt2-live` lets them play).

### Finances tab + bottom-tier economy (2026-11-08)
- **Marcel's choices:** this step = the Finances tab **plus** the first real money flows for the bottom division (not the whole pyramid yet). The tab shows **this season's in/out per category, a per-match ledger, cash over time and what's coming up**. The club gets **small running costs** from day one. **Mock-up first**, then build.
- Mock-up: `design/ui-noticeboard/mockups/S_Finances.dc.html` (generator `generators/finances.py`, local render `design/ui-noticeboard/finances_preview.png`). Example club halfway a Non-League 3 season.
- **Claude's number proposal (nothing decided), bottom division, £:**
  - In: tickets £2 per seated fan (as now; standing fans pay nothing) · tea hut £1 per visitor (seated + standing) · match subs £1 per player per match (Sunday-league reality: the players chip in) · sponsor £50 per season (paid in week 1) · prize money £1.70 at the end of the season (the GDD joke).
  - Out: pitch hire £8 and referee £5 per home match · kit washing £2 per match · travel £3 per away match · league fee £30 per season (week 1) · building as now.
  - Check against the economy model (NL3 reference club: 15 fans, ~€907 income per season, 45% costs): the reference club ends ≈ +£460 per season; costs ≈ £340.
  - At the very start (5 fans, no seats): a home match = +£16 in (5 tea + 11 subs) vs −£15 out → roughly break-even; away −£5 + £11 subs = +£6. Nobody goes broke, growth comes from seats and fans.
- **Marcel on the mock-up (2026-11-08):** layout is good for now. Build it so it scales: **bigger numbers, more income sources and expenses later**; **opponent crests** in the match list once clubs have logos; match-by-match **not clickable yet, but keep room to make it clickable later**.
- **Numbers approved (Marcel, 2026-11-08):** "Ja dit mag" — variable, the display is fine for now; **shorten amounts once we get near a million** (done: £1.2m). Post-match summary shows the money per match (yes).
- **Built (2026-11-08):**
  - `ClubState`: a **ledger** — every booking (match / season / build) with its lines per category; `book()` does all money changes (pennies carried, prize money is £1.70); `cash_log` for the chart; `season_totals()`. Categories come from `INCOME_CATS` / `EXPENSE_CATS`, so new sources/expenses are one name + where they're booked. Week 1 of every season books sponsor +£50 and league fee −£30 (new game starts on £80); prize money after the last match. Building (chairs, benches, bleachers, rows) goes through the ledger.
  - Match money: home = tickets + tea hut (everyone) + match subs − pitch, ref, kit; away = match subs − kit, travel.
  - **Finances tab** (nav enabled): This season (in/out per category + net), Match by match (newest 6, "+ N earlier"; crest column for opponent logos later; every match stored in full so rows can open later), Cash (step line per week, a dot per week you built something: "4× chair, bench"), Coming up (builds in progress, next match estimate, prize money, next season's week-1 money).
  - **Post-match summary:** money in per line, costs grouped, "This match" net, cash now.
  - Screens: `design/ui-noticeboard/game/finances.png`, `postmatch_money.png`.

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
| 2026-11-07 | UI style revised: chalkboard dropped (all textures rejected); **Clubhouse Noticeboard** with club colours on the accents, Kalam + Work Sans; light default, simple dark mode (surfaces dark, text inverted, accents unchanged) as an option (§10e) |
| 2026-11-07 | UI design round done by Claude instead of ChatGPT (same brief) |
| 2026-11-07 | UI: 5th nav item "Club"; build preview floats beside the ghost; catalogue + bottom strip stay visible in build mode; camera Q/E + right mouse; all "Now" screens mocked up (canvas "Round 4") |
| 2026-11-07 | Promotion/relegation: 1–2 up, 19–20 down, play-offs 3rd–7th + 18th of the division above for the last spot; lines switch off per division (no relegation from Non-League 3, no promotion from the Premier Division) (§6) |
| 2026-11-07 | League table UI: mini table on the Next Match card + full table as a pinned A4 sheet with zone lines (§10e) |
| 2026-11-07 | 3D test asset The Shed: "High quality Low Poly", 3 rows, 11.5 m sections (9 per side = 103.5 m), steel + corrugated roof, plastic seats, generic colours with recolourable club materials (§10f) |
| 2026-11-07 | Stands bought per section; side screen disappears between adjacent sections; club colours are a buyable upgrade you apply yourself (§10f) |
| 2026-11-07 | Workflow: Claude commits + pushes, Marcel pulls manually (no auto-pull for now) |
| 2026-11-07 | Surplus = free choice between stadium and squad (both needed); player ratings 1–99, 99 near-impossible |
| 2026-11-07 | Economy reference model v2 (real vs game, cliffs flattened) accepted for now, open for tweaking (§10b) |
| 2026-11-07 | Economy model v4: Transfers tab + 1–99 rating value curve (proposal, §10b) |
| 2026-11-07 | Player value depends on age too: old stars cheap but short-lived (§10b) |
| 2026-11-07 | Off-season = 10 weeks (starting point) |
| 2026-11-07 | Calendar: weeks can hold several matches; 19 home/19 away, no home+away vs same opponent in one half; away matches played in seeded away grounds; facilities take chair space until stands can hold them; currency stays £ |
| 2026-11-07 | Build times per section per stage, sections closed while building, no parallel limit, rush build +50% cost → 75% time (§10a) |
| 2026-11-07 | Refusing a retirement = light 'unhappy' flag (form ×0.8 till contract end), no full morale system yet (§10b) |
| 2026-11-07 | Retirement chance accepted to try: age base + drop from highest rating ever + playing time/contract/injury; announced mid-season, can stop during contract by mutual agreement (§10b) |
| 2026-11-07 | Growth & decline formulas accepted for now (% based, cap/floor, form + RNG); injuries only via lost playing time (§10b) |
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
| 2026-11-08 | Pitch grass texture: B_clumpy with softer outlines, on pitch + surround in all light modes; tint mode "match" vs "multiply" to compare (§10j) |

## 13. Open questions

**Name**
- Other things already use the name "Sunday League": a browser football/club-management game (github MrPavian/sunday-league), Steam game *Sunday League Manager: Horse & Spoon* (2025), an itch.io game *Sunday League Football* (2018), a board game. Fine as working title; worth deciding before going public.

**Tech**
- GDScript (as in the PoC) or C#? Switching later means a rewrite.
- Art style: UI decided (§10e, Clubhouse Noticeboard). 3D direction from Marcel: "High quality Low Poly" (§10f); final verdict waits on The Shed test.

**Pyramid**
- League names.
- Exact tier count: is League 1 the "Premier Division", or does the Premier Division sit above League 1?
- Play-off format (bracket, one or two legs, home advantage); who takes part is decided (§6).
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
- How fans are counted and what they do for you.
- Training, staff roles, youth.
- Season calendar (pre-season, cups, Europe).
- Save system.
