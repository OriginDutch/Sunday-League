# Sunday League — Game Design Document

> Living document. Only contains what Marcel has decided. Anything not decided is listed under **Open questions**.
> Rule for this project: Claude decides nothing unless Marcel explicitly says Claude may decide.

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
- You control the player nearest the ball (auto-switch). AI teammates know roughly where to go and which position they belong in.
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
- Purchases and recruits between matches are only saved by the autosave after the next match.
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
| 2026-11-07 | PoC: simple restarts (throw-in, corner, goal kick), 4-3-3, halves + switching sides, offside |

## 13. Open questions

**Name**
- Other things already use the name "Sunday League": a browser football/club-management game (github MrPavian/sunday-league), Steam game *Sunday League Manager: Horse & Spoon* (2025), an itch.io game *Sunday League Football* (2018), a board game. Fine as working title; worth deciding before going public.

**Tech**
- GDScript (as in the PoC) or C#? Switching later means a rewrite.
- Art style: not decided.

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
- Growth, ageing, retirement.

**Not discussed yet** (here so they don't get lost)
- Economy: safety net (see §10b), exact expense list, performance bonuses.
- Stadium upgrade list: full categories, costs and effects (§10a has the direction).
- Off-season length (x weeks).
- How fans are counted and what they do for you.
- Training, staff roles, youth.
- Season calendar (pre-season, cups, Europe).
- Save system.
