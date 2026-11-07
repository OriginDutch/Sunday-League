class_name Main
extends Node3D
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

# ---- difficulty / feel knobs ------------------------------------------------
const HUMAN_SPEED_BONUS := 1.1         # your player runs a bit faster than the AI
const HUMAN_DRIBBLE_SPEED := 0.92      # speed multiplier while you have the ball
const AI_DRIBBLE_SPEED := 0.88          # same for AI ball carriers
const HUMAN_PROTECT := 0.9             # seconds you can't be robbed after receiving
const AI_STEAL_TIME := 0.8            # AI vs AI: pressing time needed to nick the ball
const AI_STEAL_TIME_VS_HUMAN := 1.2    # AI pressing YOU needs this long
const HUMAN_STEAL_TIME := 0.3          # you pressing the AI carrier
const HUMAN_TACKLE_SUCCESS := 0.85
const AI_TACKLE_SUCCESS := 0.55
const AI_TACKLE_RATE_VS_HUMAN := 0.7   # tackle attempts per second when close to you
const AI_TACKLE_RATE := 0.5            # AI vs AI tackle attempts per second when close
const AI_TACKLE_START_RANGE := 1.4     # AI only lunges when this close to the ball
const AI_TACKLE_LUNGE := 7.0           # lunge speed (m/s) for 0.35 s
const HUMAN_TACKLE_LUNGE := 10.0
const AI_JOCKEY_DISTANCE := 1.6        # AI presser keeps this gap when you have the ball
const AI_JOCKEY_DISTANCE_AI := 1.1     # ...and this gap against an AI carrier
const MARK_DISTANCE := 2.2             # markers stand this far goal-side of their man
const COVER_DISTANCE := 4.5            # second defender covers this far goal-side of the ball carrier
const BLOCK_LINE_FACTOR := 0.5         # back line depth = ball depth from own goal x this
const BLOCK_MIN_DEPTH := 8.0           # back line never deeper than this (m from own goal line)
const BLOCK_MAX_DEPTH := 36.0          # ...nor higher than this
const BLOCK_FORM_BACK := 14.5          # formation depth of the back four
const STEP_OUT_DISTANCE := 2.5         # zone owner steps out to this distance from the ball carrier
const STEP_OUT_RADIUS := 10.0          # ...when the carrier is within this distance of his zone
const INTERCEPT_RANGE := 5.0           # AI goes for a pass passing within this distance
const PASS_LEAD := 0.7                 # how much of the receiver's run the pass leads
const LOB_PASS_DISTANCE := 30.0        # passes longer than this go through the air
const LOOSE_SWITCH_MARGIN := 5.0       # auto-switch on a loose ball only if a teammate is this much closer
const BEATEN_MARGIN := 3.0             # ball carrier this far past you -> switch to a goal-side teammate
const Q_CYCLE_WINDOW := 1.2            # press Q again within this time to cycle to the next nearest
const THROW_IN_DISTANCE := 3.0         # opponents keep this distance at a throw-in (9.15 m otherwise)
const AI_SHOOT_RANGE := 25.0
const AI_SHOT_ERROR := 1.6             # 1.0 = as accurate as you
const KEEPER_REACTION := [0.14, 0.28]  # seconds before the keeper reacts to a shot: [yours, theirs]
const KEEPER_DIVE_SPEED := [8.5, 7.0]
const KEEPER_REACH := [0.9, 0.8]
const AWAY_KEEPER_PARRY := 0.6         # chance their keeper parries instead of catching a hard shot

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
var stats := {"shots": [0, 0], "steals": [0, 0], "saves": [0, 0], "offside": [0, 0], "corners": [0, 0], "throw-ins": [0, 0], "goal kicks": [0, 0], "passes": [0, 0], "intercepts": [0, 0], "bailouts": [0, 0]}  # printed at full time (dev)

var camera: Camera3D
var cam_target := Vector3.ZERO
var aim_point := Vector3.ZERO
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
var power_bg: ColorRect
var power_fill: ColorRect


# dev: lighting test (GDD §10g). "old" = current default, "new" = options 1-4, "fancy" = 1-5
var light_mode := "old"


func _ready() -> void:
	randomize()
	var args := OS.get_cmdline_user_args()
	autoplay = "--autoplay" in args or "--shot-test" in args
	_ui_demo = "--ui-demo" in args
	if "--fancy-light" in args:
		light_mode = "fancy"
	elif "--new-light" in args:
		light_mode = "new"
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
	name_label.font_size = 64
	name_label.outline_size = 12
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
		start_friendly()
		if "--shot-test" in args:
			_shot_test_begin()
	else:
		_enter_hub()
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
			hub.root.visible = false
			_hub_camera()
	if "--shed" in args:
		# dev: preview the first 3D asset (The Shed, one 11.5 m section) on the north side
		var shed: Node3D = load("res://assets/models/the_shed.glb").instantiate()
		shed.position = Vector3(0, 0, -(HALF_W + 3.0))
		add_child(shed)
	if "--quick-friendly" in args:
		# dev: play a 2x3s friendly with nobody at the controls, then show the summary
		start_friendly()
		time_left = 3.0
		_quick = true


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
	if sfx != null:
		sfx.set_murmur(false)
	_hub_camera()


func start_friendly() -> void:
	opponent_name = Names.opponent()
	placing_item = ""
	grounds.show_markers(false)
	_spawn_teams()
	ball.visible = true
	score = [0, 0]
	half = 1
	time_left = HALF_SECONDS
	for k in stats:
		stats[k] = [0, 0]
	grounds.spawn_crowd(club.fans)
	sfx.crowd_level = clampf(club.fans / 100.0, 0.05, 1.0)
	sfx.set_murmur(true)
	mode = "match"
	hub.show_hub(false)
	hub.hide_summary()
	hud_layer.visible = true
	_start_kickoff(first_kickoff_team)


func back_to_hub() -> void:
	_enter_hub()


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
	hub.refresh()


# hub camera: WASD / arrows to pan, mouse wheel to zoom
var hub_focus := Vector3(8.0, 0, -HALF_W - 2.0)
var hub_zoom := 1.0


var hub_yaw := 0.0   # orbit angle around the focus point


func _hub_camera() -> void:
	camera.position = hub_focus + (Vector3(0, 26.0, 26.0) * hub_zoom).rotated(Vector3.UP, hub_yaw)
	camera.look_at(hub_focus, Vector3.UP)


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
		hub_focus += pan.normalized() * 30.0 * hub_zoom * delta
		hub_focus.x = clampf(hub_focus.x, -HALF_L, HALF_L)
		hub_focus.z = clampf(hub_focus.z, -HALF_W - 6.0, HALF_W + 6.0)
	_hub_camera()
	if placing_item == "":
		return
	var p := _mouse_ground_point()
	hover_slot = grounds.nearest_free_slot(p, placing_item, 3.0)
	grounds.show_markers(true, placing_item, hover_slot)


func _hub_click() -> void:
	if placing_item == "" or hover_slot < 0:
		return
	if club.place(placing_item, hover_slot):
		grounds.rebuild_furniture()
		club.save()
	_cancel_placing()


func _hub_test() -> void:
	# dev: exercise the club flow without a mouse
	print("HUB TEST start: money %d fans %d squad %d" % [club.money, club.fans, club.squad.size()])
	while club.squad.size() < ClubState.SQUAD_SIZE:
		club.recruit(0)
	club.money = 200
	print("placed bench: ", club.place("bench", 3), " chairs x5 on slot 25: ", [club.place("chair", 25), club.place("chair", 25), club.place("chair", 25), club.place("chair", 25), club.place("chair", 25)], " bench on chairs: ", club.place("bench", 25), " seats ", club.seats(), " slots ", club.slots)
	var legacy := ClubState.from_dict({"slots": {"7": "chair"}})
	print("legacy chair -> ", legacy.slots, " seats ", legacy.seats())
	grounds.rebuild_furniture()
	var summary := club.apply_match(2, 1, 5)
	print("SUMMARY ", summary)
	var d := club.to_dict()
	var back := ClubState.from_dict(JSON.parse_string(JSON.stringify(d)))
	print("ROUNDTRIP money %d fans %d slots %s squad %d" % [back.money, back.fans, str(back.slots), back.squad.size()])
	grounds.spawn_crowd(club.fans + 10)
	print("CROWD fans spawned: %d (seats %d)" % [grounds.fans.size(), club.seats()])


# ================================================================== loop

func _physics_process(delta: float) -> void:
	if mode != "match":
		if mode == "hub":
			_hub_process(delta)
		_debug_screenshot(delta)
		return
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
	_update_camera(delta)
	_update_hud()
	_update_indicators()
	_debug_screenshot(delta)


# dev helper: `-- --autoplay --shot=/path/shot.png` saves a screenshot after a few seconds and quits
var _shot_timer := 0.0


func _debug_screenshot(delta: float) -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--shot="):
			_shot_timer += delta
			if _shot_timer > 4.0:
				var img := get_viewport().get_texture().get_image()
				img.save_png(arg.substr(7))
				get_tree().quit()
			return


# dev helper: `-- --ui-demo --shot=/path.png` fakes a human charging a shot, to screenshot the aim UI
var _ui_demo := false


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
	sfx.whistle_times(2 if half == 1 else 3)
	if half == 1:
		state = "halftime"
		state_timer = 2.5
		msg_label.text = "HALF TIME  %d - %d" % [score[0], score[1]]
		ball.owner_player = null
		charging = false
		print("HALF TIME %d - %d" % [score[0], score[1]])
	else:
		_full_time()


var _quick := false


func _second_half() -> void:
	half = 2
	time_left = 3.0 if _quick else HALF_SECONDS
	# switch sides
	for p in players:
		p.attack_dir = -p.attack_dir
		p.home_pos = Vector3(-p.home_pos.x, 0, -p.home_pos.z)
	_start_kickoff(1 - first_kickoff_team)


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
	print("[%s] GOAL team %d  -> %d - %d" % [_clock_text(), scoring_team, score[0], score[1]])


func _full_time() -> void:
	state = "fulltime"
	msg_label.text = "FULL TIME  %d - %d" % [score[0], score[1]]
	print("FULL TIME %d - %d   %s" % [score[0], score[1], str(stats)])
	if autoplay:
		get_tree().quit()
		return
	# friendly done: pay, grow, autosave, show summary
	var ent: int = score[0] + score[1] + stats["saves"][0] + stats["saves"][1] + stats["steals"][0] + stats["steals"][1]
	var summary := club.apply_match(score[0], score[1], ent)
	club.save()
	print("FRIENDLY DONE -> summary ", summary, " saved to ", ProjectSettings.globalize_path(ClubState.SAVE_PATH))
	mode = "summary"
	name_label.visible = false
	hub.show_summary(summary, opponent_name)


func _restart() -> void:
	score = [0, 0]
	if half == 2:
		for p in players:
			p.attack_dir = -p.attack_dir
			p.home_pos = Vector3(-p.home_pos.x, 0, -p.home_pos.z)
	half = 1
	time_left = HALF_SECONDS
	_start_kickoff(first_kickoff_team)


# ================================================================== human input

func _unhandled_input(event: InputEvent) -> void:
	if mode == "hub":
		if event is InputEventMouseButton and (event as InputEventMouseButton).pressed:
			var mb0 := event as InputEventMouseButton
			if mb0.button_index == MOUSE_BUTTON_WHEEL_UP:
				hub_zoom = clampf(hub_zoom * 0.9, 0.35, 2.6)
			elif mb0.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				hub_zoom = clampf(hub_zoom * 1.1, 0.35, 2.6)
			elif mb0.button_index == MOUSE_BUTTON_LEFT:
				_hub_click()
			elif mb0.button_index == MOUSE_BUTTON_RIGHT:
				_cancel_placing()
		elif event is InputEventKey and (event as InputEventKey).pressed and (event as InputEventKey).keycode == KEY_ESCAPE:
			_cancel_placing()
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
					controlled.start_tackle()
			KEY_Q:
				if state == "play" or state == "restart":
					_manual_switch()
	elif event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_UP:
			match_zoom = clampf(match_zoom * 0.9, 0.5, 1.8)
			return
		if mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			match_zoom = clampf(match_zoom * 1.1, 0.5, 1.8)
			return
		if (state != "play" and state != "restart") or controlled == null:
			return
		if mb.button_index == MOUSE_BUTTON_LEFT and mb.pressed:
			if controlled.has_ball():
				_human_pass()
		elif mb.button_index == MOUSE_BUTTON_RIGHT:
			if mb.pressed and controlled.has_ball():
				charging = true
				charge = 0.0
			elif not mb.pressed and charging:
				charging = false
				if controlled.has_ball():
					_human_shoot()


func _update_human(delta: float) -> void:
	if autoplay:
		return
	switch_cooldown = maxf(0.0, switch_cooldown - delta)
	manual_lock = maxf(0.0, manual_lock - delta)
	q_time += delta
	_auto_switch()
	if controlled == null:
		return
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

	if mv != Vector3.ZERO:
		controlled.desired_move = mv.normalized()
	elif ball.pass_target == controlled:
		# no input while a pass is coming: go and meet it
		controlled.desired_move = Util.flat(ball.position - controlled.position).limit_length(1.0)
	else:
		controlled.desired_move = Vector3.ZERO
	controlled.wants_sprint = Input.is_key_pressed(KEY_SHIFT)

	if charging:
		charge = minf(charge + delta / 0.9, 1.0)
		if not controlled.has_ball():
			charging = false
		else:
			controlled.face_towards(aim_point - controlled.position)


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


func _human_shoot() -> void:
	var p := controlled
	if p.role == "GK" or p.restart_kind == "corner":
		p.long_kick(aim_point, charge)
		return
	if p.restart_kind == "throw-in":
		p.pass_towards(aim_point)
		return
	var gp := goal_aim_point(p)
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


func _pass_target_in_cone(p: Player, aim: Vector3) -> Player:
	if aim.length() < 0.01:
		return null
	var best: Player = null
	var best_score := -INF
	for mate in team_list(p.team):
		if mate == p:
			continue
		var to := Util.flat(mate.position - p.position)
		var d := to.length()
		if d < 1.5 or d > 32.0:
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
var q_cycle: Array[Player] = []
var q_index := 0
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


## Q: nearest teammate to the ball; pressing again quickly cycles to the next nearest.
func _manual_switch() -> void:
	if q_time > Q_CYCLE_WINDOW or q_cycle.is_empty():
		q_cycle.clear()
		for p in home:
			if p.role != "GK" and p != controlled:
				q_cycle.append(p)
		q_cycle.sort_custom(func(a: Player, b: Player) -> bool:
			return Util.flat_dist(a.position, ball.position) < Util.flat_dist(b.position, ball.position))
		q_index = 0
	else:
		q_index = (q_index + 1) % q_cycle.size()
	if q_cycle.is_empty():
		return
	controlled = q_cycle[q_index]
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
		var tackle_reach := 1.2 if opp.is_human else 0.8
		if opp.tackle_timer > 0.0 and d < tackle_reach and holder.protect <= 0.0:
			var success := HUMAN_TACKLE_SUCCESS if opp.is_human else AI_TACKLE_SUCCESS
			if randf() < success:
				_steal(opp, holder)
			else:
				opp.tackle_timer = 0.0
				opp.stun = 0.5
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
			needed = HUMAN_STEAL_TIME
		elif holder.is_human:
			needed = AI_STEAL_TIME_VS_HUMAN
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
		var reach: float = KEEPER_REACH[p.team] if keeper else (0.85 if p.is_human else 0.7)
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
		var parry_chance := AWAY_KEEPER_PARRY if best.team == 1 else 0.35
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
	if Util.flat_dist(_st_keeper.position, ball.position) < KEEPER_REACH[1] and ball.position.y < 2.4:
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
	var opp_strength := randf_range(0.92, 1.08)   # friendlies: some opponents are a bit quicker
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
	for i in home.size():
		if club != null and i < club.squad.size():
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
	env.fog_enabled = true
	env.fog_light_color = Color(0.75, 0.82, 0.9)
	env.fog_density = 0.0025
	env.fog_sky_affect = 0.0


func _build_pitch() -> void:
	var root := Node3D.new()
	root.name = "Pitch"
	add_child(root)
	# surrounding grass
	var surround := Color(0.3, 0.4, 0.2) if light_mode == "old" else Color(0.3, 0.4, 0.21)
	Util.box(root, Vector3(320, 0.1, 240), Vector3(0, -0.06, 0), surround, false)
	# striped pitch (+ a few metres of run-off)
	var stripes := 14
	var w := (HALF_L * 2.0 + 8.0) / stripes
	for i in stripes:
		var c := Color(0.22, 0.5, 0.2) if i % 2 == 0 else Color(0.19, 0.44, 0.17)
		if light_mode != "old":
			c = Color(0.25, 0.48, 0.2) if i % 2 == 0 else Color(0.21, 0.42, 0.17)  # 4. less neon
		Util.box(root, Vector3(w, 0.02, HALF_W * 2.0 + 8.0), Vector3(-HALF_L - 4.0 + w * (i + 0.5), 0.0, 0), c, false)
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
	cam_target = cam_target.lerp(want, clampf(delta * 2.5, 0.0, 1.0))
	_place_camera()


var match_zoom := 1.0   # mouse wheel during a match


func _place_camera() -> void:
	camera.position = cam_target + Vector3(0, 25.0, 21.0) * match_zoom
	camera.look_at(cam_target + Vector3(0, 0, -1.0), Vector3.UP)


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
	name_label.visible = controlled != null and not autoplay and mode == "match" and controlled.display_name != ""
	if name_label.visible:
		name_label.text = controlled.display_name
		name_label.position = controlled.position + Vector3(0, 2.6, 0)
	ring.visible = human
	pass_ring.visible = false
	aim_pivot.visible = false
	goal_marker.visible = false
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
	var layer := CanvasLayer.new()
	hud_layer = layer
	add_child(layer)

	score_label = Label.new()
	score_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	score_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	score_label.offset_left = -450
	score_label.offset_right = 450
	score_label.offset_top = 14
	score_label.label_settings = _font(34)
	layer.add_child(score_label)

	toast_label = Label.new()
	toast_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	toast_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	toast_label.offset_left = -300
	toast_label.offset_right = 300
	toast_label.offset_top = 64
	toast_label.label_settings = _font(30)
	layer.add_child(toast_label)

	msg_label = Label.new()
	msg_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	msg_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	msg_label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	msg_label.label_settings = _font(72)
	layer.add_child(msg_label)

	var hint := Label.new()
	hint.text = "WASD move · Shift sprint · LMB pass (white ring = receiver, red = offside) · hold RMB shoot (aim at the goal) · Space tackle · Q switch · R restart · Esc quit"
	hint.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	hint.offset_left = 14
	hint.offset_top = -34
	hint.label_settings = _font(16)
	layer.add_child(hint)

	var mm := Minimap.new()
	mm.setup(self)
	layer.add_child(mm.arrows)
	layer.add_child(mm)

	power_bg = ColorRect.new()
	power_bg.color = Color(0, 0, 0, 0.5)
	power_bg.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	power_bg.offset_left = -150
	power_bg.offset_right = 150
	power_bg.offset_top = -80
	power_bg.offset_bottom = -60
	layer.add_child(power_bg)
	power_fill = ColorRect.new()
	power_fill.color = Color(1.0, 0.75, 0.1)
	power_fill.position = Vector2(3, 3)
	power_fill.size = Vector2(0, 14)
	power_bg.add_child(power_fill)


func _font(size: int) -> LabelSettings:
	var ls := LabelSettings.new()
	ls.font_size = size
	ls.outline_size = maxi(4, size / 6)
	ls.outline_color = Color(0, 0, 0, 0.85)
	return ls


func _update_hud() -> void:
	score_label.text = "HOME  %d - %d  %s     %s" % [score[0], score[1], opponent_name.to_upper(), _clock_text()]
	toast_label.visible = toast_timer > 0.0
	power_bg.visible = charging
	power_fill.size = Vector2(294.0 * charge, 14)
	power_fill.color = Color(1.0, 0.75, 0.1).lerp(Color(1.0, 0.2, 0.1), charge)


func _clock_text() -> String:
	var t := int(ceil(time_left))
	return "%s %d:%02d" % ["1st" if half == 1 else "2nd", t / 60, t % 60]
