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
const AI_DRIBBLE_SPEED := 0.8          # same for AI ball carriers
const HUMAN_PROTECT := 0.9             # seconds you can't be robbed after receiving
const AI_STEAL_TIME := 0.45            # AI vs AI: pressing time needed to nick the ball
const AI_STEAL_TIME_VS_HUMAN := 1.2    # AI pressing YOU needs this long
const HUMAN_STEAL_TIME := 0.3          # you pressing the AI carrier
const HUMAN_TACKLE_SUCCESS := 0.85
const AI_TACKLE_SUCCESS := 0.55
const AI_TACKLE_RATE_VS_HUMAN := 0.45  # tackle attempts per second when close to you
const AI_SHOOT_RANGE := 18.0
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
var stats := {"shots": [0, 0], "steals": [0, 0], "saves": [0, 0], "offside": [0, 0], "corners": [0, 0], "throw-ins": [0, 0], "goal kicks": [0, 0]}  # printed at full time (dev)

var camera: Camera3D
var cam_target := Vector3.ZERO
var aim_point := Vector3.ZERO
var charging := false
var charge := 0.0
var switch_cooldown := 0.0

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


func _ready() -> void:
	randomize()
	var args := OS.get_cmdline_user_args()
	autoplay = "--autoplay" in args or "--shot-test" in args
	_ui_demo = "--ui-demo" in args
	_build_environment()
	_build_pitch()
	_build_goals()
	_build_scenery()
	ball = Ball.new()
	add_child(ball)
	ball.setup(self)
	_spawn_teams()
	_build_camera()
	_build_hud()
	_build_indicators()
	_start_kickoff(0)
	if "--shot-test" in args:
		_shot_test_begin()


# ================================================================== loop

func _physics_process(delta: float) -> void:
	match state:
		"kickoff":
			state_timer -= delta
			if state_timer <= 0.0:
				state = "play"
				msg_label.text = ""
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
		controlled.position = Vector3(12, 0, 15)
		_give_ball(controlled)
		toast("SAVE!")
	charging = true
	charge = 0.65


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
		# opponents back off
		if p.team != t and Util.flat_dist(p.position, spot) < 9.15:
			var away_dir := Util.flat(p.position - spot)
			if away_dir.length() < 0.1:
				away_dir = Vector3(-p.attack_dir, 0, 0)
			p.position = spot + away_dir.normalized() * 9.2
	taker.position = spot
	taker.vel = Vector3.ZERO
	taker.face_towards(Vector3(-spot.x * 0.3, 0, -spot.z))
	_give_ball(taker)
	taker.restart_kind = kind
	taker.protect = 999.0
	taker.has_ball_time = 0.0
	toast(kind.to_upper())


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


# ---- halves -------------------------------------------------------------------

func _end_of_half() -> void:
	if half == 1:
		state = "halftime"
		state_timer = 2.5
		msg_label.text = "HALF TIME  %d - %d" % [score[0], score[1]]
		ball.owner_player = null
		charging = false
		print("HALF TIME %d - %d" % [score[0], score[1]])
	else:
		_full_time()


func _second_half() -> void:
	half = 2
	time_left = HALF_SECONDS
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
	ball.owner_player = null
	charging = false
	var scorer := ball.last_touch
	var own_goal := scorer != null and scorer.team != scoring_team
	msg_label.text = "OWN GOAL!" if own_goal else "GOAL!"
	print("[%s] GOAL team %d  -> %d - %d" % [_clock_text(), scoring_team, score[0], score[1]])


func _full_time() -> void:
	state = "fulltime"
	msg_label.text = "FULL TIME  %d - %d\npress R to play again" % [score[0], score[1]]
	print("FULL TIME %d - %d   %s" % [score[0], score[1], str(stats)])
	if autoplay:
		get_tree().quit()


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
				if state == "play":
					_manual_switch()
	elif event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
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


func _auto_switch() -> void:
	var holder := ball.owner_player
	if holder != null and holder.team == 0:
		controlled = holder   # includes your keeper once he has the ball
		return
	var pt := ball.pass_target
	if pt != null and pt.team == 0 and pt.role != "GK":
		controlled = pt
		return
	if controlled != null and controlled.role == "GK":
		# keeper only stays yours while he holds the ball
		controlled = _nearest_to_ball(home, true)
		switch_cooldown = 0.3
		return
	if switch_cooldown > 0.0 or controlled == null:
		return
	var best := _nearest_to_ball(home, true)
	if best != null and best != controlled:
		var target := ball.position + ball.vel * 0.2
		if Util.flat_dist(best.position, target) < Util.flat_dist(controlled.position, target) - 1.5:
			controlled = best
			switch_cooldown = 0.4


func _manual_switch() -> void:
	var candidates: Array[Player] = []
	for p in home:
		if p.role != "GK" and p != controlled:
			candidates.append(p)
	if candidates.is_empty():
		return
	candidates.sort_custom(func(a: Player, b: Player) -> bool:
		return Util.flat_dist(a.position, ball.position) < Util.flat_dist(b.position, ball.position))
	controlled = candidates[0]
	switch_cooldown = 1.0


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
		var tackle_reach := 1.3 if opp.is_human else 1.0
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
		if d < press_reach:
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
		var max_h := 2.4 if keeper else 1.0
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
	elif spd > (19.0 if best.is_human else 16.0) and ball.pass_target != best:
		# too hot to control: deflection
		ball.vel = Vector3(ball.vel.x * 0.4 + randf_range(-3.0, 3.0), 1.5, ball.vel.z * 0.4 + randf_range(-3.0, 3.0))
		ball.last_touch = best
		ball.pass_target = null
		best.touch_cooldown = 0.35
		return
	_give_ball(best)


func _give_ball(p: Player) -> void:
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


func _build_pitch() -> void:
	var root := Node3D.new()
	root.name = "Pitch"
	add_child(root)
	# surrounding grass
	Util.box(root, Vector3(320, 0.1, 240), Vector3(0, -0.06, 0), Color(0.3, 0.4, 0.2), false)
	# striped pitch (+ a few metres of run-off)
	var stripes := 14
	var w := (HALF_L * 2.0 + 8.0) / stripes
	for i in stripes:
		var c := Color(0.22, 0.5, 0.2) if i % 2 == 0 else Color(0.19, 0.44, 0.17)
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
	# the bench
	Util.box(root, Vector3(3.0, 0.08, 0.5), Vector3(0, 0.5, -HALF_W - 4.0), Color(0.6, 0.42, 0.22))
	Util.box(root, Vector3(0.08, 0.5, 0.4), Vector3(-1.3, 0.25, -HALF_W - 4.0), Color(0.3, 0.3, 0.3))
	Util.box(root, Vector3(0.08, 0.5, 0.4), Vector3(1.3, 0.25, -HALF_W - 4.0), Color(0.3, 0.3, 0.3))
	# umbrella
	Util.cylinder(root, 0.03, 0.03, 2.2, Vector3(1.6, 1.1, -HALF_W - 4.0), Color(0.3, 0.3, 0.3), 6)
	Util.cylinder(root, 0.05, 1.2, 0.45, Vector3(1.6, 2.2, -HALF_W - 4.0), HOME_SHIRT, 8)


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
	var want := Vector3(clampf(focus.x + lead, -HALF_L + 8.0, HALF_L - 8.0), 0, clampf(focus.z * 0.85, -HALF_W + 8.0, HALF_W - 6.0))
	cam_target = cam_target.lerp(want, clampf(delta * 2.5, 0.0, 1.0))
	_place_camera()


func _place_camera() -> void:
	camera.position = cam_target + Vector3(0, 18.0, 15.0)
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
	add_child(layer)

	score_label = Label.new()
	score_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	score_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	score_label.offset_left = -300
	score_label.offset_right = 300
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
	score_label.text = "HOME  %d - %d  AWAY     %s" % [score[0], score[1], _clock_text()]
	toast_label.visible = toast_timer > 0.0
	power_bg.visible = charging
	power_fill.size = Vector2(294.0 * charge, 14)
	power_fill.color = Color(1.0, 0.75, 0.1).lerp(Color(1.0, 0.2, 0.1), charge)


func _clock_text() -> String:
	var t := int(ceil(time_left))
	return "%s %d:%02d" % ["1st" if half == 1 else "2nd", t / 60, t % 60]
