# Sunday League — PoC

Proof of fun for Sunday League. Godot 4.7, GDScript, no assets: everything is built from primitives in code.

## Starten
1. Download Godot 4.7.2 (standard version, not .NET) from godotengine.org
2. Open Godot → **Import** → pick `project.godot` in this folder
3. Press **F5** (or the ▶ button top right)

## Hub (between matches)
- Shop: buy a chair or bench, then click a highlighted section along a touchline. Chairs stack up to 4 per section. Right-click / Esc cancels.
- "Who can play for you": recruit people until you have 11, then press **Play friendly**.
- WASD / arrows pan the view, mouse wheel zooms.
- The game saves after each match and after every purchase/recruit. "New game" (click twice) wipes the save.

## Controls (match)
| Key | Action |
|---|---|
| WASD / arrows | move |
| Shift | sprint |
| Mouse | aim |
| Left click | pass (white ring = who gets it, else a pass into space) |
| Hold right click | charge shot. aim the arrow at the goal: the yellow ring on the goal shows where it goes. more power = faster + higher but less accurate |
| Space | sliding/lunge tackle (no ball) |
| Q | switch to the teammate nearest the ball (press again quickly to cycle) |
| Mouse wheel | zoom the camera |
| R | restart match |
| Esc | quit |

Control switches automatically when you pass, when a teammate wins the ball, on a loose ball a teammate is clearly closer to, and when you've been beaten.
You also take your own set pieces (corner, throw-in, goal kick).
When your keeper holds the ball, you control him: LMB pass, hold RMB for a long kick.
If you don't press anything while a pass is coming to you, your player runs to meet it.

## Tweaking
Everything worth tuning is a `const` at the top of the scripts:
- `scripts/main.gd` → pitch (105 x 68 m), `HALF_SECONDS`, `FORMATION_433`, camera offset in `_place_camera()`
- `scripts/main.gd` → difficulty block: steal times, tackle success, AI shot range/accuracy, keeper reaction/dive/reach per team
- `scripts/player.gd` → speeds, acceleration
- `scripts/ball.gd` → gravity, friction, bounce

## Files
- `scripts/main.gd` — world building, input, possession, match flow, HUD
- `scripts/player.gd` — movement, visuals, AI
- `scripts/ball.gd` — arcade ball physics
- `scripts/util.gd` — mesh/material helpers

## Dev
AI vs AI headless test: `godot --headless --path . --fixed-fps 60 -- --autoplay` (add `--trace` to log ball/holder every 5s)
Set-piece test: `-- --autoplay --restart-test` forces corners, throw-ins, goal kicks and offsides.
Club flow test: `-- --hub-test` (prints state, placement, match summary, save round-trip).
Quick friendly (2x3 s, then summary + autosave): `-- --quick-friendly`.
3D test asset The Shed on the north side: `-- --shed` (combine with `--hub-view=0,-30,0.55,25` for a close look). Rebuild the model: `python3 tools/blender/build_shed.py [--render]` (needs `pip install bpy`).
Lighting (GDD §10g): default is fancy (AgX, SSAO, softer sun, calmer grass, global illumination, glow, haze). Lighter: `-- --new-light` (no GI/glow/haze). Original: `-- --old-light`.
Shot test (90 shots at their keeper): `godot --headless --path . --fixed-fps 60 -- --shot-test`
