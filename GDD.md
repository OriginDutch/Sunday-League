# Sunday League — Game Design Document

> Living document. Only contains what Marcel has decided. Anything not decided is listed under **Open questions**.
> Rule for this project: Claude decides nothing unless Marcel explicitly says Claude may decide.

Last updated: 2026-11-07

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

### Play or autoplay

- You can play every match yourself for potentially higher rewards.
- Or autoplay: the result is a probability calculation based on player ratings.
- Autoplay rewards start at **75%** of playing yourself (tunable).

## 8. Players

- Players have **stats, names, positions and personalities**.
- Personality affects: atmosphere, attracting fans, stats, expectations about playing time, team chemistry ("that kind of thing").
- **Recruitment early on:** randoms from the street, the pub, the supermarket — anywhere you can get them from.
- **Recruitment later:** transfers from other clubs in the divisions, with money and contracts.

## 9. Your club

- Create your own club: **name, logo, colours, shirt & pattern, sponsors**.

## 10. Club building (tycoon side)

- Build, attract fans, advertising, attract sponsors.
- Building is done through **upgrades** (not free placement), with a **large list and many options**, so no two saves play the same or end up with the same stadium.
- Long-term stadium includes **trainers, staff, referees, linesmen** and above all **fans**.
- The number of fans grows with your club status, eventually perhaps **thousands, with simple animations**.

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

## 12. Decisions log

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

**Not discussed yet** (here so they don't get lost)
- Economy: income/costs, how sponsors and advertising work.
- Stadium upgrade list: categories and contents.
- How fans are counted and what they do for you.
- Training, staff roles, youth.
- Season calendar (pre-season, cups, Europe).
- Save system.
- Milestones / what goes into v0.1.
