class_name Main
extends Node3D
const LeagueScript = preload("res://scripts/league.gd")
const Kit = preload("res://scripts/ui_kit.gd")
const SettingsScript = preload("res://scripts/settings.gd")
## Football PoC — builds the pitch, spawns teams, handles input, possession, match flow and HUD.
## 11v11 on a full-size pitch: two halves (switching sides), throw-ins, corners, goal kicks, offside.

const HALF_L := 52.5        # full-size pitch: 105 x 68 m
const HALF_W := 34.0
const SCALE_X := HALF_L / 20.0   # scenery was laid out for a 40 x 25 pitch
const SCALE_Z := HALF_W / 12.5
const GOAL_W := 7.32
const GOAL_H := 2.44
const GOAL_DEPTH := 2.0
const BOX_DEPTH := 16.5          # penalty area
const BOX_HALF_W := 20.16
const GOAL_AREA_DEPTH := 5.5
const GOAL_AREA_HALF_W := 9.16
const HALF_SECONDS := 180.0      # 3 minutes per half
const KEEPER_RUSH_DEPTH := 7.0   # keeper comes off his line for loose balls inside this zone
const KEEPER_RUSH_HALF_W := 10.0
const SUPPORT_PUSH := 20.0       # how far the team pushes up when in possession
const MARK_RADIUS := 12.0        # defenders pick up attackers this close to their zone

# ---- difficulty levels (Marcel, 2026-11-07: one fixed level for now, more later) ------------
# Everything that makes the match easier or harder for YOU lives here, per level. Add a level =
# add an entry; pick it with Main.difficulty. "normal" was tuned after "solo beats passing" (10-0).
const DIFFICULTY_LEVELS := {
	"normal": {
		"human_speed_bonus": 1.04,       # was 1.10: your player runs a bit faster than the AI
		"human_dribble_speed": 0.88,     # was 0.92: same as the AI's dribble speed now
		"human_steal_time": 0.5,         # was 0.3: you pressing the AI carrier
		"ai_steal_time_vs_human": 0.8,   # was 1.2: AI pressing you (same as AI vs AI now)
		"human_tackle_success": 0.7,     # was 0.85
		"ai_tackle_success": 0.6,        # was 0.55
		"ai_tackle_rate_vs_human": 1.0,  # was 0.7 tackle attempts per second when close to you
		"ai_shot_error": 1.4,            # was 1.6 (1.0 = as accurate as you)
		"their_keeper_reaction": 0.18,   # was 0.28 s (yours: 0.14)
		"their_keeper_dive": 8.0,        # was 7.0 m/s (yours: 8.5)
		"their_keeper_reach": 0.88,      # was 0.80 m (yours: 0.90)
		"their_keeper_parry": 0.5,       # was 0.6: chance their keeper parries instead of catching a hard shot
	},
}
static var difficulty := "normal"


static func diff(key: String) -> float:
	return float(DIFFICULTY_LEVELS[difficulty][key])


static func keeper_reaction(team: int) -> float:
	return 0.14 if team == 0 else diff("their_keeper_reaction")


static func keeper_dive(team: int) -> float:
	return 8.5 if team == 0 else diff("their_keeper_dive")


static func keeper_reach(team: int) -> float:
	return 0.9 if team == 0 else diff("their_keeper_reach")


# ---- feel knobs (same on every level) -----------------------------------------
const AI_DRIBBLE_SPEED := 0.88          # same for AI ball carriers
const HUMAN_PROTECT := 0.9             # seconds you can't be robbed after receiving
const AI_STEAL_TIME := 0.8            # AI vs AI: pressing time needed to nick the ball
const AI_TACKLE_RATE := 0.5            # AI vs AI tackle attempts per second when close
const AI_TACKLE_START_RANGE := 1.4     # AI only lunges when this close to the ball
const AI_TACKLE_LUNGE := 7.0           # lunge speed (m/s) for 0.35 s
const HUMAN_TACKLE_LUNGE := 10.0
const POKE_REACH := 1.5                # standing tackle (A / Space) reach...
const POKE_SUCCESS := 0.6              # ...and chance relative to a slide
const SHOT_TAP := 0.15                 # released before this charge (≈0.14 s) = a tap...
const SHOT_TAP_POWER := 0.6            # ...which shoots at this power (Marcel 2026-11-08)
const AI_JOCKEY_DISTANCE := 1.6        # AI presser keeps this gap when you have the ball
const AI_JOCKEY_DISTANCE_AI := 1.1     # ...and this gap against an AI carrier
const MARK_DISTANCE := 2.2             # markers stand this far goal-side of their man
const COVER_DISTANCE := 4.5            # second defender covers this far goal-side of the ball carrier
const COVER_SIDE := 3.0                # ...and this far towards the middle (not in a line behind the presser)
const SEPARATION_RADIUS := 4.0         # teammates (not chasing the ball) keep about this much room
const SEPARATION_STRENGTH := 0.9
const MAX_SHOW_RUNNERS := 2            # at most this many players come short for the ball at once
const BLOCK_LINE_FACTOR := 0.5         # back line depth = ball depth from own goal x this
const BLOCK_MIN_DEPTH := 8.0           # back line never deeper than this (m from own goal line)
const BLOCK_MAX_DEPTH := 36.0          # ...nor higher than this
const BLOCK_FORM_BACK := 14.5          # formation depth of the back four
const STEP_OUT_DISTANCE := 2.5         # zone owner steps out to this distance from the ball carrier
const STEP_OUT_RADIUS := 10.0          # ...when the carrier is within this distance of his zone
const INTERCEPT_RANGE := 5.0           # AI goes for a pass passing within this distance
const PASS_LEAD := 0.7                 # how much of the receiver's run the pass leads
const RECEIVE_REACH := 1.1             # the intended receiver controls the ball from this far (others: 0.7, you 0.85)
const RECEIVE_ASSIST := true           # your receiver runs to the ball by himself while your pass is on its way
const LOB_PASS_DISTANCE := 30.0        # passes longer than this go through the air
const LOOSE_SWITCH_MARGIN := 5.0       # auto-switch on a loose ball only if a teammate is this much closer
const BEATEN_MARGIN := 3.0             # ball carrier this far past you -> switch to a goal-side teammate
const THROW_IN_DISTANCE := 3.0         # opponents keep this distance at a throw-in (9.15 m otherwise)
const AI_SHOOT_RANGE := 25.0

# 4-3-3 for a team attacking +X (x = length, y here = width; -y is the left flank). mirrored for the other side.
const FORMATION_433 := [
	Vector2(-36, -22), Vector2(-40, -8), Vector2(-40, 8), Vector2(-36, 22),   # LB LCB RCB RB
	Vector2(-22, -12), Vector2(-26, 0), Vector2(-22, 12),                      # LCM CDM RCM
	Vector2(-10, -22), Vector2(-3, 0), Vector2(-10, 22),                       # LW ST RW
]

const HOME_SHIRT := Color(0.12, 0.62, 0.28)
const AWAY_SHIRT := Color(0.82, 0.2, 0.18)
const HOME_GK := Color(0.95, 0.8, 0.15)
const AWAY_GK := Color(0.45, 0.3, 0.75)

var ball: Ball
var players: Array[Player] = []
var home: Array[Player] = []
var away: Array[Player] = []
var controlled: Player = null

var score := [0, 0]
var time_left := HALF_SECONDS
var half := 1
var first_kickoff_team := 0
var state := "kickoff"     # kickoff | play | restart | goal | halftime | fulltime | shottest
var state_timer := 0.0
var autoplay := false      # `-- --autoplay`: AI vs AI, used for headless testing
var _conceding_team := 0
var stats := {"shots": [0, 0], "steals": [0, 0], "saves": [0, 0], "offside": [0, 0], "corners": [0, 0], "throw-ins": [0, 0], "goal kicks": [0, 0], "passes": [0, 0], "completed": [0, 0], "intercepts": [0, 0], "bailouts": [0, 0]}  # printed at full time (dev)

var camera: Camera3D
var cam_target := Vector3.ZERO
var aim_point := Vector3.ZERO
# Controller (Marcel, 2026-11-08: matches first, FIFA-style aiming, Xbox layout). The last device you
# touched decides how you aim and which hint is shown.
const PAD_DEADZONE := 0.22
const PAD_WALK_TILT := 0.5            # stick tilted less than this = walk (sprint is the default)
var pad_active := false
var pad_device := 0
var paused := false
var hint_label: Label
var charging := false
var charge := 0.0
var switch_cooldown := 0.0

# club / hub (v0.1)
var mode := "hub"           # hub | match | summary
var club: ClubState
var grounds: Grounds
var hub: Hub
var hud_layer: CanvasLayer
var opponent_name := "AWAY"
var match_home := true                 # league: are we at home this match
var match_opp_strength := 1.0          # league: opponent strength (speed multiplier)
const AWAY_TRAVEL_SHARE := 0.2         # share of your fans that come along to away matches (tunable)
var placing_item := ""
var hover_slot := -1
var name_label: Label3D
var sfx: Sfx

var ring: MeshInstance3D
var pass_ring: MeshInstance3D
var aim_pivot: Node3D
var aim_arrow: MeshInstance3D
var aim_mat: StandardMaterial3D
var goal_marker: MeshInstance3D
var score_label: Label
var msg_label: Label
var toast_label: Label
var toast_timer := 0.0
var hud_board: Control
var hud_team_l: Label
var hud_team_r: Label
var hud_crest_l: TextureRect
var hud_crest_r: TextureRect
var hud_half: Label
var hud_clock: Label
var hud_msg_note: Control
var hud_toast: Control
var hud_power: Control
var hud_power_bar: ProgressBar
var hud_power_pct: Label


# lighting (GDD §10g): "fancy" = default (options 1-5), "new" = 1-4 (--new-light), "old" = original (--old-light)
var light_mode := "fancy"


func _ready() -> void:
	randomize()
	var args := OS.get_cmdline_user_args()
	autoplay = "--autoplay" in args or "--shot-test" in args
	_ui_demo = "--ui-demo" in args
	_bunch_test = "--bunch-test" in args
	if "--old-light" in args:
		light_mode = "old"
	elif "--new-light" in args:
		light_mode = "new"
	SettingsScript.load_all()
	Kit.dark = SettingsScript.dark
	_build_environment()
	_build_pitch()
	_build_goals()
	_build_scenery()
	ball = Ball.new()
	add_child(ball)
	ball.setup(self)
	_build_camera()
	_build_hud()
	_build_indicators()
	name_label = Label3D.new()
	name_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	name_label.font = Kit.font(false, 700)   # noticeboard style: ink on a paper-coloured outline
	name_label.modulate = Kit.c("ink")
	name_label.outline_modulate = Kit.c("paper")
	name_label.font_size = 64
	name_label.outline_size = 22
	name_label.pixel_size = 0.01
	name_label.no_depth_test = true
	name_label.visible = false
	add_child(name_label)

	if autoplay:
		club = ClubState.new_game()   # throwaway club for tests, never saved
		while club.squad.size() < ClubState.SQUAD_SIZE:
			club.recruit(0)
	else:
		club = ClubState.load_or_new()
	sfx = Sfx.new()
	add_child(sfx)
	grounds = Grounds.new()
	add_child(grounds)
	grounds.setup(club)
	hub = Hub.new()
	add_child(hub)
	hub.build(self)
	hub.set_club(club)

	if autoplay or _ui_demo:
		if _ui_demo:
			while club.squad.size() < ClubState.SQUAD_SIZE:
				club.recruit(0)
		for a in args:
			if a.begins_with("--temp="):
				club.temperature = a.trim_prefix("--temp=")     # dev: crowd clothing cold / mild / sunny
		if "--crowd-max" in args:
			# dev (fps test): bleachers everywhere, two hard-core ends, sold out
			cheat_max_stadium()
			for sec in [18, 19, 20, 23, 24]:
				club.hardcore[str(sec)] = true
			club.fans = club.seats() + 1200
		start_friendly()
		if "--crowd-max" in args:
			var shown := 0
			var flags := 0
			for c in grounds.crowds:
				shown += c.fan_count()
				flags += c.flag_count()
			print("CROWD MAX: %d fans drawn (%d seats, %d flags), temperature %s" % [shown, club.seats(), flags, club.temperature])
		if "--shot-test" in args:
			_shot_test_begin()
	else:
		var dev_hub: bool = Array(args).any(func(a: String) -> bool:
			return a.begins_with("--hub") or a.begins_with("--away-view") or a.begins_with("--sim-rounds") \
				or a in ["--table", "--cheats", "--fill-test", "--shed", "--bigstand"])
		if not dev_hub and "--menu-skip" not in args:
			hub.screen = "menu"   # the game starts on the main menu (GDD §10e)
		_enter_hub()
	for arg in args:
		if arg.begins_with("--fast="):
			# dev: run the simulation N times faster with the same 1/60 s step (headless balance tests)
			var n := int(arg.trim_prefix("--fast="))
			Engine.physics_ticks_per_second = 60 * n
			Engine.max_physics_steps_per_frame = 8 * n
			Engine.time_scale = n
	if "--pass-test" in args:
		_pass_test()
	if "--hub-test" in args:
		_hub_test()
	for arg in args:
		if arg.begins_with("--hub-view="):
			# dev: --hub-view=x,z,zoom  (and hide the hub UI for clean screenshots)
			var v := arg.substr(11).split(",")
			hub_focus = Vector3(float(v[0]), 0, float(v[1]))
			hub_zoom = float(v[2])
			if v.size() > 3:
				hub_yaw = deg_to_rad(float(v[3]))
			if v.size() > 4:
				hub_pitch = float(v[4])   # degrees above the ground
			hub.root.visible = false
			_hub_camera()
	for arg in args:
		if arg.begins_with("--hub-tab="):
			hub.tab = arg.trim_prefix("--hub-tab=")   # dev: open the hub on a tab (screenshots)
			hub.refresh()
	if "--settings" in args:
		hub.settings_open = true   # dev: open the settings modal
		hub.refresh()
	for arg in args:
		if arg.begins_with("--preview="):
			# dev: show the build preview card, e.g. --preview=bleachers,3
			var pv := arg.trim_prefix("--preview=").split(",")
			placing_item = pv[0]
			hub.refresh()
			hub.update_preview(pv[0], int(pv[1]), get_viewport().get_visible_rect().size * Vector2(0.55, 0.45))
	if "--table" in args:
		hub.table_open = true   # dev: open the full league table
		hub.refresh()
	if "--cheats" in args:
		hub.cheats_open = true   # dev: open the cheat panel at start (F1 toggles it)
		hub.refresh()
	for arg in args:
		if arg.begins_with("--away-view="):
			# dev: show the seeded away ground of a club name with its crowd, e.g. --away-view="Red Lion FC"
			var nm := arg.trim_prefix("--away-view=")
			var hf := grounds.use_away(nm, 1.0)
			grounds.spawn_crowd(hf, 12)
			print("AWAY %s: %d home fans, %d spots" % [nm, hf, grounds.active_slots.size()])
	if "--shed" in args:
		# dev: preview the first 3D asset (The Shed, one 11.5 m section) on the north side
		var shed: Node3D = load("res://assets/models/the_shed.glb").instantiate()
		shed.position = Vector3(0, 0, -(HALF_W + 3.0))
		add_child(shed)
	if "--bigstand" in args:
		# dev: big two-tier stand POC (GDD §10i) along the north touchline, 6 m behind it
		var bs = load("res://scripts/big_stand.gd").new()  # by path: works before the editor rescans class names
		bs.position = Vector3(0, 0, -(HALF_W + 6.0))
		add_child(bs)
		# floodlight masts in all 4 corners, 8 m diagonally out from the corner flags, aimed at the centre spot
		var mast_scene := load("res://assets/models/floodlight_mast.glb") as PackedScene
		if mast_scene:
			for sx in [-1, 1]:
				for sz in [-1, 1]:
					var mast: Node3D = mast_scene.instantiate()
					mast.position = Vector3(sx * (HALF_L + 8.0), 0, sz * (HALF_W + 8.0))
					mast.rotation.y = atan2(-mast.position.x, -mast.position.z)
					add_child(mast)
		for arg in args:
			if arg.begins_with("--club-colours="):
				# dev: --club-colours=primaryhex,secondaryhex  (demo of the club colours upgrade)
				var cc: PackedStringArray = arg.trim_prefix("--club-colours=").split(",")
				bs.set_club_colours(Color(cc[0]), Color(cc[1]))
	if "--stands-demo" in args:
		# dev: every stand type around the ground (screenshots): West main stand with the tunnel, East a
		# Shed mix 3/5/8 next to bleachers, North main 10/12, South bleachers
		club.builds.clear()
		club.sections.clear()
		club.slots.clear()
		for k in 9:
			club.sections[str(9 + k)] = {"stage": "main", "rows": [10, 12, 15, 15, 15, 15, 15, 12, 10][k]}
			club.sections[str(k)] = {"stage": ["shed", "shed", "shed", "bleachers", "shed", "shed", "shed", "bleachers", "shed"][k],
				"rows": [3, 5, 8, 7, 8, 8, 5, 5, 3][k]}
		for k in 5:
			club.sections[str(18 + k)] = {"stage": "main", "rows": [10, 12, 12, 12, 10][k]}
			club.sections[str(23 + k)] = {"stage": "bleachers", "rows": 7}
		grounds.rebuild_furniture()
		hub.refresh()
		print("STANDS DEMO seats ", club.seats(), " tiers ", club.seat_tiers())
		if "--stands-match" in args:
			club.fans = 2500
			while club.squad.size() < ClubState.SQUAD_SIZE:
				club.recruit(0)
			start_friendly()
	if "--fps" in args:
		_toggle_fps()
	if "--tackle-test" in args:
		# dev: standing tackle (A) vs slide (X) success and miss behaviour, plus the B tap shot
		while club.squad.size() < ClubState.SQUAD_SIZE:
			club.recruit(0)
		start_friendly()
		_tt = 0.0
	if "--pass-test2" in args:
		# dev: every pass type with fake pad buttons; prints the ball's flight and who gets it
		while club.squad.size() < ClubState.SQUAD_SIZE:
			club.recruit(0)
		start_friendly()
		_pt2 = 0.0
	if "--pad-test" in args:
		# dev: drive a match with fake controller events and print what happens
		while club.squad.size() < ClubState.SQUAD_SIZE:
			club.recruit(0)
		start_friendly()
		_pad_test = 0.0
	if "--playoff-test" in args:
		_playoff_test_setup()
	if "--quick-friendly" in args:
		# dev: play a 2x3s friendly with nobody at the controls, then show the summary
		start_friendly()
		time_left = 3.0
		_quick = true


# dev: `-- --playoff-test --menu-skip`: a new club finishes 3rd–7th, loses the first play-off leg 0–1,
# then the second leg is forced level -> extra time -> penalties (your kicks auto-taken). Screenshots in /tmp/po_*.png.
var _po_test := -1.0
var _po_flags := {}


func _playoff_test_setup() -> void:
	seed(11)
	club = ClubState.new_game()
	grounds.state = club
	while club.squad.size() < ClubState.SQUAD_SIZE:
		club.recruit(0)
	club.slots["0"] = "chairs:4"
	club.slots["1"] = "chairs:4"
	club.slots["2"] = "chairs:4"
	grounds.rebuild_furniture()
	var w := 0
	while not club.league.season_over():
		var r: Vector2i = [Vector2i(3, 0), Vector2i(1, 1), Vector2i(0, 2), Vector2i(2, 1)][w % 4]
		club.league.play_round(r.x, r.y)
		w += 1
	club.end_season_money()
	print("PO TEST finished %d, seats %d, in play-offs: %s" % [club.league.position_of(0), club.seats(), not club.playoff.is_empty()])
	var pf := club.playoff_fixture()
	if pf.is_empty():
		print("PO TEST not in the play-offs, stopping")
		get_tree().quit()
		return
	if int(pf["leg"]) == 0:
		club.apply_match(0, 1, 3, pf["home"], pf["opponent"]["name"])
		club.record_playoff_leg(pf["tie"], 0, 1)
	start_friendly()
	print("PO TEST second leg vs %s, ctx %s" % [opponent_name, str(match_ctx)])
	_po_test = 0.0


func _po_shot(name: String) -> void:
	if _po_flags.has(name):
		return
	_po_flags[name] = true
	if DisplayServer.get_name() == "headless":
		print("PO TEST (headless, no shot) ", name)
		return
	var img := get_viewport().get_texture().get_image()
	img.save_png("/tmp/po_%s.png" % name)
	print("PO TEST shot ", name)


func _po_test_tick(delta: float) -> void:
	_po_test += delta
	if mode == "match" and half == 1 and state == "play" and not _po_flags.has("skip1"):
		_po_flags["skip1"] = true
		var fl: Array = match_ctx["first_leg"]
		score = [int(fl[1]) - int(fl[0]) + 1, 1]   # level on aggregate
		half = 2
		time_left = 0.5
	if mode == "match" and half >= 3 and state == "play":
		if not _po_flags.has("et%d" % half):
			_po_flags["et%d" % half] = true
			time_left = 1.5
		elif time_left < 1.0:
			_po_shot("extratime")
	if mode == "match" and state == "penalties" and "--po-skip" in OS.get_cmdline_user_args() and pens["phase"] == "aim":
		# dev: jump to the end of the shootout (rendering it is slow here): we win 4–3
		pens["goals"] = [4, 3]
		pens["taken"] = [5, 5]
		pens["winner"] = 0
		pens["phase"] = "done"
		pens["timer"] = 2.9
		msg_label.text = "WE WIN ON PENALTIES  4 - 3"
	if mode == "match" and state == "penalties":
		var tmr: float = pens["timer"]
		if pens["human"] and pens["phase"] == "aim":
			if tmr > 0.8 and not charging and not _po_flags.has("press%d" % pens["taken"][0]):
				_po_flags["press%d" % pens["taken"][0]] = true
				_pen_button(true)
			elif charging and charge > 0.55:
				_po_shot("pen_aim")
				_pen_button(false)
				pens["z"] = randf_range(-3.3, 3.3)
		if pens["phase"] == "flight" and tmr > 0.2:
			_po_shot("pen_flight")
		if pens["phase"] == "result" and tmr > 0.6:
			_po_shot("pen_result_" + str(pens["outcome"]))
		if pens["phase"] == "done" and tmr > 1.0:
			_po_shot("pen_done")
	if mode == "summary":
		if not _po_flags.has("sum_t"):
			_po_flags["sum_t"] = _po_test
		elif _po_test - float(_po_flags["sum_t"]) > 1.0:
			_po_shot("summary")
			if not _po_flags.has("hub"):
				_po_flags["hub"] = _po_test
				back_to_hub()
	if _po_flags.has("hub") and _po_test - float(_po_flags["hub"]) > 1.5:
		_po_shot("hub_board")
		print("PO TEST playoff state: done=%s summary=%s outcome=%s" % [club.playoff_done(), club._playoff_summary(), str(club.expected_outcome())])
		get_tree().quit()


var _tt := -1.0
var _tt_i := -1
var _tt_res := {}
# [kind, button, start distance from the carrier]
const TT := [["poke", JOY_BUTTON_A, 0.7], ["slide", JOY_BUTTON_X, 1.5], ["slide whiff", JOY_BUTTON_X, 7.0], ["poke whiff", JOY_BUTTON_A, 4.0], ["tap shot", JOY_BUTTON_B, 0.0], ["held shot 0.5s", JOY_BUTTON_B, 0.5]]
const TT_REPS := 20


func _tt_tick(delta: float) -> void:
	if state != "play" and _tt_i < 0:
		return
	_tt += delta
	var idx := _tt_i / TT_REPS if _tt_i >= 0 else -1
	if _tt_i < 0 or _tt > 1.6:
		if _tt_i >= 0:
			var r: Dictionary = _tt_res.get(TT[idx][0], {"won": 0, "n": 0, "stun": 0.0, "kind": "", "speed": 0.0})
			r["n"] += 1
			if ball.owner_player == home[5]:
				r["won"] += 1
			r["stun"] = maxf(float(r["stun"]), float(_tt_res.get("_stun", 0.0)))
			r["kind"] = home[5].tackle_kind
			r["speed"] = maxf(float(r["speed"]), float(_tt_res.get("_speed", 0.0)))
			_tt_res[TT[idx][0]] = r
		_tt_i += 1
		_tt_res["_stun"] = 0.0
		_tt_res["_speed"] = 0.0
		if _tt_i >= TT.size() * TT_REPS:
			for k in TT:
				var r2: Dictionary = _tt_res[k[0]]
				print("TT %-15s won ball %d/%d  tackle_kind %s  max time on the floor %.2fs  shot speed %.1f" % [k[0], r2["won"], r2["n"], r2["kind"], r2["stun"], r2["speed"]])
			get_tree().quit()
			return
		_tt = 0.0
		idx = _tt_i / TT_REPS
		var sc: Array = TT[idx]
		var flip := home[0].attack_dir
		for q in players:
			q.vel = Vector3.ZERO
			q.desired_move = Vector3.ZERO
			q.position = q.home_pos
			q.stun = 0.0
			q.tackle_timer = 0.0
			q.contact_time = 0.0
		pad_active = true
		var me: Player = home[5]
		if String(sc[0]).contains("shot"):
			me.position = Vector3(30.0 * flip, 0, 0)
			ball.reset_to(me.position)
			_give_ball(me)
		else:
			var carrier: Player = away[9]
			carrier.position = Vector3(0, 0, 0)
			ball.reset_to(carrier.position)
			_give_ball(carrier)
			carrier.protect = 0.0
			carrier.stun = 99.0   # stands still with the ball
			me.position = carrier.position + Vector3(-float(sc[2]) * flip, 0, 0)
			me.face_towards(carrier.position - me.position)
		controlled = me
		for q in players:
			if q != away[9] and q != me:
				q.stun = 99.0
		return
	var sc3: Array = TT[idx]
	var me2: Player = home[5]
	_tt_res["_stun"] = maxf(float(_tt_res["_stun"]), me2.stun if me2.stun < 50.0 else 0.0)
	if ball.owner_player == null:
		_tt_res["_speed"] = maxf(float(_tt_res["_speed"]), ball.vel.length())
	if _tt - delta < 0.2 and _tt >= 0.2:
		_pad_ev(int(sc3[1]), true)
		if not String(sc3[0]).begins_with("held"):
			_pad_ev(int(sc3[1]), false)
	if String(sc3[0]).begins_with("held") and _tt - delta < 0.2 + float(sc3[2]) and _tt >= 0.2 + float(sc3[2]):
		_pad_ev(int(sc3[1]), false)


var _pt2 := -1.0
var _pt2_i := -1
var _pt2_log := {}
# [name, buttons to press (time offsets), stick, ball carrier spot (attacking +x), carrier role]
const PT2 := [
	["A ground", [[0.0, JOY_BUTTON_A]], Vector2(1, 0), Vector3(-5, 0, 0), "CM", 20.0],
	["A A lofted", [[0.0, JOY_BUTTON_A], [0.08, JOY_BUTTON_A]], Vector2(1, 0), Vector3(-5, 0, 0), "CM", 20.0],
	["A A lofted short", [[0.0, JOY_BUTTON_A], [0.08, JOY_BUTTON_A]], Vector2(1, 0), Vector3(8, 0, 0), "CM", 20.0],
	["X lob", [[0.0, JOY_BUTTON_X]], Vector2(1, 0), Vector3(-25, 0, 0), "CB", 20.0],
	["X cross", [[0.0, JOY_BUTTON_X]], Vector2(0, -1), Vector3(38, 0, 28), "RW", 40.0],
	["Y through", [[0.0, JOY_BUTTON_Y]], Vector2(1, 0), Vector3(5, 0, 0), "CM", 25.0],
	["Y Y lofted through", [[0.0, JOY_BUTTON_Y], [0.08, JOY_BUTTON_Y]], Vector2(1, 0), Vector3(5, 0, 0), "CM", 25.0],
	["LB+Y over the top", [[0.0, -2], [0.1, JOY_BUTTON_Y]], Vector2(1, 0), Vector3(5, 0, 0), "CM", 25.0],
	["LB+B chip", [[0.0, -2], [0.1, -3], [0.55, -4]], Vector2(1, 0), Vector3(30, 0, 3), "ST", 0.0],
]


func _pt2_tick(delta: float) -> void:
	if state != "play" and _pt2_i < 0:
		return
	_pt2 += delta
	if _pt2_i < 0 or _pt2 > 4.0:
		if _pt2_i >= 0:
			var l: Dictionary = _pt2_log
			print("PT2 %-20s kick %s  max height %.2f  flight %.2fs  lands/first touch x=%.1f z=%.1f  next owner %s" % [PT2[_pt2_i][0],
				l.get("kick", "?"), l.get("maxh", 0.0), l.get("ft", 0.0), l.get("land", Vector3.ZERO).x, l.get("land", Vector3.ZERO).z, l.get("owner", "nobody")])
		_pt2_i += 1
		if _pt2_i >= PT2.size():
			print("PT2 done")
			get_tree().quit()
			return
		_pt2 = 0.0
		_pt2_log = {}
		var sc: Array = PT2[_pt2_i]
		# we attack +x for the test; opponents sent back to their own half, ours spread out
		var flip := home[0].attack_dir
		var carrier: Player = home[{"CB": 2, "CM": 5, "ST": 9, "RW": 10}[sc[4]]]
		for q in players:
			q.vel = Vector3.ZERO
			q.position = q.home_pos
			q.stun = 0.0
		for q in home:
			if q.role != "GK":
				q.position = q.home_pos + Vector3(float(sc[5]) * flip, 0, 0)
		for q in away:
			q.position = Vector3(q.home_pos.x, 0, q.home_pos.z)
		carrier.position = Vector3(sc[3].x * flip, 0, sc[3].z)
		for q in away:
			q.stun = 0.0 if "--pt2-live" in OS.get_cmdline_user_args() else 4.5   # frozen: measure the pass itself
			var off := Util.flat(q.position - carrier.position)
			if off.length() < 6.0:
				q.position = carrier.position + (off.normalized() if off.length() > 0.1 else Vector3(1, 0, 0)) * 6.0
		ball.reset_to(carrier.position)
		_give_ball(carrier)
		controlled = carrier
		pending_pass = {}
		pad_active = true
		_pad_ev(-1, true, JOY_AXIS_LEFT_X, sc[2].x * flip)
		_pad_ev(-1, true, JOY_AXIS_LEFT_Y, sc[2].y)
		return
	var sc2: Array = PT2[_pt2_i]
	for ev in sc2[1]:
		var at: float = 0.3 + float(ev[0])
		if _pt2 - delta < at and _pt2 >= at:
			match int(ev[1]):
				-2:
					_pad_ev(JOY_BUTTON_LEFT_SHOULDER, true)
				-3:
					_pad_ev(JOY_BUTTON_B, true)
				-4:
					_pad_ev(JOY_BUTTON_B, false)
					_pad_ev(JOY_BUTTON_LEFT_SHOULDER, false)
				_:
					_pad_ev(int(ev[1]), true)
					_pad_ev(int(ev[1]), false)
	if _pt2 > 0.9 and _pt2 < 1.2 and Input.is_joy_button_pressed(0, JOY_BUTTON_LEFT_SHOULDER):
		_pad_ev(JOY_BUTTON_LEFT_SHOULDER, false)
	if ball.owner_player == null and not _pt2_log.has("kick"):
		_pt2_log["kick"] = "%.2fs" % (_pt2 - 0.3)
		_pt2_log["t0"] = _pt2
		print("PT2   kicked by %s vel %s pos %s" % ["us" if ball.last_touch != null and ball.last_touch.team == 0 else "them", str(ball.vel.snapped(Vector3(0.1,0.1,0.1))), str(ball.position.snapped(Vector3(0.1,0.1,0.1)))])
	if _pt2_log.has("kick") and _pt2_i == 5 and int(_pt2 * 60) % 10 == 0 and "--pt2-trace" in OS.get_cmdline_user_args():
		print("PT2     t=%.2f ball %s vel %s ST %s target %s state %s" % [_pt2 - float(_pt2_log["t0"]), str(ball.position.snapped(Vector3(0.1,0.1,0.1))), str(ball.vel.snapped(Vector3(0.1,0.1,0.1))), "%s v=%.1f dm=%s spr=%s hum=%s ctl=%s" % [str(home[9].position.snapped(Vector3(0.1,0.1,0.1))), home[9].vel.length(), str(home[9].desired_move.snapped(Vector3(0.1,0.1,0.1))), home[9].wants_sprint, home[9].is_human, home.find(controlled)], str(ball.pass_target == home[9]), state])
	if _pt2_log.has("kick") and not _pt2_log.has("owner"):
		_pt2_log["maxh"] = maxf(float(_pt2_log.get("maxh", 0.0)), ball.position.y)
		if ball.position.y > 0.3:
			_pt2_log["air"] = true
		if (_pt2_log.get("air", false) and ball.position.y <= Ball.RADIUS + 0.02 and not _pt2_log.has("land")) or ball.owner_player != null:
			if not _pt2_log.has("land"):
				_pt2_log["land"] = ball.position * Vector3(home[0].attack_dir, 1, 1)
				_pt2_log["ft"] = _pt2 - float(_pt2_log["t0"])
		if ball.owner_player != null:
			var o := ball.owner_player
			_pt2_log["owner"] = "%s #%d" % ["us" if o.team == 0 else "THEM", team_list(o.team).find(o)]
			if not _pt2_log.has("land"):
				_pt2_log["land"] = ball.position * Vector3(home[0].attack_dir, 1, 1)


func _pass_test() -> void:
	# dev: lead passes to a running receiver; prints how close the ball gets and how fast it is then
	var passer := home[5]
	var recv := home[6]
	var cases := [[Vector3(15, 0, 10), Vector3(0, 0, -6)], [Vector3(25, 0, 0), Vector3(6, 0, 0)],
		[Vector3(8, 0, -12), Vector3(-4, 0, -4)], [Vector3(35, 0, 15), Vector3(5, 0, -3)], [Vector3(10, 0, 0), Vector3(0, 0, 0)]]
	for c in cases:
		var rp: Vector3 = c[0]
		var rv: Vector3 = c[1]
		passer.position = Vector3.ZERO
		recv.position = rp
		recv.vel = rv
		ball.reset_to(passer.position)
		ball.owner_player = passer
		passer.pass_to(recv)
		var best := INF
		var spd_at := 0.0
		for i in 300:
			recv.position += rv * (1.0 / 60.0)
			ball.step(1.0 / 60.0)
			var d := Util.flat_dist(ball.position, recv.position)
			if d < best:
				best = d
				spd_at = ball.flat_speed()
		print("PASS to %s running %s: closest %.2f m, ball speed there %.1f m/s" % [str(rp), str(rv), best, spd_at])
	get_tree().quit()


# ================================================================== hub / club flow

func _enter_hub() -> void:
	mode = "hub"
	hud_layer.visible = false
	hub.hide_summary()
	hub.show_hub(true)
	for p in players:
		p.visible = false
	ball.visible = false
	name_label.visible = false
	grounds.clear_crowd()
	var done := club.complete_builds()
	if not done.is_empty():
		club.save()
		toast("Construction finished: %d section(s)" % done.size())
	grounds.use_home()
	if sfx != null:
		sfx.set_murmur(false)
	_hub_camera()


## The next league match (GDD calendar). Kept under the old name: dev flags call it too.
func start_friendly() -> void:
	var fx: Dictionary = club.league.next_fixture()
	match_ctx = {}
	pens = {}
	var opp: Dictionary
	if fx.is_empty():
		# season over: your next play-off leg, if you're in them (otherwise the hub offers the next season)
		fx = club.playoff_fixture()
		if fx.is_empty():
			return
		opp = fx["opponent"]
		match_ctx = fx.duplicate()
		match_ctx["kind"] = "playoff"
	else:
		opp = club.league.teams[fx["opponent"]]
	opponent_name = opp["name"]
	match_home = fx["home"] or "--crowd-max" in OS.get_cmdline_user_args() or "--stands-match" in OS.get_cmdline_user_args()
	match_opp_strength = float(opp["str"])
	placing_item = ""
	grounds.show_markers(false)
	_spawn_teams()
	ball.visible = true
	score = [0, 0]
	half = 1
	time_left = SettingsScript.half_seconds()
	for k in stats:
		stats[k] = [0, 0]
	if match_home:
		grounds.use_home()
		grounds.spawn_crowd(club.fans)
	else:
		# seeded away ground per club (block 3); some of your fans travel along
		var home_fans := grounds.use_away(opponent_name, match_opp_strength)
		grounds.spawn_crowd(home_fans, int(round(club.fans * AWAY_TRAVEL_SHARE)))
	sfx.crowd_level = clampf(club.fans / 100.0, 0.05, 1.0) if match_home else clampf(club.fans * AWAY_TRAVEL_SHARE / 100.0, 0.03, 0.4)
	sfx.set_murmur(true)
	mode = "match"
	hub.show_hub(false)
	hub.hide_summary()
	hud_layer.visible = true
	_start_kickoff(first_kickoff_team)
	_update_hint()


func back_to_hub() -> void:
	paused = false
	Engine.time_scale = 1.0
	_enter_hub()


## Dev cheat: the next league match ends with this score without playing it.
func cheat_result(gf: int, ga: int) -> void:
	var fx: Dictionary = club.league.next_fixture()
	if fx.is_empty():
		var pf := club.playoff_fixture()
		if pf.is_empty():
			return
		var ps := club.apply_match(gf, ga, 3, pf["home"], pf["opponent"]["name"])
		var won_after = null
		if pf.has("first_leg") and int(pf["first_leg"][0]) + gf == int(pf["first_leg"][1]) + ga:
			won_after = randf() < 0.5   # cheat: a level tie goes to a coin flip
		club.record_playoff_leg(pf["tie"], gf, ga, won_after, "pens" if won_after != null else "")
		ps["playoff"] = _playoff_info(pf, gf, ga, won_after, [], false)
		ps["season_over"] = true
		club.save()
		mode = "summary"
		hub.show_hub(false)
		hub.show_summary(ps, pf["opponent"]["name"])
		return
	var opp: Dictionary = club.league.teams[fx["opponent"]]
	var summary := club.apply_match(gf, ga, 3, fx["home"], opp["name"])
	summary["round_results"] = club.league.play_round(gf, ga)
	summary["position"] = club.league.position_of(0)
	summary["season_over"] = club.league.season_over()
	club.end_season_money()
	club.save()
	mode = "summary"
	hub.show_hub(false)
	hub.show_summary(summary, opp["name"])


var _cheat_away_idx := 0


## Dev cheat: show the next club's away ground in the hub (cycles through the league).
func cheat_view_away() -> String:
	var teams: Array = club.league.teams
	_cheat_away_idx = _cheat_away_idx % (teams.size() - 1) + 1
	var t: Dictionary = teams[_cheat_away_idx]
	var fans := grounds.use_away(t["name"], float(t["str"]))
	grounds.spawn_crowd(fans)
	return t["name"]


## Dev cheat (fps test): open bleachers, 7 rows, on every section, finished now.
func cheat_max_stadium() -> void:
	club.builds.clear()
	for sec in Grounds.section_count():
		club.sections[str(sec)] = {"stage": "bleachers", "rows": ClubState.BLEACHER_ROWS[-1]}
		for k in ClubState.SPOTS_PER_SECTION:
			club.slots.erase(str(sec * ClubState.SPOTS_PER_SECTION + k))
	grounds.rebuild_furniture()


func cheat_view_home() -> void:
	grounds.clear_crowd()
	grounds.use_home()


func next_season() -> void:
	if not club.playoff_done():
		return   # your play-offs come first
	var rep := club.start_next_season()
	print("SEASON CHANGE ", rep)
	club.complete_builds()   # the 10-week off-season passes
	club.save()
	grounds.rebuild_furniture()
	hub.refresh()


func new_game() -> void:
	ClubState.delete_save()
	club = ClubState.new_game()
	grounds.state = club
	grounds.rebuild_furniture()
	hub.last_seated = 0
	hub.set_club(club)


func begin_placing(item: String) -> void:
	if club.money < club.price_of(item):
		return
	placing_item = item
	grounds.show_markers(true, item)


func _cancel_placing() -> void:
	placing_item = ""
	hover_slot = -1
	grounds.show_markers(false)
	hub.update_preview("", -1, Vector2.ZERO)
	hub.refresh()


# hub camera (Marcel, 2026-11-07: free look between matches + reset).
# WASD/arrows pan (relative to the view), wheel zoom, Q/E rotate, R/F tilt,
# hold right or middle mouse and drag to orbit + tilt, C or the button resets. All tunable.
const HUB_DEFAULT_FOCUS := Vector3(8.0, 0, -HALF_W - 2.0)
const HUB_DEFAULT_PITCH := 45.0     # degrees above the ground
const HUB_DIST := 36.8              # camera distance at zoom 1
const HUB_PITCH_MIN := 8.0
const HUB_PITCH_MAX := 85.0
const HUB_ZOOM_MIN := 0.12
const HUB_ZOOM_MAX := 3.0
const HUB_ROTATE_SPEED := 1.6       # rad/s with Q/E
const HUB_TILT_SPEED := 40.0        # deg/s with R/F
const HUB_DRAG_SENS := 0.006        # rad per pixel
const HUB_PAN_LIMIT := 45.0         # metres beyond the pitch
var hub_focus := HUB_DEFAULT_FOCUS
var hub_zoom := 1.0
var hub_yaw := 0.0   # orbit angle around the focus point
var hub_pitch := HUB_DEFAULT_PITCH
var _hub_drag := false
var _hub_drag_moved := 0.0


func reset_hub_camera() -> void:
	hub_focus = HUB_DEFAULT_FOCUS
	hub_zoom = 1.0
	hub_yaw = 0.0
	hub_pitch = HUB_DEFAULT_PITCH


func _hub_camera() -> void:
	_set_stand_clip(false)
	var p := deg_to_rad(hub_pitch)
	var offset := Vector3(0, sin(p), cos(p)) * HUB_DIST * hub_zoom
	camera.position = hub_focus + offset.rotated(Vector3.UP, hub_yaw)
	camera.position.y = maxf(camera.position.y, 1.2)
	camera.look_at(hub_focus + Vector3(0, 0.5 if hub_zoom < 0.4 else 0.0, 0), Vector3.UP)


func _hub_process(delta: float) -> void:
	var pan := Vector3.ZERO
	if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
		pan.z -= 1.0
	if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
		pan.z += 1.0
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
		pan.x -= 1.0
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
		pan.x += 1.0
	if pan != Vector3.ZERO:
		hub_focus += pan.normalized().rotated(Vector3.UP, hub_yaw) * 30.0 * maxf(hub_zoom, 0.3) * delta * SettingsScript.camera_mult()
		hub_focus.x = clampf(hub_focus.x, -HALF_L - HUB_PAN_LIMIT, HALF_L + HUB_PAN_LIMIT)
		hub_focus.z = clampf(hub_focus.z, -HALF_W - HUB_PAN_LIMIT, HALF_W + HUB_PAN_LIMIT)
	if Input.is_key_pressed(KEY_Q):
		hub_yaw += HUB_ROTATE_SPEED * delta * SettingsScript.camera_mult()
	if Input.is_key_pressed(KEY_E):
		hub_yaw -= HUB_ROTATE_SPEED * delta * SettingsScript.camera_mult()
	if Input.is_key_pressed(KEY_R):
		hub_pitch = clampf(hub_pitch + HUB_TILT_SPEED * delta, HUB_PITCH_MIN, HUB_PITCH_MAX)
	if Input.is_key_pressed(KEY_F):
		hub_pitch = clampf(hub_pitch - HUB_TILT_SPEED * delta, HUB_PITCH_MIN, HUB_PITCH_MAX)
	_hub_camera()
	if placing_item == "":
		return
	var p := _mouse_ground_point()
	hover_slot = grounds.nearest_free_slot(p, placing_item, 3.0)
	grounds.show_markers(true, placing_item, hover_slot)
	var anchor := Vector3.ZERO
	if hover_slot >= 0:
		anchor = Grounds.section_point(hover_slot, 0.0, Grounds.SEAT_OFFSET) if placing_item in ClubState.SECTION_ITEMS else Grounds.slot_position(hover_slot)
	hub.update_preview(placing_item, hover_slot, camera.unproject_position(anchor + Vector3(0, 1.0, 0)))


func _hub_click() -> void:
	if placing_item == "" or hover_slot < 0:
		return
	if club.place(placing_item, hover_slot):
		grounds.rebuild_furniture()
		club.save()
	if placing_item == "hardcore":            # keep toggling sections until Esc / right click
		hub.refresh()
		return
	_cancel_placing()


func _hub_test() -> void:
	# dev: exercise the club flow without a mouse
	print("HUB TEST start: money %d fans %d squad %d" % [club.money, club.fans, club.squad.size()])
	while club.squad.size() < ClubState.SQUAD_SIZE:
		club.recruit(0)
	club.money = 200
	print("placed bench: ", club.place("bench", 3), " chairs x5 on spot 25: ", [club.place("chair", 25), club.place("chair", 25), club.place("chair", 25), club.place("chair", 25), club.place("chair", 25)], " bench on chairs: ", club.place("bench", 25), " seats ", club.seats(), " slots ", club.slots)
	print("spots %d sections %d" % [Grounds.slot_count(), Grounds.section_count()])
	if "--fill-test" in OS.get_cmdline_user_args():
		# dev: fill a mix of sections so the layout can be screenshotted
		club.money = 99999
		for sec in [2, 3, 5, 6, 12, 20, 25]:
			for k in ClubState.SPOTS_PER_SECTION:
				var spot: int = sec * ClubState.SPOTS_PER_SECTION + k
				if (sec + k) % 2 == 0:
					club.place("bench", spot)
				else:
					for c in 4:
						club.place("chair", spot)
		club.sections["7"] = {"stage": "bleachers", "rows": 3}
		club.sections["13"] = {"stage": "bleachers", "rows": 7}
		club.sections["14"] = {"stage": "bleachers", "rows": 7}
		club.sections["15"] = {"stage": "bleachers", "rows": 3}
		club.sections["6"] = {"stage": "bleachers", "rows": 5}
		club.place("bleachers", 1)
		grounds.rebuild_furniture()
		print("FILL seats ", club.seats())
	var legacy := ClubState.from_dict({"version": 1, "money": 999, "slots": {"7": "chair"}})
	print("v1 save -> new game: money ", legacy.money, " slots ", legacy.slots)
	grounds.rebuild_furniture()
	var summary := club.apply_match(2, 1, 5)
	print("SUMMARY ", summary)
	var d := club.to_dict()
	var back := ClubState.from_dict(JSON.parse_string(JSON.stringify(d)))
	print("ROUNDTRIP money %d fans %d slots %s squad %d" % [back.money, back.fans, str(back.slots), back.squad.size()])
	grounds.spawn_crowd(maxi(club.fans + 10, club.seats() + 30))
	_league_test()
	_build_test()
	if "--cheats" in OS.get_cmdline_user_args():
		print("CHEAT away: ", cheat_view_away(), " / ", cheat_view_away(), " spots ", grounds.active_slots.size())
		cheat_view_home()
		var r0 := club.league.round_idx
		cheat_result(3, 0)
		print("CHEAT result: round %d -> %d, pos %d, mode %s" % [r0, club.league.round_idx, club.league.position_of(0), mode])
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--sim-rounds="):
			# dev: play N league rounds with random scores (to see the table / season end in the hub)
			for i in int(arg.trim_prefix("--sim-rounds=")):
				if club.league.season_over():
					break
				var fx: Dictionary = club.league.next_fixture()
				var res := club.apply_match(randi_range(0, 3), randi_range(0, 2), 3, fx["home"], club.league.teams[fx["opponent"]]["name"])
				club.league.play_round(res["goals_for"], res["goals_against"])
				club.end_season_money()
			hub.refresh()
			print("SIM week %d round %d pos %d" % [club.league.current_week(), club.league.round_idx, club.league.position_of(0)])
	var shown := 0
	var flags := 0
	for c in grounds.crowds:
		shown += c.fan_count()
		flags += c.flag_count()
	print("CROWD fans drawn: %d (flags %d), seats %d" % [shown, flags, club.seats()])


# ================================================================== loop

func _physics_process(delta: float) -> void:
	if mode != "match":
		if mode == "hub" or mode == "freecam":
			_hub_process(delta)
		_debug_screenshot(delta)
		return
	if _pad_test >= 0.0:
		_pad_test_tick(delta)
	if _pt2 >= 0.0:
		_pt2_tick(delta)
	if _tt >= 0.0:
		_tt_tick(delta)
	match state:
		"kickoff":
			state_timer -= delta
			if state_timer <= 0.0:
				state = "play"
				msg_label.text = ""
				sfx.whistle()
		"goal":
			state_timer -= delta
			if state_timer <= 0.0:
				if time_left <= 0.0:
					_end_of_half()
				else:
					_start_kickoff(_conceding_team)
		"halftime":
			state_timer -= delta
			if state_timer <= 0.0:
				_second_half()
		"restart":
			state_timer -= delta
			if state_timer <= 0.0:
				state = "play"
		"play":
			if autoplay and "--trace" in OS.get_cmdline_user_args() and int(time_left * 60.0) % 300 == 0:
				var h := ball.owner_player
				print("[%s] ball %s v=%.1f holder=%s" % [_clock_text(), str(ball.position.snapped(Vector3(0.1,0.1,0.1))), ball.flat_speed(), ("none" if h == null else "%s t%d %s" % [h.role, h.team, str(h.position.snapped(Vector3(0.1,0.1,0.1)))])])
			if autoplay and "--restart-test" in OS.get_cmdline_user_args():
				_restart_test_tick(delta)
			time_left -= delta
			if time_left <= 0.0:
				time_left = 0.0
				_end_of_half()
		"shottest":
			_shot_test_step(delta)
		"penalties":
			_pen_tick(delta)

	if state == "play" or state == "restart":
		_update_human(delta)
		for p in players:
			p.is_human = p == controlled and not autoplay
		_assign_marks(0)
		_assign_marks(1)
		for p in players:
			if not p.is_human:
				p.ai_update(delta)
		for p in players:
			p.step(delta)
		_separate_players()
		var sp := _current_set_piece()
		if sp != null:
			_enforce_set_piece_distance(sp.position, sp.team, sp.restart_kind)
		if state == "play":
			_resolve_possession(delta)
			ball.step(delta)
			_check_goal()
			if state == "play":
				_check_out()
		else:
			ball.step(delta)
	elif state == "goal":
		for p in players:
			p.desired_move = Vector3.ZERO
			p.step(delta)
		ball.step(delta)

	toast_timer = maxf(0.0, toast_timer - delta)
	if _bunch_test:
		_bunch_check(delta)
	_update_camera(delta)
	_update_hud()
	_update_indicators()
	_debug_screenshot(delta)


# dev helper: `-- --autoplay --shot=/path/shot.png` saves a screenshot after a few seconds and quits
# (`--shot-after=S` waits S seconds, `--zoom=Z` forces the match zoom, e.g. 0.35 for a close look)
var _shot_timer := 0.0


func _debug_screenshot(delta: float) -> void:
	var wait := 4.0
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--shot-after="):
			wait = float(arg.substr(13))
		elif arg.begins_with("--zoom="):
			match_zoom = float(arg.substr(7))
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--shot="):
			_shot_timer += delta
			if _shot_timer > wait:
				var img := get_viewport().get_texture().get_image()
				img.save_png(arg.substr(7))
				get_tree().quit()
			return


# dev helper: `-- --ui-demo --shot=/path.png` fakes a human charging a shot, to screenshot the aim UI
var _ui_demo := false
var _pad_test := -1.0
var _pad_log := {}


func _pad_ev(button := -1, pressed := true, axis := -1, value := 0.0) -> void:
	var e: InputEvent
	if button >= 0:
		var b := InputEventJoypadButton.new()
		b.button_index = button
		b.pressed = pressed
		e = b
	else:
		var m := InputEventJoypadMotion.new()
		m.axis = axis
		m.axis_value = value
		e = m
	e.device = 0
	Input.parse_input_event(e)


func _pad_test_tick(delta: float) -> void:
	var t0 := _pad_test
	_pad_test += delta
	var t := _pad_test
	var at := func(x: float) -> bool: return t0 < x and t >= x
	if at.call(0.5):
		_pad_ev(-1, true, JOY_AXIS_LEFT_X, 1.0)
	if at.call(3.5):
		print("PADTEST pad_active ", pad_active, " move ", controlled.desired_move if controlled else null, " sprint ", controlled.wants_sprint if controlled else null, " hint ", hint_label.text.left(20))
		_pad_ev(-1, true, JOY_AXIS_LEFT_X, 0.35)
	if at.call(4.0):
		print("PADTEST half tilt sprint ", controlled.wants_sprint)
		_pad_ev(-1, true, JOY_AXIS_LEFT_X, 0.0)
		_pad_ev(-1, true, JOY_AXIS_LEFT_Y, -1.0)
	var fr := Engine.get_process_frames()
	if t >= 4.5 and not _pad_log.has("passed") and controlled != null and controlled.has_ball() and state == "play":
		print("PADTEST aim dir ", Util.flat(aim_point - controlled.position).normalized().snapped(Vector3.ONE * 0.01), " has_ball ", controlled.has_ball())
		_pad_log["passer"] = controlled
		_pad_ev(JOY_BUTTON_A, true)
		_pad_ev(JOY_BUTTON_A, false)
		_pad_log["passed"] = t
	if _pad_log.has("passed") and not _pad_log.has("checked") and t >= float(_pad_log["passed"]) + 0.3:
		_pad_log["checked"] = true
		print("PADTEST 0.3 s after A: passer still has ball ", (_pad_log["passer"] as Player).has_ball(), " ball speed ", snappedf(ball.vel.length(), 0.1))
	if t >= 14.0 and not _pad_log.has("start1"):
		_pad_log["start1"] = fr
		_pad_ev(JOY_BUTTON_START, true)
		_pad_ev(JOY_BUTTON_START, false)
	elif _pad_log.has("start1") and not _pad_log.has("start2") and fr >= int(_pad_log["start1"]) + 3:
		print("PADTEST paused ", paused, " time_scale ", Engine.time_scale, " msg ", msg_label.text)
		_pad_log["start2"] = fr
		_pad_ev(JOY_BUTTON_START, true)
		_pad_ev(JOY_BUTTON_START, false)
	elif _pad_log.has("start2") and not _pad_log.has("kb") and fr >= int(_pad_log["start2"]) + 3:
		print("PADTEST resumed ", not paused, " time_scale ", Engine.time_scale)
		_pad_log["kb"] = fr
		_pad_ev(-1, true, JOY_AXIS_LEFT_Y, 0.0)
		var k := InputEventKey.new()
		k.keycode = KEY_W
		k.pressed = true
		Input.parse_input_event(k)
	elif _pad_log.has("kb") and fr >= int(_pad_log["kb"]) + 3:
		print("PADTEST keyboard back: pad_active ", pad_active, " hint ", hint_label.text.left(20), " (passed at ", _pad_log.get("passed", "never"), ")")
		get_tree().quit()


func _ui_demo_tick() -> void:
	aim_point = Vector3(HALF_L, 0, 1.6) if not ("--ui-demo-still" in OS.get_cmdline_user_args()) else aim_point
	if not controlled.has_ball():
		controlled.position = Vector3(-10, 0, -24)
		_give_ball(controlled)
		toast("SAVE!")
	charging = true
	charge = 0.65


func _crowd(kind: String) -> void:
	if grounds != null:
		grounds.react(kind)
	if sfx != null:
		sfx.crowd(kind)


func toast(text: String) -> void:
	toast_label.text = text
	toast_timer = 1.1


# ================================================================== match flow

func _start_kickoff(kicking_team: int) -> void:
	state = "kickoff"
	state_timer = 1.2
	msg_label.text = "READY"
	charging = false
	ball.reset_to(Vector3.ZERO)
	for p in players:
		p.position = p.home_pos
		p.vel = Vector3.ZERO
		p.desired_move = Vector3.ZERO
		p.stun = 0.0
		p.tackle_timer = 0.0
		p.touch_cooldown = 0.0
		p.contact_time = 0.0
		p.restart_kind = ""
		p.face_towards(Vector3(p.attack_dir, 0, 0))
	# the kicking team's most advanced outfielder stands on the ball
	var list := team_list(kicking_team)
	var taker: Player = null
	for p in list:
		if p.role == "GK":
			continue
		if taker == null or (p.home_pos.x * p.attack_dir) > (taker.home_pos.x * taker.attack_dir):
			taker = p
	if taker != null:
		taker.position = Vector3(-taker.attack_dir * 0.8, 0, 0)
	if not autoplay:
		controlled = _nearest_to_ball(home, true)


func _check_goal() -> void:
	var p := ball.position
	if absf(p.z) > GOAL_W * 0.5 or p.y > GOAL_H:
		return
	if p.x > HALF_L + Ball.RADIUS:
		_goal(_team_attacking(1.0))
	elif p.x < -HALF_L - Ball.RADIUS:
		_goal(_team_attacking(-1.0))


func _team_attacking(side: float) -> int:
	return 0 if home[0].attack_dir == side else 1


## Ball fully over a line (not a goal): award throw-in / corner / goal kick.
func _check_out() -> void:
	if ball.owner_player != null and ball.owner_player.restart_kind != "":
		return   # ball is being held for a set piece
	var p := ball.position
	var last := ball.last_touch
	var last_team := last.team if last != null else 0
	if absf(p.z) > HALF_W + Ball.RADIUS:
		var spot := Vector3(clampf(p.x, -HALF_L + 1.0, HALF_L - 1.0), 0, signf(p.z) * HALF_W)
		_award_restart("throw-in", 1 - last_team, spot)
	elif absf(p.x) > HALF_L + Ball.RADIUS:
		var side := signf(p.x)
		var attackers := _team_attacking(side)
		var defenders := 1 - attackers
		var zs := signf(p.z) if absf(p.z) > 0.01 else 1.0
		if last_team == defenders:
			_award_restart("corner", attackers, Vector3(side * (HALF_L - 0.3), 0, zs * (HALF_W - 0.3)))
		else:
			_award_restart("goal kick", defenders, Vector3(side * (HALF_L - GOAL_AREA_DEPTH), 0, zs * 4.0))


func _award_restart(kind: String, t: int, spot: Vector3) -> void:
	stats_add(kind, t)
	state = "restart"
	state_timer = 0.8
	charging = false
	ball.reset_to(spot)
	var taker: Player = null
	if kind == "goal kick":
		taker = team_list(t)[0]
	else:
		var best_d := INF
		for p in team_list(t):
			if p.role == "GK":
				continue
			var d := Util.flat_dist(p.position, spot)
			if d < best_d:
				best_d = d
				taker = p
	for p in players:
		p.restart_kind = ""
		p.tackle_timer = 0.0
	_enforce_set_piece_distance(spot, t, kind)
	taker.position = spot
	taker.vel = Vector3.ZERO
	if t == 0 and not autoplay:
		controlled = taker
	taker.face_towards(Vector3(-spot.x * 0.3, 0, -spot.z))
	_give_ball(taker)
	taker.restart_kind = kind
	taker.protect = 999.0
	taker.has_ball_time = 0.0
	toast(kind.to_upper())
	sfx.whistle()


## Dead ball: opponents stay back (9.15 m, or a few metres at a throw-in) until it's taken.
func _enforce_set_piece_distance(spot: Vector3, taking_team: int, kind: String) -> void:
	var r := THROW_IN_DISTANCE if kind == "throw-in" else 9.15
	for p in team_list(1 - taking_team):
		var away_dir := Util.flat(p.position - spot)
		if away_dir.length() < r:
			if away_dir.length() < 0.1:
				away_dir = Vector3(-p.attack_dir, 0, 0)
			p.position = spot + away_dir.normalized() * r
			p.vel = Vector3.ZERO


func _current_set_piece() -> Player:
	var h := ball.owner_player
	return h if h != null and h.restart_kind != "" else null


func stats_add(kind: String, t: int) -> void:
	var key := kind + "s" if kind != "free kick" else "offside"
	if kind == "goal kick":
		key = "goal kicks"
	if stats.has(key):
		stats[key][t] += 1


# dev: `-- --autoplay --restart-test` forces every set piece in turn
var _rt_timer := 3.0
var _rt_i := 0


func _restart_test_tick(delta: float) -> void:
	_rt_timer -= delta
	if _rt_timer > 0.0:
		return
	_rt_timer = 7.0
	var kinds := ["corner", "throw-in", "goal kick", "offside"]
	var kind: String = kinds[_rt_i % kinds.size()]
	var t := _rt_i % 2
	_rt_i += 1
	var side := team_list(t)[0].attack_dir
	print("[%s] forcing %s for team %d" % [_clock_text(), kind, t])
	match kind:
		"corner":
			_award_restart("corner", t, Vector3(side * (HALF_L - 0.3), 0, HALF_W - 0.3))
		"throw-in":
			_award_restart("throw-in", t, Vector3(randf_range(-30, 30), 0, -HALF_W))
		"goal kick":
			_award_restart("goal kick", t, Vector3(-side * (HALF_L - GOAL_AREA_DEPTH), 0, 4.0))
		"offside":
			_call_offside(team_list(1 - t)[10])


# ---- offside ------------------------------------------------------------------

## x of the second-last defender of the team defending against `attacking_team` (keeper counts).
func offside_line(attacking_team: int) -> float:
	var dir := team_list(attacking_team)[0].attack_dir
	var xs: Array[float] = []
	for o in team_list(1 - attacking_team):
		xs.append(o.position.x * dir)
	xs.sort()
	var second_last := xs[xs.size() - 2] if xs.size() >= 2 else 0.0
	return maxf(second_last, 0.0) * dir   # can't be offside in your own half


func in_offside_position(p: Player, ball_x: float) -> bool:
	var dir := p.attack_dir
	if p.position.x * dir <= 0.0:
		return false
	if (p.position.x - ball_x) * dir <= 0.0:
		return false
	return (p.position.x - offside_line(p.team)) * dir > 0.0


## Called by the ball whenever someone plays it: remember which teammates were offside.
func mark_offside(kicker: Player) -> void:
	ball.offside_players.clear()
	for m in team_list(kicker.team):
		if m != kicker and in_offside_position(m, kicker.position.x):
			ball.offside_players.append(m)


func _call_offside(p: Player) -> void:
	stats["offside"][p.team] += 1
	_award_restart("free kick", 1 - p.team, Vector3(clampf(p.position.x, -HALF_L + 1, HALF_L - 1), 0, clampf(p.position.z, -HALF_W + 1, HALF_W - 1)))
	toast("OFFSIDE!")
	_crowd("offside")


# ---- halves -------------------------------------------------------------------

func _end_of_half() -> void:
	var to_extra := half == 2 and _needs_extra_time()
	if half == 1 or half == 3 or to_extra:
		sfx.whistle_times(2)
		state = "halftime"
		state_timer = 2.5
		var what := "HALF TIME"
		if to_extra:
			what = "EXTRA TIME"
		elif half == 3:
			what = "EXTRA TIME, HALF TIME"
		msg_label.text = "%s  %d - %d" % [what, score[0], score[1]]
		ball.owner_player = null
		charging = false
		print("%s %d - %d" % [what, score[0], score[1]])
	elif half == 4 and _needs_extra_time():
		sfx.whistle_times(3)
		_start_shootout()
	else:
		sfx.whistle_times(3)
		_full_time()


var _quick := false


## Next half: 2nd half, or extra time (two halves of a third of a normal half, GDD §6).
func _second_half() -> void:
	half += 1
	var hs := SettingsScript.half_seconds()
	time_left = 3.0 if _quick else (hs if half <= 2 else hs / 3.0)
	# switch sides at half time and at the break in extra time (not before extra time)
	if half != 3:
		for p in players:
			p.attack_dir = -p.attack_dir
			p.home_pos = Vector3(-p.home_pos.x, 0, -p.home_pos.z)
	_start_kickoff(1 - first_kickoff_team if half % 2 == 0 else first_kickoff_team)


func _goal(scoring_team: int) -> void:
	score[scoring_team] += 1
	_conceding_team = 1 - scoring_team
	state = "goal"
	state_timer = 2.5
	sfx.whistle()
	ball.owner_player = null
	charging = false
	var scorer := ball.last_touch
	var own_goal := scorer != null and scorer.team != scoring_team
	msg_label.text = "OWN GOAL!" if own_goal else "GOAL!"
	if not own_goal and scorer != null and scorer.display_name != "":
		msg_label.text = "GOAL!\n%s" % scorer.display_name
	if grounds != null:
		_crowd("goal_for" if scoring_team == 0 else "goal_against")
	for p in players:
		if p.team == scoring_team:
			p.celebrate(state_timer)
	print("[%s] GOAL team %d  -> %d - %d" % [_clock_text(), scoring_team, score[0], score[1]])


func _full_time() -> void:
	state = "fulltime"
	msg_label.text = "FULL TIME  %d - %d" % [score[0], score[1]]
	print("FULL TIME %d - %d   %s" % [score[0], score[1], str(stats)])
	if _bunch_test:
		print("BUNCH summary: %d hits in %d samples" % [_bunch_hits, _bunch_samples])
	if autoplay:
		get_tree().quit()
		return
	# friendly done: pay, grow, autosave, show summary
	var ent: int = score[0] + score[1] + stats["saves"][0] + stats["saves"][1] + stats["steals"][0] + stats["steals"][1]
	var summary := club.apply_match(score[0], score[1], ent, match_home, opponent_name)
	if match_ctx.get("kind", "") == "playoff":
		var won_after = null
		var how := ""
		if not pens.is_empty():
			won_after = int(pens["winner"]) == 0
			how = "pens"
		elif half >= 3:
			how = "et"
		club.record_playoff_leg(match_ctx["tie"], score[0], score[1], won_after, how)
		summary["playoff"] = _playoff_info(match_ctx, score[0], score[1], won_after,
			[] if pens.is_empty() else pens["goals"], half >= 3)
		summary["season_over"] = true
		club.save()
		mode = "summary"
		name_label.visible = false
		hub.show_summary(summary, opponent_name)
		return
	summary["round_results"] = club.league.play_round(score[0], score[1])
	summary["position"] = club.league.position_of(0)
	summary["season_over"] = club.league.season_over()
	club.end_season_money()
	club.save()
	print("FRIENDLY DONE -> summary ", summary, " saved to ", ProjectSettings.globalize_path(ClubState.SAVE_PATH))
	mode = "summary"
	name_label.visible = false
	hub.show_summary(summary, opponent_name)


func _restart() -> void:
	score = [0, 0]
	if half == 2 or half == 3:
		for p in players:
			p.attack_dir = -p.attack_dir
			p.home_pos = Vector3(-p.home_pos.x, 0, -p.home_pos.z)
	half = 1
	time_left = SettingsScript.half_seconds()
	_start_kickoff(first_kickoff_team)


# ================================================================== play-offs: extra time and penalties (GDD §6)

const PEN_SPOT := 11.0           # penalty spot, metres from the goal line
const PEN_DIVE_Z := 2.3          # a diving keeper ends up this far from the middle
const PEN_REACH_DIVE := 1.15     # ...and reaches this far from there (the corners stay out of reach)
const PEN_REACH_STAY := 0.95     # a keeper who stays in the middle
const PEN_ERROR := 1.3           # penalty shots are a bit less accurate than open-play shots, more so with power
var match_ctx := {}              # {} = league match; play-off leg: {kind "playoff", tie, leg, round, home, opponent, first_leg [us, them]}
var pens := {}                   # penalty shootout state ({} = none)


## Second leg level on aggregate (after 90 minutes, or after extra time)?
func _needs_extra_time() -> bool:
	if match_ctx.get("kind", "") != "playoff" or not match_ctx.has("first_leg"):
		return false
	var fl: Array = match_ctx["first_leg"]
	return int(fl[0]) + score[0] == int(fl[1]) + score[1]


func _pen_height(power: float) -> float:
	return lerpf(0.3, 2.1, power)


## Shootout: alternate kicks at the far goal, best of five, then sudden death. You aim and shoot your
## own kicks (hold RMB / B for power, release); keepers on both sides guess at random (Marcel: keeping is chance).
func _start_shootout() -> void:
	state = "penalties"
	charging = false
	ball.owner_player = null
	var spots := {}
	var order := [[], []]
	for t in 2:
		var list := team_list(t)
		var outs: Array = []
		for i in list.size():
			if list[i].role != "GK":
				outs.append(i)
		# most attacking players take the first kicks
		outs.sort_custom(func(a: int, b: int) -> bool:
			return list[a].home_pos.x * list[a].attack_dir > list[b].home_pos.x * list[b].attack_dir)
		order[t] = outs
	var i := 0
	for p in players:
		p.vel = Vector3.ZERO
		p.desired_move = Vector3.ZERO
		p.tackle_timer = 0.0
		p.restart_kind = ""
		p.stun = 0.0
		if p.role == "GK":
			continue
		# the rest wait arm in arm in the centre circle (well, near enough)
		var a := lerpf(-1.25, 1.25, float(i) / 19.0)
		p.position = Vector3(cos(a) * 8.5, 0, sin(a) * 8.5)
		p.face_towards(Vector3(1, 0, 0))
		spots[p.get_instance_id()] = p.position
		i += 1
	pens = {"goals": [0, 0], "taken": [0, 0], "kicker_team": randi() % 2, "order": order, "spots": spots,
		"phase": "", "timer": 0.0, "winner": -1, "human": false, "aim_z": 0.0}
	msg_label.text = "PENALTIES"
	print("PENALTIES  %s first" % ("we kick" if pens["kicker_team"] == 0 else "they kick"))
	_pen_setup_kick()


func _pen_setup_kick() -> void:
	var t: int = pens["kicker_team"]
	var list := team_list(t)
	var order: Array = pens["order"][t]
	var shooter: Player = list[order[int(pens["taken"][t]) % order.size()]]
	var keeper: Player = team_list(1 - t)[0]
	var spot := Vector3(HALF_L - PEN_SPOT, 0, 0)
	# last kicker back to the circle, the other keeper out of the way
	if pens.has("shooter"):
		var last: Player = pens["shooter"]
		last.position = pens["spots"][last.get_instance_id()]
		last.face_towards(Vector3(1, 0, 0))
	var waiting: Player = team_list(t)[0]
	waiting.position = Vector3(HALF_L - 20.0, 0, -10.0)
	waiting.face_towards(Vector3(1, 0, 0))
	ball.reset_to(spot)
	shooter.position = spot + Vector3(-2.2, 0, -0.5)
	shooter.vel = Vector3.ZERO
	shooter.face_towards(Vector3(1, 0, 0.2))
	keeper.position = Vector3(HALF_L - 0.4, 0, 0)
	keeper.vel = Vector3.ZERO
	keeper.face_towards(Vector3(-1, 0, 0))
	pens["shooter"] = shooter
	pens["keeper"] = keeper
	pens["phase"] = "aim"
	pens["timer"] = 0.0
	pens["outcome"] = ""
	pens["aim_z"] = 0.0
	pens["human"] = t == 0 and not autoplay
	_update_hint()
	charge = 0.0
	charging = false
	if pens["human"]:
		controlled = shooter
		msg_label.text = "YOUR PENALTY"
	else:
		pens["ai_z"] = randf_range(-1.0, 1.0) * (GOAL_W * 0.5 - 0.5)
		pens["ai_power"] = randf_range(0.35, 0.85)
		msg_label.text = "THEIR PENALTY"


func _pen_button(pressed: bool) -> void:
	if not pens.get("human", false) or pens.get("phase", "") != "aim":
		return
	if pressed:
		charging = true
		charge = 0.0
	elif charging:
		charging = false
		pens["power"] = charge if charge >= SHOT_TAP else SHOT_TAP_POWER   # a tap = quick shot
		pens["z"] = pens["aim_z"]
		pens["phase"] = "runup"
		pens["timer"] = 0.0
		msg_label.text = ""


func _pen_aim_z() -> float:
	var shooter: Player = pens["shooter"]
	var z: float = pens["aim_z"]
	if pad_active:
		z = _pad_stick().x * (GOAL_W * 0.5 + 0.3)
	else:
		var gp := _mouse_ground_point()
		var dir := Util.flat(gp - shooter.position)
		if dir.x > 0.3:
			z = shooter.position.z + dir.z * (HALF_L - shooter.position.x) / dir.x
	return clampf(z, -GOAL_W * 0.5 - 1.5, GOAL_W * 0.5 + 1.5)


func _pen_tick(delta: float) -> void:
	pens["timer"] += delta
	var shooter: Player = pens["shooter"]
	var keeper: Player = pens["keeper"]
	var timer: float = pens["timer"]
	match pens["phase"]:
		"aim":
			if pens["human"]:
				pens["aim_z"] = _pen_aim_z()
				shooter.face_towards(Vector3(HALF_L, 0, pens["aim_z"]) - shooter.position)
				if charging:
					charge = minf(charge + delta / 0.9, 1.0)
			elif timer > 1.6:
				pens["power"] = pens["ai_power"]
				pens["z"] = pens["ai_z"]
				pens["phase"] = "runup"
				pens["timer"] = 0.0
				msg_label.text = ""
		"runup":
			# a few steps up to the ball, then the kick; the keeper picks a side as it's struck
			var spot := Vector3(HALF_L - PEN_SPOT, 0, 0)
			var from := spot + Vector3(-2.2, 0, -0.5)
			var to := spot + Vector3(-0.7, 0, 0)
			shooter.position = from.lerp(to, clampf(timer / 0.4, 0.0, 1.0))
			shooter.vel = (to - from) / 0.4
			if timer >= 0.4:
				shooter.vel = Vector3.ZERO
				var power: float = pens["power"]
				shooter.shoot_at(Vector3(HALF_L, 0, pens["z"]), power, _pen_height(power), PEN_ERROR)
				var dive := randi() % 3 - 1
				pens["dive"] = dive
				if dive != 0:
					# facing -x the keeper's right is -z
					keeper.play_once("dive_left" if dive > 0 else "dive_right", 1.15)
				pens["phase"] = "flight"
				pens["timer"] = 0.0
		"flight":
			var dive: int = pens["dive"]
			keeper.position.z = move_toward(keeper.position.z, dive * PEN_DIVE_Z, delta * 7.5)
			var prev_x := ball.position.x
			ball.step(delta)
			if prev_x < keeper.position.x and ball.position.x >= keeper.position.x:
				var reach := PEN_REACH_DIVE if dive != 0 else PEN_REACH_STAY
				var top := 1.9 if dive != 0 else 2.25
				var dz := absf(ball.position.z - dive * PEN_DIVE_Z)
				if dz < reach and ball.position.y < top:
					ball.vel = Vector3(-absf(ball.vel.x) * 0.3, 2.0, ball.vel.z * 0.2 + dive * 1.5)
					_pen_result("saved")
				elif absf(ball.position.z) < GOAL_W * 0.5 - Ball.RADIUS and ball.position.y < GOAL_H - Ball.RADIUS:
					_pen_result("goal")
				else:
					_pen_result("miss")
			elif timer > 2.5:
				_pen_result("miss")   # it never got there
		"result":
			ball.step(delta)
			keeper.position.z = move_toward(keeper.position.z, int(pens["dive"]) * PEN_DIVE_Z, delta * 7.5)
			if timer > 2.0:
				var w := _pen_decided()
				if w >= 0:
					pens["winner"] = w
					pens["phase"] = "done"
					pens["timer"] = 0.0
					var g: Array = pens["goals"]
					msg_label.text = "%s ON PENALTIES  %d - %d" % ["WE WIN" if w == 0 else "THEY WIN", g[0], g[1]]
					sfx.whistle_times(3)
					print("PENALTIES %d - %d  winner %d" % [g[0], g[1], w])
					if w == 0:
						for p in home:
							p.celebrate(3.0)
				else:
					pens["kicker_team"] = 1 - int(pens["kicker_team"])
					_pen_setup_kick()
		"done":
			if timer > 3.0:
				_full_time()


func _pen_result(outcome: String) -> void:
	var t: int = pens["kicker_team"]
	pens["outcome"] = outcome
	pens["phase"] = "result"
	pens["timer"] = 0.0
	pens["taken"][t] += 1
	if outcome == "goal":
		pens["goals"][t] += 1
	var good := (outcome == "goal") == (t == 0)
	msg_label.text = {"goal": "GOAL!", "saved": "SAVED!", "miss": "MISSED!"}[outcome]
	if outcome == "goal" or good:
		_crowd("goal_for" if good else "goal_against")
	if outcome == "goal":
		sfx.whistle()
	print("PEN team %d %s  (%d - %d)" % [t, outcome, pens["goals"][0], pens["goals"][1]])


## Winning team, or -1 while it's still open. First five each (stops early once one side can't
## catch up), then sudden death in pairs.
func _pen_decided() -> int:
	var g: Array = pens["goals"]
	var n: Array = pens["taken"]
	if int(n[0]) < 5 or int(n[1]) < 5:
		for t in 2:
			if int(g[t]) > int(g[1 - t]) + (5 - int(n[1 - t])):
				return t
		return -1
	if n[0] == n[1] and g[0] != g[1]:
		return 0 if int(g[0]) > int(g[1]) else 1
	return -1


## What the post-match card says about a play-off leg.
func _playoff_info(ctx: Dictionary, gf: int, ga: int, won_after, pen_goals: Array, after_et: bool) -> Dictionary:
	var rnd := int(ctx["round"])
	var info := {"title": ClubState.round_name(rnd, ctx["tie"]), "leg": int(ctx["leg"]) + 1}
	var staying_up := not club.playoff.is_empty() and int(club.playoff["div"]) < club.division()
	if not ctx.has("first_leg"):
		info["line"] = "First leg %d–%d. Second leg %s." % [gf, ga, "at home" if not ctx["home"] else "away"]
		return info
	var a := int(ctx["first_leg"][0]) + gf
	var b := int(ctx["first_leg"][1]) + ga
	var won: bool = a > b if a != b else bool(won_after)
	info["aggregate"] = [a, b]
	info["won"] = won
	var how := ""
	if not pen_goals.is_empty():
		how = " (%d–%d on penalties)" % [pen_goals[0], pen_goals[1]]
	elif after_et:
		how = " (after extra time)"
	var line := ""
	if won and rnd == 3:
		line = "Won the play-off final%s — we stay up!" % how if staying_up else "Won the play-off final%s — promotion!" % how
	elif won:
		line = "Through to the %s%s." % [ClubState.round_name(rnd + 1, "").to_lower().replace("play-off ", ""), how]
	elif staying_up:
		line = "Out%s. We go down." % how
	else:
		line = "Out of the play-offs%s." % how
	info["line"] = "Aggregate %d–%d. %s" % [a, b, line]
	return info


# ================================================================== human input

# ------------------------------------------------------------------ fps overlay (` key; Shift+` = vsync on/off)
# (not F8/F9: when the game runs inside the Godot editor, F8 stops the game)

var _fps_layer: CanvasLayer
var _fps_label: Label
var _fps_t := 0.0


func _toggle_fps() -> void:
	if _fps_layer == null:
		_fps_layer = CanvasLayer.new()
		_fps_layer.layer = 100
		add_child(_fps_layer)
		var p := PanelContainer.new()
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0, 0, 0, 0.6)
		sb.set_corner_radius_all(4)
		sb.content_margin_left = 10
		sb.content_margin_right = 10
		sb.content_margin_top = 6
		sb.content_margin_bottom = 6
		p.add_theme_stylebox_override("panel", sb)
		# top right, under the hub's top bar and clear of the match score chip
		p.anchor_left = 1.0
		p.anchor_right = 1.0
		p.grow_horizontal = Control.GROW_DIRECTION_BEGIN
		p.offset_right = -16
		p.offset_top = 130
		p.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_fps_label = Label.new()
		_fps_label.add_theme_font_size_override("font_size", 15)
		_fps_label.add_theme_color_override("font_color", Color(1, 1, 1))
		p.add_child(_fps_label)
		_fps_layer.add_child(p)
		_fps_layer.visible = false
	_fps_layer.visible = not _fps_layer.visible
	_fps_t = 0.0


func _fps_tick(delta: float) -> void:
	if _fps_layer == null or not _fps_layer.visible:
		return
	_fps_t -= delta
	if _fps_t > 0.0:
		return
	_fps_t = 0.25
	var fps := Performance.get_monitor(Performance.TIME_FPS)
	var tris := Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
	var calls := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
	var fans := 0
	if grounds != null:
		for c in grounds.crowds:
			fans += c.fan_count()
	var vs := DisplayServer.window_get_vsync_mode() != DisplayServer.VSYNC_DISABLED
	_fps_label.text = "%d fps  ·  %.1f ms\n%.1f M triangles  ·  %d draw calls\n%d fans  ·  vsync %s (Shift+`)" % [
		fps, 1000.0 / maxf(fps, 1.0), tris / 1000000.0, calls, fans, "on" if vs else "off"]


func _process(delta: float) -> void:
	_fps_tick(delta)
	if _po_test >= 0.0:
		_po_test_tick(delta)


func _input(event: InputEvent) -> void:
	if event is InputEventKey and (event as InputEventKey).pressed and not (event as InputEventKey).echo:
		var ke := event as InputEventKey
		if ke.keycode == KEY_QUOTELEFT and not ke.shift_pressed:
			_toggle_fps()
		elif ke.keycode == KEY_QUOTELEFT and ke.shift_pressed:
			var on := DisplayServer.window_get_vsync_mode() != DisplayServer.VSYNC_DISABLED
			DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED if on else DisplayServer.VSYNC_ENABLED)
	# which device is in charge: a pad as soon as you use it, keyboard/mouse back when you touch those
	var was := pad_active
	if event is InputEventJoypadButton and (event as InputEventJoypadButton).pressed:
		pad_active = true
		pad_device = event.device
	elif event is InputEventJoypadMotion and absf((event as InputEventJoypadMotion).axis_value) > 0.5:
		pad_active = true
		pad_device = event.device
	elif event is InputEventKey and (event as InputEventKey).pressed:
		pad_active = false
	elif event is InputEventMouseButton or (event is InputEventMouseMotion and (event as InputEventMouseMotion).relative.length() > 3.0):
		pad_active = false
	if was != pad_active:
		_update_hint()


func _update_hint() -> void:
	if hint_label == null:
		return
	if state == "penalties":
		hint_label.text = ("Penalty: LS left/right aims · hold B for power, release to shoot · Start pause" if pad_active else
			"Penalty: aim with the mouse · hold RMB for power, release to shoot · Esc quit")
		return
	hint_label.text = ("LS move · LT walk · A pass (A A high) · X lob/cross · Y through (Y Y high, LB+Y over the top) · hold B shoot (LB+B chip) · no ball: A tackle, X slide, LB switch · Start pause"
		if pad_active else
		"WASD move · Shift walk · LMB pass · MMB high pass · E lob/cross · F through (Ctrl high, Shift over the top) · hold RMB shoot (Ctrl chip) · Space tackle · C slide · Q switch · Esc quit")


## Controller buttons in a match (FIFA-like, Xbox): A pass · B shoot (hold for power) · X tackle ·
## LB switch · Start pause. After the match: A / Start back to the club.
func _pad_button(b: InputEventJoypadButton) -> void:
	if mode == "summary":
		if b.pressed and b.button_index in [JOY_BUTTON_A, JOY_BUTTON_START]:
			back_to_hub()
		return
	if mode != "match":
		return
	if b.pressed and b.button_index == JOY_BUTTON_START:
		_toggle_pause()
		return
	if paused:
		return
	if state == "penalties":
		if b.button_index == JOY_BUTTON_B:
			_pen_button(b.pressed)
		return
	var live := (state == "play" or state == "restart") and controlled != null
	var lb := Input.is_joy_button_pressed(pad_device, JOY_BUTTON_LEFT_SHOULDER)
	match b.button_index:
		JOY_BUTTON_A:
			if b.pressed and live and controlled.has_ball():
				_queue_pass("ground")
			elif b.pressed and state == "play" and controlled != null and not controlled.has_ball():
				controlled.start_poke()
		JOY_BUTTON_B:
			if b.pressed and live and controlled.has_ball():
				charging = true
				charge = 0.0
				chip_shot = lb
			elif not b.pressed and charging:
				charging = false
				if live and controlled.has_ball():
					_human_shoot()
		JOY_BUTTON_X:
			if b.pressed and live and controlled.has_ball():
				_queue_pass("lob")
			elif b.pressed and state == "play" and controlled != null and not controlled.has_ball():
				controlled.start_tackle()
		JOY_BUTTON_Y:
			if b.pressed and live and controlled.has_ball():
				_queue_pass("through_lob" if lb else "through")
		JOY_BUTTON_LEFT_SHOULDER:
			# with the ball LB is a modifier (LB+Y, LB+B), without it switches player
			if b.pressed and (state == "play" or state == "restart") and not (controlled != null and controlled.has_ball()):
				_manual_switch()


func _toggle_pause() -> void:
	paused = not paused
	Engine.time_scale = 0.0 if paused else 1.0
	msg_label.text = "PAUSED  (Start to play on)" if paused else ""


## Left stick (with a dead zone), in pitch directions: up = away from the camera.
func _pad_stick() -> Vector2:
	var v := Vector2(Input.get_joy_axis(pad_device, JOY_AXIS_LEFT_X), Input.get_joy_axis(pad_device, JOY_AXIS_LEFT_Y))
	var l := v.length()
	if l < PAD_DEADZONE:
		return Vector2.ZERO
	return v / l * minf(1.0, (l - PAD_DEADZONE) / (1.0 - PAD_DEADZONE))


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventJoypadButton:
		_pad_button(event as InputEventJoypadButton)
		return
	if mode == "freecam" and event is InputEventKey and (event as InputEventKey).pressed and (event as InputEventKey).keycode == KEY_F5:
		mode = "match"   # dev cheat: back to the match
		msg_label.text = ""
		return
	if mode == "hub" or mode == "freecam":
		if event is InputEventMouseMotion and _hub_drag:
			var mm := event as InputEventMouseMotion
			hub_yaw -= mm.relative.x * HUB_DRAG_SENS * SettingsScript.camera_mult()
			hub_pitch = clampf(hub_pitch + rad_to_deg(mm.relative.y * HUB_DRAG_SENS), HUB_PITCH_MIN, HUB_PITCH_MAX)
			_hub_drag_moved += mm.relative.length()
		elif event is InputEventMouseButton:
			var mb0 := event as InputEventMouseButton
			if mb0.button_index in [MOUSE_BUTTON_RIGHT, MOUSE_BUTTON_MIDDLE]:
				if mb0.pressed:
					_hub_drag = true
					_hub_drag_moved = 0.0
				else:
					_hub_drag = false
					# a right click without dragging still cancels placing
					if mb0.button_index == MOUSE_BUTTON_RIGHT and _hub_drag_moved < 6.0:
						_cancel_placing()
			elif mb0.pressed:
				if mb0.button_index == MOUSE_BUTTON_WHEEL_UP:
					hub_zoom = clampf(hub_zoom * 0.9, HUB_ZOOM_MIN, HUB_ZOOM_MAX)
				elif mb0.button_index == MOUSE_BUTTON_WHEEL_DOWN:
					hub_zoom = clampf(hub_zoom * 1.1, HUB_ZOOM_MIN, HUB_ZOOM_MAX)
				elif mb0.button_index == MOUSE_BUTTON_LEFT:
					_hub_click()
		elif event is InputEventKey and (event as InputEventKey).pressed:
			var hk := (event as InputEventKey).keycode
			if hk == KEY_ESCAPE:
				_cancel_placing()
			elif hk == KEY_C:
				reset_hub_camera()
			elif hk == KEY_F1:
				hub.cheats_open = not hub.cheats_open
				hub.refresh()
		return
	if mode != "match":
		return
	if event is InputEventKey:
		var k := event as InputEventKey
		if not k.pressed or k.echo:
			return
		match k.keycode:
			KEY_R:
				_restart()
			KEY_ESCAPE:
				get_tree().quit()
			KEY_SPACE:
				if state == "play" and controlled != null and not controlled.has_ball():
					controlled.start_poke()
			KEY_C:
				if state == "play" and controlled != null and not controlled.has_ball():
					controlled.start_tackle()
			KEY_E:
				if _can_pass():
					_do_pass("lob")
			KEY_F:
				if _can_pass():
					_do_pass("through_lofted" if k.ctrl_pressed else ("through_lob" if k.shift_pressed else "through"))
			KEY_Q:
				if state == "play" or state == "restart":
					_manual_switch()
			KEY_F2:
				# dev cheat: end the match now with the current score
				if state != "fulltime":
					_full_time()
			KEY_F3, KEY_F4:
				# dev cheat: goal for you (F3) or for them (F4)
				if state == "play" or state == "restart" or state == "kickoff":
					var t := 0 if k.keycode == KEY_F3 else 1
					ball.last_touch = (home if t == 0 else away)[home.size() - 2]
					_goal(t)
			KEY_F5:
				# dev cheat: pause and look around with the hub camera; F5 again to play on
				hub_focus = Util.flat(ball.position)
				mode = "freecam"
				msg_label.text = "FREE CAMERA  (F5 to play on)"
	elif event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_UP:
			match_zoom = clampf(match_zoom * 0.9, 0.5, 1.8)
			return
		if mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			match_zoom = clampf(match_zoom * 1.1, 0.5, 1.8)
			return
		if state == "penalties":
			if mb.button_index == MOUSE_BUTTON_RIGHT:
				_pen_button(mb.pressed)
			return
		if (state != "play" and state != "restart") or controlled == null:
			return
		if mb.button_index == MOUSE_BUTTON_LEFT and mb.pressed:
			if controlled.has_ball():
				_human_pass()
		elif mb.button_index == MOUSE_BUTTON_MIDDLE and mb.pressed:
			if controlled.has_ball():
				_do_pass("lofted")
		elif mb.button_index == MOUSE_BUTTON_RIGHT:
			if mb.pressed and controlled.has_ball():
				charging = true
				charge = 0.0
				chip_shot = mb.ctrl_pressed
			elif not mb.pressed and charging:
				charging = false
				if controlled.has_ball():
					_human_shoot()


func _update_human(delta: float) -> void:
	if autoplay:
		return
	switch_cooldown = maxf(0.0, switch_cooldown - delta)
	manual_lock = maxf(0.0, manual_lock - delta)
	if pad_active:
		var rs := Input.get_joy_axis(pad_device, JOY_AXIS_RIGHT_Y)
		if absf(rs) > 0.3:
			match_zoom = clampf(match_zoom * (1.0 + rs * delta * 1.2), 0.5, 1.8)
	q_time += delta
	_pending_pass_tick(delta)
	_auto_switch()
	if controlled == null:
		return
	var stick := Vector2.ZERO
	if pad_active:
		stick = _pad_stick()
		aim_point = _pad_aim(stick)
	else:
		aim_point = _mouse_ground_point()
	if _ui_demo:
		_ui_demo_tick()

	var mv := Vector3.ZERO
	if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
		mv.z -= 1.0
	if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
		mv.z += 1.0
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
		mv.x -= 1.0
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
		mv.x += 1.0
	if stick != Vector2.ZERO:
		mv = Vector3(stick.x, 0, stick.y)

	if RECEIVE_ASSIST and ball.pass_target == controlled and ball.owner_player == null:
		# a pass is coming: run to where it was played (like the AI does), your input waits until you have it
		var meet := ball.pass_meet if (ball.pass_meet != Vector3.INF and not ball.past_meet()) else Util.flat(ball.position + ball.vel * 0.3)
		var near := Util.flat_dist(controlled.position, ball.position) <= 6.0
		if ball.pass_lob or ball.pass_through:
			# air ball / through-ball: get to where it comes down; only go for the ball itself once it's low and close
			if near and ball.position.y < 1.2:
				meet = Util.flat(ball.position + ball.vel * 0.15)
		elif not near:
			meet = meet.lerp(Util.flat(ball.position), 0.35)
		else:
			meet = Util.flat(ball.position + ball.vel * 0.15)
		var to_meet := Util.flat(meet - controlled.position)
		controlled.desired_move = to_meet.limit_length(1.0) if to_meet.length() > 0.3 else Vector3.ZERO
		controlled.wants_sprint = to_meet.length() > 2.0
	elif mv != Vector3.ZERO:
		controlled.desired_move = mv.normalized()
	else:
		controlled.desired_move = Vector3.ZERO
	if not (RECEIVE_ASSIST and ball.pass_target == controlled and ball.owner_player == null):
		# sprint is the default; hold Shift to walk (Marcel, 2026-11-07: holding Shift all match hurts)
		controlled.wants_sprint = not Input.is_key_pressed(KEY_SHIFT)
		if pad_active:
			# pad: LT held or the stick only half tilted = walk
			controlled.wants_sprint = Input.get_joy_axis(pad_device, JOY_AXIS_TRIGGER_LEFT) < 0.5 and stick.length() >= PAD_WALK_TILT

	if charging:
		charge = minf(charge + delta / 0.9, 1.0)
		if not controlled.has_ball():
			charging = false
		else:
			controlled.face_towards(aim_point - controlled.position)


## Pad aiming, FIFA-style: passes go the way the left stick points (or the way you face); a shot
## goes at the goal, the stick's up/down picks the far or near side.
func _pad_aim(stick: Vector2) -> Vector3:
	var p := controlled
	var dir := Vector3(stick.x, 0, stick.y) if stick != Vector2.ZERO else Util.flat(p.facing)
	if dir.length() < 0.01:
		dir = Vector3(p.attack_dir, 0, 0)
	var shooting := charging and p.role != "GK" and p.restart_kind not in ["corner", "throw-in"]
	if shooting:
		return Vector3(HALF_L * p.attack_dir, 0, clampf(stick.y, -1.0, 1.0) * GOAL_W * 0.4)
	return p.position + dir.normalized() * 18.0


func _human_pass() -> void:
	var aim := Util.flat(aim_point - controlled.position)
	var mate := _pass_target_in_cone(controlled, aim)
	if mate != null:
		controlled.pass_to(mate)
		if mate.role != "GK":
			controlled = mate
		switch_cooldown = 0.3
	else:
		controlled.pass_towards(aim_point)


# ------------------------------------------------------------------ pass types (GDD §7, Marcel 2026-11-08)
# Pad, FIFA layout: A pass (A A half-high), X lob / cross, Y through-ball (Y Y half-high, LB+Y over the top),
# LB+B chip. Every pad pass has a short wind-up in which a second tap upgrades it (FIFA-style).
# Mouse/keyboard stay instant: LMB pass, MMB half-high, E lob/cross, F through (Ctrl+F half-high,
# Shift+F over the top), Ctrl+RMB chip.

const PASS_WINDUP := 0.18        # seconds between pressing a pass (pad) and the kick; the double-tap window
var pending_pass := {}           # {kind, t, by}
var chip_shot := false


func _can_pass() -> bool:
	return (state == "play" or state == "restart") and controlled != null and controlled.has_ball()


func _queue_pass(kind: String) -> void:
	if not pending_pass.is_empty() and pending_pass["by"] == controlled:
		if pending_pass["kind"] == "ground" and kind == "ground":
			pending_pass["kind"] = "lofted"
		elif pending_pass["kind"] == "through" and kind == "through":
			pending_pass["kind"] = "through_lofted"
		return
	pending_pass = {"kind": kind, "t": PASS_WINDUP, "by": controlled}


func _pending_pass_tick(delta: float) -> void:
	if pending_pass.is_empty():
		return
	var by: Player = pending_pass["by"]
	if by != controlled or not by.has_ball() or (state != "play" and state != "restart"):
		pending_pass = {}
		return
	pending_pass["t"] -= delta
	if pending_pass["t"] <= 0.0:
		var kind: String = pending_pass["kind"]
		pending_pass = {}
		_do_pass(kind)


## Flank in the opponent's half: a lob becomes a cross into the box.
func _in_cross_zone(p: Player) -> bool:
	return p.position.x * p.attack_dir > 0.0 and absf(p.position.z) > BOX_HALF_W - 4.0


func _do_pass(kind: String) -> void:
	var p := controlled
	if p.restart_kind == "throw-in":
		_human_pass()   # throw-ins are thrown, whatever the button
		return
	var aim := Util.flat(aim_point - p.position)
	var mate: Player = null
	match kind:
		"ground":
			_human_pass()
			return
		"lofted":
			mate = _pass_target_in_cone(p, aim)
			if mate != null:
				p.lofted_pass_to(mate)
			else:
				var lt := Player.lofted_time(minf(Util.flat_dist(p.position, aim_point), 35.0))
				p.air_ball_to(p.position + aim.normalized() * minf(aim.length(), 35.0), lt)
		"lob":
			if _in_cross_zone(p) and p.role != "GK":
				mate = _cross_target(p)
				p.cross_to(mate, Vector3((HALF_L - 9.0) * p.attack_dir, 0, -signf(p.position.z) * 2.0))
			else:
				mate = _pass_target_in_cone(p, aim, 60.0)
				if mate != null:
					p.lob_pass_to(mate)
				else:
					p.air_ball_towards(aim_point, 18.0, 1.0, 1.7, "shoot")
		"through", "through_lofted", "through_lob":
			mate = _through_target(p, aim)
			var style: String = {"through": "ground", "through_lofted": "lofted", "through_lob": "lob"}[kind]
			if mate != null:
				p.through_to(mate, style)
			elif style == "ground":
				p.pass_towards(aim_point)
			else:
				p.air_ball_towards(aim_point, 20.0 if style == "lofted" else 18.0, 0.6 if style == "lofted" else 1.0, 0.8 if style == "lofted" else 1.7)
	if mate != null and mate.role != "GK":
		controlled = mate
	switch_cooldown = 0.3
	print("[%s] PASS %s by #%d -> %s" % [_clock_text(), kind, home.find(p), "space" if mate == null else "#%d" % home.find(mate)])


## Cross: the teammate in (or running into) the box nearest the penalty spot.
func _cross_target(p: Player) -> Player:
	var spot := Vector3((HALF_L - 11.0) * p.attack_dir, 0, 0)
	var best: Player = null
	var best_d := INF
	for m in team_list(p.team):
		if m == p or m.role == "GK":
			continue
		var depth := m.position.x * p.attack_dir
		if depth < HALF_L - BOX_DEPTH - 6.0 or absf(m.position.z) > BOX_HALF_W + 2.0:
			continue
		var d := Util.flat_dist(m.position, spot)
		if d < best_d:
			best_d = d
			best = m
	return best


## Through-ball: a teammate roughly the way you aim, preferring the ones further forward.
func _through_target(p: Player, aim: Vector3) -> Player:
	if aim.length() < 0.01:
		return null
	var best: Player = null
	var best_score := -INF
	for m in team_list(p.team):
		if m == p or m.role == "GK":
			continue
		var to := Util.flat(m.position - p.position)
		var d := to.length()
		if d < 3.0 or d > 45.0:
			continue
		var ang := aim.angle_to(to)
		if ang > deg_to_rad(45.0):
			continue
		var s := -ang * 6.0 + (m.position.x - p.position.x) * p.attack_dir * 0.06 - d * 0.03
		if s > best_score:
			best_score = s
			best = m
	return best


func _human_shoot() -> void:
	var p := controlled
	if charge < SHOT_TAP:
		charge = SHOT_TAP_POWER   # a tap: quick shot
	if p.role == "GK" or p.restart_kind == "corner":
		p.long_kick(aim_point, charge)
		return
	if p.restart_kind == "throw-in":
		p.pass_towards(aim_point)
		return
	var gp := goal_aim_point(p)
	if chip_shot:
		chip_shot = false
		p.chip_at(gp if gp != Vector3.INF else aim_point, charge)
		return
	if gp != Vector3.INF:
		p.shoot_at(gp, charge, shot_height(charge), 1.0)
	else:
		p.shoot_at(aim_point, charge, 0.5, 1.0)


## Where on the opponent's goal line the current aim is pointing, or Vector3.INF if not at goal.
func goal_aim_point(p: Player) -> Vector3:
	var dir := Util.flat(aim_point - p.position)
	if dir.x * p.attack_dir <= 0.05:
		return Vector3.INF
	var gx := HALF_L * p.attack_dir
	var t := (gx - p.position.x) / dir.x
	var z := p.position.z + dir.z * t
	if absf(z) > GOAL_W * 0.5 + 3.0:
		return Vector3.INF
	return Vector3(gx, 0, z)


func shot_height(power: float) -> float:
	return lerpf(0.35, 1.5, power)


func _pass_target_in_cone(p: Player, aim: Vector3, max_d := 32.0) -> Player:
	if aim.length() < 0.01:
		return null
	var best: Player = null
	var best_score := -INF
	for mate in team_list(p.team):
		if mate == p:
			continue
		var to := Util.flat(mate.position - p.position)
		var d := to.length()
		if d < 1.5 or d > max_d:
			continue
		var ang := aim.angle_to(to)
		if ang > deg_to_rad(40.0):
			continue
		var s := -ang * 8.0 - d * 0.08
		if s > best_score:
			best_score = s
			best = mate
	return best


## Automatic switching (Marcel, 2026-11-07): your pass -> receiver, a teammate wins the ball,
## a loose ball that a teammate is clearly closer to, and when you've been beaten.
## Plus, from earlier decisions: your keeper while he holds the ball, and your own set pieces.
var manual_lock := 0.0          # after Q, distance-based auto-switching waits a moment
var q_time := 99.0


func _auto_switch() -> void:
	var holder := ball.owner_player
	if holder != null and holder.team == 0 and (holder.role == "GK" or holder.restart_kind != ""):
		controlled = holder
		return
	if holder != null and holder.team == 0 and holder != controlled:
		controlled = holder   # a teammate won / received the ball
		switch_cooldown = 0.5
		return
	if controlled != null and controlled.role == "GK" and holder != controlled:
		controlled = _nearest_to_ball(home, true)
		return
	if controlled == null or switch_cooldown > 0.0 or manual_lock > 0.0:
		return
	if ball.pass_target != null and ball.pass_target.team == 0:
		return   # one of our passes is on its way, the receiver switch already happened
	var target := ball.position + ball.vel * 0.3
	if holder == null:
		# loose ball: only switch when someone is clearly closer
		var best := _nearest_to_ball(home, true)
		if best != null and best != controlled and Util.flat_dist(best.position, target) + LOOSE_SWITCH_MARGIN < Util.flat_dist(controlled.position, target):
			controlled = best
			switch_cooldown = 0.8
		return
	if holder.team == 1:
		# beaten: the ball carrier is past you, towards your goal -> nearest teammate goal-side of him
		var dir := controlled.attack_dir
		if (controlled.position.x - holder.position.x) * dir > BEATEN_MARGIN:
			var best_d := INF
			var best: Player = null
			for p in home:
				if p.role == "GK" or p == controlled:
					continue
				if (p.position.x - holder.position.x) * dir >= 0.0:
					continue
				var d := Util.flat_dist(p.position, holder.position)
				if d < best_d:
					best_d = d
					best = p
			if best != null:
				controlled = best
				switch_cooldown = 1.0


## Q (Marcel, 2026-11-07: cycling drifted away from the ball): always the teammate nearest to where
## the ball is going, other than the one you control — recomputed on every press. Pressing again
## therefore bounces between the two nearest players instead of walking further away.
func _manual_switch() -> void:
	var target := Util.flat(ball.position + ball.vel * 0.4)
	var best: Player = null
	var best_d := INF
	for p in home:
		if p.role == "GK" or p == controlled:
			continue
		var d := Util.flat_dist(p.position, target)
		if d < best_d:
			best_d = d
			best = p
	if best == null:
		return
	controlled = best
	q_time = 0.0
	manual_lock = 1.5


func _mouse_ground_point() -> Vector3:
	var mp := get_viewport().get_mouse_position()
	var origin := camera.project_ray_origin(mp)
	var dir := camera.project_ray_normal(mp)
	if absf(dir.y) < 0.0001:
		return aim_point
	var t := -origin.y / dir.y
	if t < 0.0:
		return aim_point
	return origin + dir * t


# ================================================================== possession

func _resolve_possession(delta: float) -> void:
	var holder := ball.owner_player
	if holder == null:
		_try_collect()
		return
	if holder.role == "GK" and holder.in_own_box():
		return   # keepers with the ball in their box are untouchable
	for opp in team_list(1 - holder.team):
		if opp.touch_cooldown > 0.0 or opp.stun > 0.0:
			continue
		var d := Util.flat_dist(opp.position, ball.position)
		# lunging tackle
		var poke := opp.tackle_kind == "poke"
		var tackle_reach := (POKE_REACH if poke else 1.2) if opp.is_human else 0.8
		if opp.tackle_timer > 0.0 and d < tackle_reach and holder.protect <= 0.0:
			var success := diff("human_tackle_success") if opp.is_human else diff("ai_tackle_success")
			if poke:
				success *= POKE_SUCCESS
			if randf() < success:
				_steal(opp, holder)
			else:
				opp.tackle_timer = 0.0
				opp.stun = 0.0 if poke else 0.5   # a standing tackle that fails: you're still on your feet
				if holder.is_human:
					toast("DODGED!")
			return
		# pressure: stand on the ball long enough and you nick it
		var press_reach := 1.0 if opp.is_human else 0.9
		# you can't nick the ball from straight behind: the presser has to be beside or in front
		var side := Util.flat(opp.position - holder.position).normalized().dot(holder.facing)
		if d < press_reach and side > -0.35:
			opp.contact_time += delta
		else:
			opp.contact_time = maxf(0.0, opp.contact_time - delta * 2.0)
		var needed := AI_STEAL_TIME
		if opp.is_human:
			needed = diff("human_steal_time")
		elif holder.is_human:
			needed = diff("ai_steal_time_vs_human")
		if opp.contact_time > needed and holder.protect <= 0.0:
			_steal(opp, holder)
			return


func _try_collect() -> void:
	var best: Player = null
	var best_d := INF
	for p in players:
		if p.touch_cooldown > 0.0 or p.stun > 0.0:
			continue
		var keeper := p.role == "GK" and p.in_own_box()
		var reach: float = keeper_reach(p.team) if keeper else (0.85 if p.is_human else 0.7)
		if ball.pass_target == p and not keeper:
			reach = maxf(reach, RECEIVE_REACH)
		var max_h := 2.4 if keeper else (1.7 if ball.pass_target == p else 1.0)   # receivers can chest a lobbed pass down
		if ball.position.y > max_h:
			continue
		var d := Util.flat_dist(p.position, ball.position)
		if d < reach and d < best_d:
			best_d = d
			best = p
	if best == null:
		return
	if best in ball.offside_players:
		_call_offside(best)
		return
	if ball.last_touch != null and best.team != ball.last_touch.team:
		ball.offside_players.clear()
	var spd := ball.flat_speed()
	if best.role == "GK" and best.in_own_box():
		var parry_chance := diff("their_keeper_parry") if best.team == 1 else 0.35
		if spd > 18.0 and randf() < parry_chance:
			ball.vel = Vector3(-ball.vel.x * 0.3, 3.0, ball.vel.z * 0.4 + randf_range(-5.0, 5.0))
			ball.last_touch = best
			ball.pass_target = null
			best.touch_cooldown = 0.6
			toast("PARRIED!")
			return
		if spd > 12.0 and ball.last_touch != null and ball.last_touch.team != best.team:
			stats["saves"][best.team] += 1
			toast("SAVE!")
			_crowd("save" if best.team == 0 else "chance")
	elif spd > (19.0 if best.is_human else 16.0) and ball.pass_target != best:
		# too hot to control: deflection
		ball.vel = Vector3(ball.vel.x * 0.4 + randf_range(-3.0, 3.0), 1.5, ball.vel.z * 0.4 + randf_range(-3.0, 3.0))
		ball.last_touch = best
		ball.pass_target = null
		best.touch_cooldown = 0.35
		return
	_give_ball(best)


func _give_ball(p: Player) -> void:
	if ball.last_touch != null and ball.last_touch.team != p.team and ball.owner_player == null:
		stats["intercepts"][p.team] += 1
	elif ball.pass_target != null and ball.last_touch != null and ball.last_touch != p and ball.last_touch.team == p.team:
		stats["completed"][p.team] += 1
	ball.owner_player = p
	ball.pass_target = null
	ball.last_touch = p
	ball.vel = Vector3.ZERO
	var humans_side := p.team == 0 and not autoplay and p.role != "GK"
	p.protect = HUMAN_PROTECT if humans_side else 0.5
	p.has_ball_time = 0.0
	p.think_timer = randf_range(0.2, 0.4)
	for q in players:
		q.contact_time = 0.0


func _steal(winner: Player, loser: Player) -> void:
	loser.touch_cooldown = 0.8
	loser.stun = 0.25
	winner.contact_time = 0.0
	winner.tackle_timer = 0.0
	stats["steals"][winner.team] += 1
	if winner.team == 0 and grounds != null:
		_crowd("tackle")
	if winner.is_human:
		toast("WON IT!")
	elif loser.is_human:
		toast("ROBBED")
	var loose_chance := 0.15 if winner.is_human else 0.35
	if randf() < loose_chance:
		ball.owner_player = null
		var a := randf() * TAU
		ball.vel = Vector3(cos(a) * 4.5, 0.5, sin(a) * 4.5)
		ball.last_touch = winner
		winner.touch_cooldown = 0.2
	else:
		_give_ball(winner)


func _separate_players() -> void:
	var min_d := Player.RADIUS * 2.0
	for i in players.size():
		for j in range(i + 1, players.size()):
			var a := players[i]
			var b := players[j]
			var diff := Util.flat(a.position - b.position)
			var d := diff.length()
			if d < min_d and d > 0.001:
				var push := diff / d * (min_d - d) * 0.5
				# a set-piece taker can't be shoved off his spot
				if a.restart_kind != "":
					b.position -= push * 2.0
				elif b.restart_kind != "":
					a.position += push * 2.0
				else:
					a.position += push
					b.position -= push


# ================================================================== AI helpers (used by Player)

## Greedy man-marking: most dangerous attacker gets the closest free defender.
var _bunch_test := false
var _bunch_t := 0.0
var _bunch_hits := 0
var _bunch_samples := 0


## dev (--bunch-test): log moments where 3+ teammates stand within 2.5 m of each other.
func _bunch_check(delta: float) -> void:
	_bunch_t += delta
	if _bunch_t < 0.5 or state != "play":
		return
	_bunch_t = 0.0
	_bunch_samples += 1
	for t in 2:
		var list := team_list(t)
		for p in list:
			if p.role == "GK":
				continue
			var near: Array = []
			for q in list:
				if q != p and q.role != "GK" and Util.flat_dist(p.position, q.position) < 2.5:
					near.append(q)
			if near.size() >= 2:
				_bunch_hits += 1
				var holder := ball.owner_player
				var who := "loose" if holder == null else ("own" if holder.team == t else "opp")
				var info := []
				for q in [p] + near:
					var qq: Player = q
					info.append("%s(run=%s mark=%s chase=%s 2nd=%s zone=%s)" % [qq.role, qq.run_mode, qq.mark_target != null,
						is_chaser(qq), is_second_presser(qq), zone_owner(t) == qq])
				print("BUNCH t%d ball=%s at %s: %s" % [t, who, str(Util.flat(p.position).snapped(Vector3(0.1, 0.1, 0.1))), ", ".join(info)])
				return


func _assign_marks(t: int) -> void:
	var defenders: Array[Player] = []
	for p in team_list(t):
		p.mark_target = null
		if p.role != "GK":
			defenders.append(p)
	var own_goal := Vector3(-HALF_L * team_list(t)[0].attack_dir, 0, 0)
	var attackers: Array[Player] = []
	for o in team_list(1 - t):
		if o.role != "GK" and o != ball.owner_player:
			attackers.append(o)
	attackers.sort_custom(func(a: Player, b: Player) -> bool:
		return Util.flat_dist(a.position, own_goal) < Util.flat_dist(b.position, own_goal))
	for o in attackers:
		var best: Player = null
		var best_d := INF
		for d in defenders:
			if d.mark_target != null:
				continue
			var dist := Util.flat_dist(d.position, o.position)
			if dist < best_d:
				best_d = dist
				best = d
		if best != null:
			best.mark_target = o


func team_list(t: int) -> Array[Player]:
	return home if t == 0 else away


func _nearest_to_ball(list: Array[Player], skip_gk: bool) -> Player:
	var best: Player = null
	var best_d := INF
	var target := ball.position + ball.vel * 0.2
	for p in list:
		if skip_gk and p.role == "GK":
			continue
		var d := Util.flat_dist(p.position, target)
		if d < best_d:
			best_d = d
			best = p
	return best


func is_chaser(p: Player) -> bool:
	var nearest := _nearest_to_ball(team_list(p.team), true)
	if nearest != p:
		return false
	if p.team == 0 and not autoplay and controlled != null:
		# the human does the chasing unless this AI is way closer
		return Util.flat_dist(p.position, ball.position) < Util.flat_dist(controlled.position, ball.position) - 3.0
	return true


## The second-nearest outfielder to the ball covers when the opponent has it close by.
## The defender whose zone the ball carrier is in (not the chaser / second man), or null.
func zone_owner(t: int) -> Player:
	var holder := ball.owner_player
	if holder == null or holder.team == t:
		return null
	var first := _nearest_to_ball(team_list(t), true)
	var best: Player = null
	var best_d := STEP_OUT_RADIUS
	for p in team_list(t):
		if p.role == "GK" or p == first or p.is_human or is_second_presser(p):
			continue
		var d := Util.flat_dist(p.zone_spot(), holder.position)
		if d < best_d:
			best_d = d
			best = p
	return best


## True when the team's chaser is already within a few metres of the opposing ball carrier.
func carrier_pressed(t: int) -> bool:
	var holder := ball.owner_player
	if holder == null or holder.team == t:
		return false
	var first := _nearest_to_ball(team_list(t), true)
	return first != null and Util.flat_dist(first.position, holder.position) < 5.0


func count_run_mode(t: int, mode_name: String) -> int:
	var n := 0
	for p in team_list(t):
		if p.run_mode == mode_name:
			n += 1
	return n


func is_second_presser(p: Player) -> bool:
	var first := _nearest_to_ball(team_list(p.team), true)
	var best: Player = null
	var best_d := INF
	for q in team_list(p.team):
		if q.role == "GK" or q == first or q.is_human:
			continue
		var d := Util.flat_dist(q.position, ball.position)
		if d < best_d:
			best_d = d
			best = q
	return best == p and best_d < 18.0


func nearest_opponent(p: Player) -> Player:
	var best: Player = null
	var best_d := INF
	for o in team_list(1 - p.team):
		var d := Util.flat_dist(o.position, p.position)
		if d < best_d:
			best_d = d
			best = o
	return best


func best_open_teammate(p: Player) -> Player:
	var best: Player = null
	var best_score := -INF
	for mate in team_list(p.team):
		if mate == p or mate.role == "GK":
			continue
		var d := Util.flat_dist(mate.position, p.position)
		if d < 3.0 or d > 40.0:
			continue
		if in_offside_position(mate, p.position.x):
			continue
		var open := 10.0
		for o in team_list(1 - p.team):
			open = minf(open, Util.flat_dist(o.position, mate.position))
			open = minf(open, _dist_to_segment(o.position, p.position, mate.position) * 1.5)
		if open < 1.2:
			continue
		var forward := (mate.position.x - p.position.x) * p.attack_dir
		var s := open * 0.8 + forward * 0.35
		if s > best_score:
			best_score = s
			best = mate
	return best


func _dist_to_segment(pt: Vector3, a: Vector3, b: Vector3) -> float:
	var ab := Util.flat(b - a)
	var ap := Util.flat(pt - a)
	var len2 := ab.length_squared()
	if len2 < 0.0001:
		return ap.length()
	var t := clampf(ap.dot(ab) / len2, 0.0, 1.0)
	return (ap - ab * t).length()


# ================================================================== shot test (dev)
# `-- --shot-test`: fires 90 "human" shots at the away keeper and prints how many go in.

var _st_shooter: Player
var _st_keeper: Player
var _st_n := 0
var _st_outcome := ""
var _st_power := 0.0
var _st_stats := {}


func _shot_test_begin() -> void:
	state = "shottest"
	msg_label.text = ""
	_st_shooter = home[1]
	_st_keeper = away[0]
	for p in players:
		if p != _st_shooter and p != _st_keeper:
			p.position = Vector3(0, 0, -HALF_W + 0.5)
	state_timer = 0.0


func _shot_test_step(delta: float) -> void:
	state_timer -= delta
	if state_timer <= 0.0:
		if _st_n > 0:
			_st_record(_st_outcome if _st_outcome != "" else "miss")
		if _st_n >= 90:
			_st_report()
			get_tree().quit()
			return
		_st_n += 1
		_st_outcome = ""
		state_timer = 2.0
		_st_keeper.position = _st_keeper.home_pos
		_st_keeper.vel = Vector3.ZERO
		_st_shooter.position = Vector3(HALF_L - randf_range(8.0, 20.0), 0, randf_range(-10.0, 10.0))
		_st_shooter.is_human = true
		ball.reset_to(_st_shooter.position)
		_st_power = randf()
		var gp := Vector3(HALF_L, 0, randf_range(GOAL_W * 0.25, GOAL_W * 0.5 - 0.3) * (1.0 if randf() < 0.5 else -1.0))
		_st_shooter.shoot_at(gp, _st_power, shot_height(_st_power), 1.0)
	_st_keeper.ai_update(delta)
	_st_keeper.step(delta)
	ball.step(delta)
	if _st_outcome != "":
		return
	if Util.flat_dist(_st_keeper.position, ball.position) < keeper_reach(1) and ball.position.y < 2.4:
		_st_outcome = "save"
		ball.vel = Vector3.ZERO
		ball.position = Vector3(0, Ball.RADIUS, 0)
	elif ball.position.x > HALF_L + Ball.RADIUS:
		_st_outcome = "goal" if (absf(ball.position.z) < GOAL_W * 0.5 and ball.position.y < GOAL_H) else "miss"


func _st_record(outcome: String) -> void:
	var bucket := "low" if _st_power < 0.4 else ("mid" if _st_power < 0.75 else "high")
	if not _st_stats.has(bucket):
		_st_stats[bucket] = {"goal": 0, "save": 0, "miss": 0}
	_st_stats[bucket][outcome] += 1


func _st_report() -> void:
	for k in ["low", "mid", "high"]:
		if _st_stats.has(k):
			print("SHOT TEST %s power: %s" % [k, str(_st_stats[k])])


# ================================================================== spawning

func _spawn_teams() -> void:
	for p in players:
		p.queue_free()
	players.clear()
	home.clear()
	away.clear()
	controlled = null
	var opp_strength := match_opp_strength   # league team strength (0.92–1.08)
	var slots: Array = FORMATION_433
	for t in 2:
		var mirror := 1.0 if t == 0 else -1.0
		var list := home if t == 0 else away
		var gk := Player.new()
		add_child(gk)
		gk.setup(self, t, "GK", Vector3((-HALF_L + 1.0) * mirror, 0, 0), HOME_GK if t == 0 else AWAY_GK)
		list.append(gk)
		players.append(gk)
		for s in slots:
			var v: Vector2 = s
			var p := Player.new()
			add_child(p)
			p.setup(self, t, "OUT", Vector3(v.x * mirror, 0, v.y * mirror), HOME_SHIRT if t == 0 else AWAY_SHIRT)
			list.append(p)
			players.append(p)
		for p in list:
			p.speed_mult = 1.0 if t == 0 else opp_strength
	for list in [home, away]:
		for i in list.size():
			list[i].set_number(i + 1)    # keeper 1, then the 4-3-3 in formation order
			list[i].slot = i
	for i in away.size():
		away[i].look_seed = "%s#%d" % [opponent_name, i]
	for i in home.size():
		home[i].look_seed = "%s#%d" % [ClubState.CLUB_NAME, i]
		if club != null and i < club.squad.size():
			home[i].look_seed = club.squad[i]["name"]
			home[i].look_age = int(club.squad[i].get("age", 0))
			home[i].display_name = club.squad[i]["name"]


# ================================================================== world building

func _build_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var psm := ProceduralSkyMaterial.new()
	psm.sky_top_color = Color(0.35, 0.55, 0.85)
	psm.sky_horizon_color = Color(0.75, 0.82, 0.9)
	psm.ground_horizon_color = Color(0.6, 0.65, 0.6)
	sky.sky_material = psm
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.55
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-55.0, -35.0, 0.0)
	sun.light_energy = 1.0
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 80.0
	add_child(sun)

	if light_mode == "old":
		return
	# --- options 1-4 (tunable numbers, Claude's picks) ---
	# 1. AgX tonemapping (same colour handling as the Blender renders) + less flat ambient
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.ambient_light_energy = 0.5
	# 2. ambient occlusion: contact shadows under roofs, between seats, where things meet the ground
	env.ssao_enabled = true
	env.ssao_radius = 1.2
	env.ssao_intensity = 2.2
	env.ssao_power = 1.6
	# 3. lower, warmer sun with softer shadows that reach further
	sun.rotation_degrees = Vector3(-40.0, -35.0, 0.0)
	sun.light_color = Color(1.0, 0.95, 0.86)
	sun.light_energy = 1.7
	sun.shadow_blur = 1.6
	sun.directional_shadow_max_distance = 140.0
	RenderingServer.directional_soft_shadow_filter_set_quality(RenderingServer.SHADOW_QUALITY_SOFT_MEDIUM)
	# 4. grass colour is handled in _build_pitch (less neon)
	if light_mode != "fancy":
		return
	# --- option 5: global illumination, glow, distance haze ---
	env.sdfgi_enabled = true
	env.sdfgi_use_occlusion = true
	env.glow_enabled = true
	env.glow_intensity = 0.4
	env.glow_bloom = 0.05
	# depth fog (Marcel, 2026-11-07: the exponential fog made a haze over everything when zoomed out):
	# nothing up to FOG_BEGIN, then builds up to the horizon
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_DEPTH
	env.fog_light_color = Color(0.75, 0.82, 0.9)
	env.fog_density = 1.0
	env.fog_depth_begin = FOG_BEGIN
	env.fog_depth_end = FOG_END
	env.fog_depth_curve = 1.6
	env.fog_sky_affect = 0.0


const FOG_BEGIN := 120.0   # metres (tunable)
const FOG_END := 400.0


# grass texture (GDD §10j, 2026-11-08): B_clumpy, world-space triplanar so it runs on across the stripe boxes.
# GRASS_TINT_MODE (Marcel wanted to compare both):
#   "match"    = tint compensated so the pitch averages the old flat colours, with blade detail on top
#   "multiply" = old colours used as-is as tint -> texture x colour, a much darker pitch
const GRASS_TINT_MODE := "match"
const GRASS_TILE_M := 5.0   # metres per texture repeat (tunable)
# average colour of grass_B_clumpy_albedo.png in linear space (used by "match")
const GRASS_TEX_MEAN_LINEAR := Color(0.0878, 0.2688, 0.047)
var _grass_albedo: Texture2D
var _grass_normal: Texture2D


func _grass_mat(color: Color) -> StandardMaterial3D:
	if _grass_albedo == null:
		_grass_albedo = load("res://assets/textures/pitch/grass_B_clumpy_albedo.png")
		_grass_normal = load("res://assets/textures/pitch/grass_B_clumpy_normal.png")
	var m := Util.mat(color)
	if GRASS_TINT_MODE == "match":
		m.albedo_color = (color.srgb_to_linear() / GRASS_TEX_MEAN_LINEAR).linear_to_srgb()
	m.albedo_texture = _grass_albedo
	m.normal_enabled = true
	m.normal_texture = _grass_normal
	m.uv1_triplanar = true
	m.uv1_world_triplanar = true
	m.uv1_scale = Vector3.ONE / GRASS_TILE_M
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	return m


func _build_pitch() -> void:
	var root := Node3D.new()
	root.name = "Pitch"
	add_child(root)
	# surrounding grass
	var surround := Color(0.3, 0.4, 0.2) if light_mode == "old" else Color(0.3, 0.4, 0.21)
	var sb := Util.box(root, Vector3(320, 0.1, 240), Vector3(0, -0.06, 0), surround, false)
	sb.material_override = _grass_mat(surround)
	# striped pitch (+ a few metres of run-off)
	var stripes := 14
	var w := (HALF_L * 2.0 + 8.0) / stripes
	for i in stripes:
		var c := Color(0.22, 0.5, 0.2) if i % 2 == 0 else Color(0.19, 0.44, 0.17)
		if light_mode != "old":
			c = Color(0.25, 0.48, 0.2) if i % 2 == 0 else Color(0.21, 0.42, 0.17)  # 4. less neon
		var sm := Util.box(root, Vector3(w, 0.02, HALF_W * 2.0 + 8.0), Vector3(-HALF_L - 4.0 + w * (i + 0.5), 0.0, 0), c, false)
		sm.material_override = _grass_mat(c)
	var white := Color(0.95, 0.95, 0.95)
	var ly := 0.015
	# touchlines, goal lines, halfway line
	_line(root, Vector3(-HALF_L, ly, -HALF_W), Vector3(HALF_L, ly, -HALF_W), white)
	_line(root, Vector3(-HALF_L, ly, HALF_W), Vector3(HALF_L, ly, HALF_W), white)
	_line(root, Vector3(-HALF_L, ly, -HALF_W), Vector3(-HALF_L, ly, HALF_W), white)
	_line(root, Vector3(HALF_L, ly, -HALF_W), Vector3(HALF_L, ly, HALF_W), white)
	_line(root, Vector3(0, ly, -HALF_W), Vector3(0, ly, HALF_W), white)
	_circle(root, Vector3(0, ly, 0), 9.15, white)
	Util.cylinder(root, 0.2, 0.2, 0.01, Vector3(0, ly, 0), white)
	for s in [-1.0, 1.0]:
		var sx: float = s
		var gl := sx * HALF_L
		# penalty area
		var pa := sx * (HALF_L - BOX_DEPTH)
		_line(root, Vector3(pa, ly, -BOX_HALF_W), Vector3(pa, ly, BOX_HALF_W), white)
		_line(root, Vector3(gl, ly, -BOX_HALF_W), Vector3(pa, ly, -BOX_HALF_W), white)
		_line(root, Vector3(gl, ly, BOX_HALF_W), Vector3(pa, ly, BOX_HALF_W), white)
		# goal area
		var ga := sx * (HALF_L - GOAL_AREA_DEPTH)
		_line(root, Vector3(ga, ly, -GOAL_AREA_HALF_W), Vector3(ga, ly, GOAL_AREA_HALF_W), white)
		_line(root, Vector3(gl, ly, -GOAL_AREA_HALF_W), Vector3(ga, ly, -GOAL_AREA_HALF_W), white)
		_line(root, Vector3(gl, ly, GOAL_AREA_HALF_W), Vector3(ga, ly, GOAL_AREA_HALF_W), white)
		# penalty spot
		Util.cylinder(root, 0.15, 0.15, 0.01, Vector3(sx * (HALF_L - 11.0), ly, 0), white)
		# corner flags
		for t in [-1.0, 1.0]:
			var sz: float = t
			Util.cylinder(root, 0.03, 0.03, 1.5, Vector3(gl, 0.75, sz * HALF_W), Color(0.9, 0.9, 0.9), 6)
			Util.box(root, Vector3(0.02, 0.3, 0.4), Vector3(gl, 1.35, sz * HALF_W - sz * 0.2), Color(1.0, 0.85, 0.1))


func _line(parent: Node, a: Vector3, b: Vector3, color: Color) -> void:
	var d := b - a
	var len := d.length()
	var size := Vector3(0.12, 0.01, len) if absf(d.z) > absf(d.x) else Vector3(len, 0.01, 0.12)
	Util.box(parent, size, (a + b) * 0.5, color, false)


func _circle(parent: Node, center: Vector3, radius: float, color: Color) -> void:
	var mi := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = radius - 0.06
	tm.outer_radius = radius + 0.06
	tm.rings = 64
	tm.ring_segments = 4
	mi.mesh = tm
	mi.material_override = Util.mat(color)
	mi.scale = Vector3(1, 0.05, 1)
	mi.position = center
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)


func _build_goals() -> void:
	var white := Color(0.97, 0.97, 0.97)
	var net := Color(1, 1, 1, 0.22)
	for s in [-1.0, 1.0]:
		var sx: float = s
		var root := Node3D.new()
		add_child(root)
		var gx := sx * HALF_L
		var half := GOAL_W * 0.5
		Util.cylinder(root, 0.07, 0.07, GOAL_H, Vector3(gx, GOAL_H * 0.5, -half), white)
		Util.cylinder(root, 0.07, 0.07, GOAL_H, Vector3(gx, GOAL_H * 0.5, half), white)
		Util.box(root, Vector3(0.14, 0.14, GOAL_W + 0.14), Vector3(gx, GOAL_H, 0), white)
		var bx := gx + sx * GOAL_DEPTH
		Util.box(root, Vector3(0.03, GOAL_H, GOAL_W), Vector3(bx, GOAL_H * 0.5, 0), net, false)
		Util.box(root, Vector3(GOAL_DEPTH, 0.03, GOAL_W), Vector3(gx + sx * GOAL_DEPTH * 0.5, GOAL_H, 0), net, false)
		Util.box(root, Vector3(GOAL_DEPTH, GOAL_H, 0.03), Vector3(gx + sx * GOAL_DEPTH * 0.5, GOAL_H * 0.5, -half), net, false)
		Util.box(root, Vector3(GOAL_DEPTH, GOAL_H, 0.03), Vector3(gx + sx * GOAL_DEPTH * 0.5, GOAL_H * 0.5, half), net, false)


func _build_test() -> void:
	# dev: build bleachers on a section with chairs (demolition), rush on an empty one, rows on top
	var c := ClubState.new_game()
	c.money = 99999
	c.place("chair", 2 * ClubState.SPOTS_PER_SECTION)          # section 2 gets a chair
	var seats0 := c.seats()
	print("BUILD start now %.1f seats %d" % [c.now(), seats0])
	print("BUILD bleachers on sec 2 (chairs): ", c.place("bleachers", 2), " weeks ", c.build_weeks("bleachers", 3), " chair gone: ", not c.slots.has("10"))
	print("BUILD rush on sec 3: ", c.place("bleachers_rush", 3), " cost ", c.build_cost("bleachers_rush"), " finish ", c.build_of(3)["finish"])
	print("BUILD chair on building sec 2 refused: ", not c.can_place("chair", 11), " rows refused while building: ", not c.can_build("rows", 2))
	print("BUILD seats while building %d" % c.seats())
	c.league.play_round(1, 0)
	print("BUILD after 1 round now %.1f done %d seats %d" % [c.now(), c.complete_builds().size(), c.seats()])
	while c.now() < 3.0:
		c.league.play_round(1, 0)
	print("BUILD now %.1f done %d sections %s seats %d" % [c.now(), c.complete_builds().size(), str(c.sections), c.seats()])
	print("BUILD rows on 2: ", c.place("rows", 2), " ready ", c.ready_label(c.build_of(2)))
	var back := ClubState.from_dict(JSON.parse_string(JSON.stringify(c.to_dict())))
	print("BUILD roundtrip sections %s builds %d" % [str(back.sections), back.builds.size()])


func _league_test() -> void:
	# dev: check fixtures (balance, returns, weeks) and play a whole season with random scores
	var lg = LeagueScript.create("Test FC")
	var homes := {}
	var first_half_pairs := {}
	var ok_pairs := true
	for r in lg.rounds.size():
		for m in lg.rounds[r]["matches"]:
			var key := "%d-%d" % [mini(m[0], m[1]), maxi(m[0], m[1])]
			if r < 19:
				if first_half_pairs.has(key):
					ok_pairs = false
				first_half_pairs[key] = m
				homes[m[0]] = homes.get(m[0], 0) + 1
			else:
				var f: Array = first_half_pairs.get(key, [])
				if f.is_empty() or f[0] != m[1]:
					ok_pairs = false
	var weeks: Array = lg.rounds.map(func(rd): return rd["week"])
	var per_week := {}
	for w in weeks:
		per_week[w] = per_week.get(w, 0) + 1
	var doubles := per_week.values().filter(func(c): return c == 2).size()
	print("LEAGUE rounds %d pairs-ok %s first-half homes %s..%s last week %d doubles %d empty weeks %d" % [
		lg.rounds.size(), ok_pairs, homes.values().min(), homes.values().max(), weeks[-1], doubles, LeagueScript.SEASON_WEEKS - per_week.size()])
	var you_home := 0
	while not lg.season_over():
		var fx: Dictionary = lg.next_fixture()
		if fx["home"]:
			you_home += 1
		lg.play_round(randi_range(0, 3), randi_range(0, 3))
	var t: Array = lg.table()
	print("LEAGUE season done: you played %d home; champion %s %d pts; you %d" % [you_home, t[0]["name"], t[0]["pts"], lg.position_of(0)])
	lg.start_new_season()
	var back = LeagueScript.from_dict(JSON.parse_string(JSON.stringify(lg.to_dict())))
	print("LEAGUE season %d round %d next %s last finish %d" % [back.season, back.round_idx, str(back.next_fixture()), back.last_finish])


func _build_scenery() -> void:
	# a few low-poly trees and the club's entire "main stand": one bench
	var root := Node3D.new()
	add_child(root)
	var spots := [Vector3(-28, 0, -20), Vector3(-17, 0, -22), Vector3(-4, 0, -24), Vector3(12, 0, -21),
		Vector3(26, 0, -19), Vector3(30, 0, 4), Vector3(-31, 0, 8), Vector3(-25, 0, 22), Vector3(22, 0, 23)]
	for sp in spots:
		var p: Vector3 = sp
		p = Vector3(p.x * SCALE_X, 0, p.z * SCALE_Z)
		var sc := randf_range(0.8, 1.3)
		Util.cylinder(root, 0.25 * sc, 0.3 * sc, 1.6 * sc, p + Vector3(0, 0.8 * sc, 0), Color(0.4, 0.27, 0.15), 6)
		Util.cylinder(root, 0.0, 1.8 * sc, 3.2 * sc, p + Vector3(0, 3.0 * sc, 0), Color(0.2, 0.45, 0.2), 7)
	# seating is bought by the player now (see Grounds)


func _build_camera() -> void:
	camera = Camera3D.new()
	camera.fov = 48.0
	add_child(camera)
	camera.make_current()
	cam_target = Vector3.ZERO
	_place_camera()




func _update_camera(delta: float) -> void:
	if state == "penalties" or (state == "fulltime" and not pens.is_empty()):
		_set_stand_clip(false)
		# behind the penalty taker, looking at the goal
		var gx := HALF_L
		camera.position = camera.position.lerp(Vector3(gx - PEN_SPOT - 9.0, 4.6, 0.0) if mode == "match" else camera.position, clampf(delta * 3.0, 0.0, 1.0))
		camera.look_at(Vector3(gx, 1.0, 0.0), Vector3.UP)
		return
	# look ahead towards the goal the ball carrier is attacking
	var lead := 0.0
	var holder := ball.owner_player
	if holder != null:
		lead = holder.attack_dir * 7.0
	else:
		lead = clampf(ball.vel.x * 0.25, -4.0, 4.0)
	# follow the ball, pulled a bit towards your player, and track sideways too so the near touchline stays in view
	var focus := ball.position
	if controlled != null and not autoplay:
		focus = focus.lerp(controlled.position, 0.3)
	var want := Vector3(clampf(focus.x + lead, -HALF_L + 8.0, HALF_L - 8.0), 0, clampf(focus.z * 0.9, -HALF_W + 4.0, HALF_W - 2.0))
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--cam-focus="):
			# dev: point the match camera at x,z (screenshots of the stands near the camera)
			var v := arg.trim_prefix("--cam-focus=").split(",")
			want = Vector3(float(v[0]), 0, float(v[1]))
	cam_target = cam_target.lerp(want, clampf(delta * 2.5, 0.0, 1.0))
	_place_camera()


var match_zoom := 1.0   # mouse wheel during a match


func _place_camera() -> void:
	camera.position = cam_target + Vector3(0, 25.0, 21.0) * match_zoom
	camera.look_at(cam_target + Vector3(0, 0, -1.0), Vector3.UP)
	_set_stand_clip(true)


## Stands on the West (camera) side: hide what sticks up above the camera's sight line to the near
## touchline (Marcel, option B: "only what really blocks the view"). See stand_clip.gdshader.
func _set_stand_clip(on: bool) -> void:
	var touch := HALF_W + 0.3
	if "--clip-test" in OS.get_cmdline_user_args():
		RenderingServer.global_shader_parameter_set("stand_clip", Vector4(touch, 0.4, 1.0, 0.0))   # dev: force a clip in the hub
		return
	var cz := camera.global_position.z if camera != null else 0.0
	if not on or cz <= touch + 1.0:
		RenderingServer.global_shader_parameter_set("stand_clip", Vector4(touch, 0.0, 0.0, 0.0))
		return
	var slope := camera.global_position.y / (cz - touch)
	RenderingServer.global_shader_parameter_set("stand_clip", Vector4(touch, slope, 1.0, 0.25))
	if Engine.get_physics_frames() % 120 == 0 and "--clip-debug" in OS.get_cmdline_user_args():
		print("CLIP ", Vector4(touch, slope, 1.0, 0.25), " cam ", camera.global_position, " get ", RenderingServer.global_shader_parameter_get("stand_clip"))


func _make_ring(inner: float, outer: float, color: Color) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = inner
	tm.outer_radius = outer
	tm.rings = 24
	tm.ring_segments = 4
	mi.mesh = tm
	mi.material_override = Util.mat(color, true)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	return mi


func _build_indicators() -> void:
	ring = _make_ring(0.48, 0.62, Color(1.0, 0.85, 0.1))
	ring.scale = Vector3(1, 0.1, 1)
	pass_ring = _make_ring(0.5, 0.6, Color(1.0, 1.0, 1.0, 0.8))
	pass_ring.scale = Vector3(1, 0.1, 1)

	# aim arrow: a flat bar from the player towards the mouse, grows while charging
	aim_pivot = Node3D.new()
	add_child(aim_pivot)
	aim_arrow = MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.14, 0.02, 1.0)
	aim_arrow.mesh = bm
	aim_mat = Util.mat(Color(1, 1, 1, 0.85), true)
	aim_arrow.material_override = aim_mat
	aim_arrow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	aim_pivot.add_child(aim_arrow)
	var tip := MeshInstance3D.new()
	var pm := PrismMesh.new()
	pm.size = Vector3(0.45, 0.4, 0.02)
	tip.mesh = pm
	tip.material_override = aim_mat
	tip.rotation_degrees = Vector3(90, 0, 0)
	tip.name = "Tip"
	tip.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	aim_pivot.add_child(tip)

	# where the shot will cross the goal line
	goal_marker = _make_ring(0.26, 0.38, Color(1.0, 0.85, 0.1))
	goal_marker.rotation_degrees = Vector3(0, 0, 90)


func _update_indicators() -> void:
	var human := controlled != null and not autoplay and state == "play"
	name_label.visible = controlled != null and not autoplay and mode == "match" and controlled.display_name != "" and state != "penalties"
	if name_label.visible:
		name_label.text = controlled.display_name
		name_label.position = controlled.position + Vector3(0, 2.6, 0)
	ring.visible = human
	pass_ring.visible = false
	aim_pivot.visible = false
	goal_marker.visible = false
	if state == "penalties" and pens.get("human", false) and pens.get("phase", "") == "aim":
		ring.visible = true
		ring.position = Vector3(controlled.position.x, 0.03, controlled.position.z)
		goal_marker.visible = true
		goal_marker.position = Vector3(HALF_L, _pen_height(charge), float(pens["aim_z"]))
		return
	if not human:
		return
	ring.position = Vector3(controlled.position.x, 0.03, controlled.position.z)
	if not controlled.has_ball():
		return

	var aim := Util.flat(aim_point - controlled.position)
	if aim.length() < 0.05:
		return
	# arrow
	var length := 1.6 + (charge * 4.0 if charging else 0.0)
	aim_pivot.visible = true
	aim_pivot.position = Vector3(controlled.position.x, 0.04, controlled.position.z)
	aim_pivot.rotation.y = atan2(aim.x, aim.z)
	aim_arrow.scale = Vector3(1, 1, length)
	aim_arrow.position = Vector3(0, 0, 0.5 + length * 0.5)
	var tip := aim_pivot.get_node("Tip") as Node3D
	tip.position = Vector3(0, 0, 0.5 + length + 0.15)
	aim_mat.albedo_color = Color(1, 1, 1, 0.85) if not charging else Color(1.0, 0.85, 0.1).lerp(Color(1.0, 0.2, 0.1), charge)

	if charging:
		var gp := Vector3.INF if controlled.role == "GK" else goal_aim_point(controlled)
		if gp != Vector3.INF:
			goal_marker.visible = true
			goal_marker.position = Vector3(gp.x, shot_height(charge), gp.z)
	else:
		var mate := _pass_target_in_cone(controlled, aim)
		if mate != null:
			pass_ring.visible = true
			pass_ring.position = Vector3(mate.position.x, 0.03, mate.position.z)
			var off := in_offside_position(mate, controlled.position.x) and controlled.restart_kind not in ["throw-in", "corner", "goal kick"]
			(pass_ring.material_override as StandardMaterial3D).albedo_color = Color(1.0, 0.25, 0.2, 0.9) if off else Color(1, 1, 1, 0.8)


# ================================================================== HUD

func _build_hud() -> void:
	# Clubhouse Noticeboard in-match HUD (GDD §10e, mock-up "In-match HUD"), on a 1920×1080 board
	var layer := CanvasLayer.new()
	hud_layer = layer
	add_child(layer)
	var mm := Minimap.new()
	mm.setup(self)
	layer.add_child(mm.arrows)
	layer.add_child(mm)
	hud_board = Control.new()
	hud_board.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(hud_board)
	get_viewport().size_changed.connect(_fit_hud)
	_fit_hud()

	# score chip (top left)
	var chip := PanelContainer.new()
	var sb := Kit.box(Kit.c("paper"), 3)
	sb.content_margin_left = 18
	sb.content_margin_right = 18
	chip.add_theme_stylebox_override("panel", sb)
	chip.position = Vector2(32, 24)
	chip.custom_minimum_size = Vector2(0, 64)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 14)
	chip.add_child(row)
	hud_crest_l = Kit.icon("crest_home", 32, Kit.c("pen"))
	hud_crest_l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(hud_crest_l)
	hud_team_l = Kit.label("YOU", false, 22, 700, Kit.c("ink"))
	hud_team_l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(hud_team_l)
	var pill := PanelContainer.new()
	var ps := StyleBoxFlat.new()
	ps.bg_color = Kit.c("ink")
	ps.set_corner_radius_all(4)
	ps.content_margin_left = 12
	ps.content_margin_right = 12
	pill.add_theme_stylebox_override("panel", ps)
	pill.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	score_label = Kit.label("0 – 0", false, 26, 700, Kit.c("paper"))
	pill.add_child(score_label)
	row.add_child(pill)
	hud_team_r = Kit.label("OPP", false, 22, 700, Kit.c("ink"))
	hud_team_r.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(hud_team_r)
	hud_crest_r = Kit.icon("crest_away", 32, Kit.c("ink"))
	hud_crest_r.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(hud_crest_r)
	var div := ColorRect.new()
	div.color = Kit.c("div")
	div.custom_minimum_size = Vector2(1, 36)
	div.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(div)
	hud_half = Kit.label("1st half", false, 16, 600, Kit.c("muted"))
	hud_half.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(hud_half)
	hud_clock = Kit.label("3:00", false, 22, 700, Kit.c("ink"))
	hud_clock.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(hud_clock)
	hud_board.add_child(chip)

	# big messages (GOAL!, HALF TIME, ...) on a sticky note
	var note := Kit.sheet("note", 440, -4.0, Vector4(24, 18, 24, 16), 0)
	hud_msg_note = note["root"]
	msg_label = Kit.label("", true, 60, 700, Kit.c("primary"), true)
	msg_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	(note["body"] as VBoxContainer).add_child(msg_label)
	Kit.tape(hud_msg_note, Vector2(172, -14), 3)
	hud_board.add_child(hud_msg_note)
	hud_msg_note.anchor_left = 0.5
	hud_msg_note.anchor_right = 0.5
	hud_msg_note.offset_left = -220
	hud_msg_note.offset_right = 220
	hud_msg_note.offset_top = 150

	# toasts (SAVE!, PARRIED!, ...) as a small paper tag
	var tt := PanelContainer.new()
	var ts := Kit.box(Kit.c("paper"), 3)
	ts.content_margin_left = 16
	ts.content_margin_right = 16
	ts.content_margin_top = 4
	ts.content_margin_bottom = 4
	tt.add_theme_stylebox_override("panel", ts)
	toast_label = Kit.label("", true, 28, 700, Kit.c("pen"))
	tt.add_child(toast_label)
	hud_toast = tt
	hud_board.add_child(tt)
	tt.anchor_left = 0.5
	tt.anchor_right = 0.5
	tt.grow_horizontal = Control.GROW_DIRECTION_BOTH
	tt.offset_top = 104
	tt.rotation_degrees = 1.0

	# controls hint (bottom left), real bindings only (dev keys are listed in the F1 panel)
	var hp := PanelContainer.new()
	var hs := Kit.box(Kit.c("paper"), 3)
	hs.content_margin_left = 14
	hs.content_margin_right = 14
	hs.content_margin_top = 10
	hs.content_margin_bottom = 10
	hp.add_theme_stylebox_override("panel", hs)
	hint_label = Kit.label("", false, 14, 500, Kit.c("ink"))
	hp.add_child(hint_label)
	_update_hint()
	hud_board.add_child(hp)
	hp.anchor_top = 1.0
	hp.anchor_bottom = 1.0
	hp.grow_vertical = Control.GROW_DIRECTION_BEGIN
	hp.offset_left = 32
	hp.offset_bottom = -24

	# shot power
	var pw := PanelContainer.new()
	var pws := Kit.box(Kit.c("paper"), 3)
	pws.content_margin_left = 18
	pws.content_margin_right = 18
	pws.content_margin_top = 12
	pws.content_margin_bottom = 12
	pw.add_theme_stylebox_override("panel", pws)
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 8)
	var ph := HBoxContainer.new()
	var pl := Kit.caps("Shot power", Kit.c("muted"))
	pl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ph.add_child(pl)
	hud_power_pct = Kit.label("0%", false, 16, 700, Kit.c("ink"))
	ph.add_child(hud_power_pct)
	pv.add_child(ph)
	hud_power_bar = Kit.progress(0.0, false)
	pv.add_child(hud_power_bar)
	pw.add_child(pv)
	hud_power = pw
	hud_board.add_child(pw)
	pw.anchor_left = 0.5
	pw.anchor_right = 0.5
	pw.anchor_top = 1.0
	pw.anchor_bottom = 1.0
	pw.offset_left = -210
	pw.offset_right = 210
	pw.offset_top = -96 - 64
	pw.offset_bottom = -96


## Dark/light switch: rebuild the HUD with the new colours.
func rebuild_hud() -> void:
	var was := hud_layer.visible
	hud_layer.queue_free()
	_build_hud()
	hud_layer.visible = was


func _fit_hud() -> void:
	var vp := get_viewport().get_visible_rect().size
	var sc := minf(vp.x / Kit.DESIGN.x, vp.y / Kit.DESIGN.y)
	hud_board.scale = Vector2(sc, sc)
	hud_board.size = vp / sc


func _font(size: int) -> LabelSettings:
	var ls := LabelSettings.new()
	ls.font_size = size
	ls.outline_size = maxi(4, size / 6)
	ls.outline_color = Color(0, 0, 0, 0.85)
	return ls


static func _abbr(n: String) -> String:
	if n == ClubState.CLUB_NAME:
		return "YOU"
	return n.substr(0, 3).to_upper()


func _update_hud() -> void:
	var us_left := match_home
	hud_team_l.text = _abbr(ClubState.CLUB_NAME if us_left else opponent_name)
	hud_team_r.text = _abbr(opponent_name if us_left else ClubState.CLUB_NAME)
	hud_crest_l.texture = Kit.icon_tex("crest_home" if us_left else "crest_away")
	hud_crest_r.texture = Kit.icon_tex("crest_away" if us_left else "crest_home")
	hud_crest_l.modulate = Kit.c("pen") if us_left else Kit.c("ink")
	hud_crest_r.modulate = Kit.c("ink") if us_left else Kit.c("pen")
	var l: int = score[0] if us_left else score[1]
	var r: int = score[1] if us_left else score[0]
	score_label.text = "%d – %d" % [l, r]
	var t := int(ceil(time_left))
	hud_half.text = ["1st half", "2nd half", "Extra time", "Extra time"][clampi(half - 1, 0, 3)]
	hud_clock.text = "%d:%02d" % [t / 60, t % 60]
	if not pens.is_empty():
		var pg: Array = pens["goals"]
		hud_half.text = "Penalties"
		hud_clock.text = "%d – %d" % [pg[0] if us_left else pg[1], pg[1] if us_left else pg[0]]
	hud_msg_note.visible = msg_label.text != ""
	hud_toast.visible = toast_timer > 0.0
	hud_power.visible = charging
	hud_power_bar.value = 100.0 * charge
	hud_power_pct.text = "%d%%" % int(round(100.0 * charge))


func _clock_text() -> String:
	var t := int(ceil(time_left))
	return "%s %d:%02d" % [["1st", "2nd", "ET1", "ET2"][clampi(half - 1, 0, 3)], t / 60, t % 60]
