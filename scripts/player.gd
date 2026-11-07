class_name Player
extends Node3D
## One footballer: movement, visuals and a deliberately simple AI brain.

const RADIUS := 0.38
const SPEED := 6.0
const SPRINT := 8.5
const GK_SPEED := 7.0
const ACCEL := 32.0

var main: Main
var team := 0                # 0 = home (human side, attacks +X), 1 = away (attacks -X)
var role := "OUT"            # "GK" or "OUT"
var home_pos := Vector3.ZERO # formation spot (already mirrored for the away team)
var attack_dir := 1.0
var is_human := false        # set every frame by Main
var mark_target: Player = null  # who to mark when defending, assigned by Main
var restart_kind := ""        # "throw-in" / "corner" / "goal kick" / "free kick" while taking a set piece

var vel := Vector3.ZERO
var yaw := 0.0
var facing := Vector3(0, 0, 1)
var desired_move := Vector3.ZERO   # length 0..1, set by AI or human input
var wants_sprint := false

var touch_cooldown := 0.0   # can't touch the ball while > 0
var protect := 0.0          # can't be dispossessed while > 0
var contact_time := 0.0     # how long this player has been pressing the ball carrier
var stun := 0.0             # after a missed tackle / being tackled
var tackle_timer := 0.0     # lunging
var has_ball_time := 0.0
var think_timer := 0.0
var jitter := Vector3.ZERO  # small personal offset so AI isn't robotic

var visual: Node3D
var body: Node3D
var bob_t := 0.0


func setup(m: Main, t: int, r: String, home: Vector3, shirt: Color) -> void:
	main = m
	team = t
	role = r
	home_pos = home
	attack_dir = 1.0 if team == 0 else -1.0
	yaw = PI * 0.5 if team == 0 else -PI * 0.5
	_build_visual(shirt)
	_update_facing()


func _build_visual(shirt: Color) -> void:
	visual = Node3D.new()
	add_child(visual)
	body = Node3D.new()
	visual.add_child(body)

	var skin_tones := [Color(0.98, 0.82, 0.68), Color(0.87, 0.67, 0.5), Color(0.6, 0.42, 0.3), Color(0.42, 0.28, 0.2)]
	var hair_tones := [Color(0.15, 0.1, 0.07), Color(0.45, 0.28, 0.12), Color(0.9, 0.75, 0.35), Color(0.8, 0.35, 0.12), Color(0.2, 0.2, 0.22)]
	var skin: Color = skin_tones[randi() % skin_tones.size()]
	var hair: Color = hair_tones[randi() % hair_tones.size()]

	# legs + shorts + shirt (chunky toy style)
	Util.cylinder(body, 0.09, 0.09, 0.5, Vector3(-0.13, 0.25, 0), skin, 8)
	Util.cylinder(body, 0.09, 0.09, 0.5, Vector3(0.13, 0.25, 0), skin, 8)
	Util.cylinder(body, 0.26, 0.28, 0.25, Vector3(0, 0.6, 0), Color(0.95, 0.95, 0.95))
	var torso := MeshInstance3D.new()
	var cap := CapsuleMesh.new()
	cap.radius = 0.3
	cap.height = 0.85
	cap.radial_segments = 12
	cap.rings = 4
	torso.mesh = cap
	torso.material_override = Util.mat(shirt)
	torso.position = Vector3(0, 1.0, 0)
	body.add_child(torso)
	# arms
	Util.cylinder(body, 0.08, 0.08, 0.5, Vector3(-0.36, 1.0, 0), shirt, 8)
	Util.cylinder(body, 0.08, 0.08, 0.5, Vector3(0.36, 1.0, 0), shirt, 8)
	# head, hair, eyes (+Z is "forward" in local space)
	Util.sphere(body, 0.24, Vector3(0, 1.62, 0), skin)
	var h := Util.sphere(body, 0.22, Vector3(0, 1.74, -0.03), hair)
	h.scale = Vector3(1.05, 0.6, 1.05)
	Util.sphere(body, 0.035, Vector3(-0.08, 1.65, 0.21), Color(0.05, 0.05, 0.05))
	Util.sphere(body, 0.035, Vector3(0.08, 1.65, 0.21), Color(0.05, 0.05, 0.05))
	if role == "GK":
		Util.sphere(body, 0.1, Vector3(-0.36, 0.72, 0), Color(0.9, 1.0, 0.4))
		Util.sphere(body, 0.1, Vector3(0.36, 0.72, 0), Color(0.9, 1.0, 0.4))


# ------------------------------------------------------------------ movement

func has_ball() -> bool:
	return main.ball.owner_player == self


func step(delta: float) -> void:
	touch_cooldown = maxf(0.0, touch_cooldown - delta)
	protect = maxf(0.0, protect - delta)
	stun = maxf(0.0, stun - delta)

	if tackle_timer > 0.0:
		tackle_timer -= delta
		vel = vel.move_toward(Vector3.ZERO, 12.0 * delta)
	else:
		var max_speed := SPRINT if wants_sprint else SPEED
		if role == "GK":
			max_speed = (Main.KEEPER_DIVE_SPEED[team] as float) if wants_sprint else GK_SPEED
		if is_human:
			max_speed *= Main.HUMAN_SPEED_BONUS
		if has_ball():
			max_speed *= Main.HUMAN_DRIBBLE_SPEED if is_human else Main.AI_DRIBBLE_SPEED
		var target_v := desired_move.limit_length(1.0) * max_speed
		if stun > 0.0 or restart_kind != "":
			target_v = Vector3.ZERO
		vel = vel.move_toward(target_v, ACCEL * delta)
	vel.y = 0.0
	position += vel * delta

	# stay on the pitch; keepers stay in their box
	if restart_kind != "":
		vel = Vector3.ZERO
	position.x = clampf(position.x, -Main.HALF_L - 2.0, Main.HALF_L + 2.0)
	position.z = clampf(position.z, -Main.HALF_W - 2.0, Main.HALF_W + 2.0)
	if role == "GK":
		var own_x := -Main.HALF_L * attack_dir
		var far_x := own_x + attack_dir * Main.BOX_DEPTH
		position.x = clampf(position.x, minf(own_x, far_x), maxf(own_x, far_x))
		position.z = clampf(position.z, -Main.BOX_HALF_W, Main.BOX_HALF_W)
	position.y = 0.0

	if vel.length() > 0.6:
		yaw = lerp_angle(yaw, atan2(vel.x, vel.z), clampf(delta * 12.0, 0.0, 1.0))
	_update_facing()
	_animate(delta)


func face_towards(dir: Vector3) -> void:
	var d := Util.flat(dir)
	if d.length() > 0.01:
		yaw = atan2(d.x, d.z)
		_update_facing()


func _update_facing() -> void:
	facing = Vector3(sin(yaw), 0.0, cos(yaw))
	if visual:
		visual.rotation.y = yaw


func _animate(delta: float) -> void:
	var spd := vel.length()
	bob_t += delta * (4.0 + spd * 1.6)
	body.position.y = absf(sin(bob_t)) * minf(spd, 6.0) * 0.018
	var lean := 0.5 if tackle_timer > 0.0 else spd * 0.025
	body.rotation.x = lean
	body.rotation.z = sin(bob_t * 3.0) * 0.15 if stun > 0.0 else 0.0


# ------------------------------------------------------------------ actions

func pass_to(receiver: Player) -> void:
	var lead := receiver.position + receiver.vel * 0.35
	var to := Util.flat(lead - position)
	var spd := clampf(5.5 + to.length() * 0.85, 8.0, 24.0)
	face_towards(to)
	main.ball.kick(to.normalized() * spd + Vector3.UP * 0.4, self, receiver)


func pass_towards(point: Vector3) -> void:
	var to := Util.flat(point - position)
	var spd := clampf(5.5 + to.length() * 0.85, 8.0, 24.0)
	face_towards(to)
	main.ball.kick(to.normalized() * spd + Vector3.UP * 0.4, self, null)


## Shoot so the ball arrives at `target` (x/z) at roughly `height`.
## Higher power = faster but less accurate. Returns the planned crossing point.
func shoot_at(target: Vector3, power: float, height: float, error_scale: float = 1.0) -> void:
	main.stats["shots"][team] += 1
	var to := Util.flat(target - position)
	var dir := to.normalized()
	var spread := (0.025 + 0.06 * power) * error_scale
	dir = dir.rotated(Vector3.UP, randf_range(-spread, spread))
	height = maxf(Ball.RADIUS, height + randf_range(-0.35, 0.35) * power * error_scale)
	var spd := lerpf(15.0, 28.0, power)
	var t := maxf(to.length() / spd, 0.12) * 1.04   # small fudge for air drag
	var vy := (height - Ball.RADIUS + 0.5 * Ball.GRAVITY * t * t) / t
	vy = minf(vy, 11.0)
	face_towards(dir)
	main.ball.kick(dir * spd + Vector3.UP * vy, self, null)


func long_kick(target: Vector3, power: float) -> void:
	# keeper punt/goal kick: a lofted ball towards the target
	var to := Util.flat(target - position)
	var spd := lerpf(11.0, 22.0, power)
	face_towards(to)
	main.ball.kick(to.normalized() * spd + Vector3.UP * lerpf(4.0, 8.0, power), self, null)


func start_tackle() -> void:
	if tackle_timer > 0.0 or stun > 0.0:
		return
	var to := Util.flat(main.ball.position - position)
	if to.length() > 0.01:
		vel = to.normalized() * (11.0 if is_human else 9.5)
		face_towards(to)
	tackle_timer = 0.35


# ------------------------------------------------------------------ AI

func ai_update(delta: float) -> void:
	think_timer -= delta
	if think_timer <= 0.0 and not has_ball():
		think_timer = randf_range(0.4, 0.8)
		jitter = Vector3(randf_range(-1.5, 1.5), 0, randf_range(-1.5, 1.5))
	if role == "GK":
		_ai_keeper(delta)
	else:
		_ai_outfield(delta)


func _seek(target: Vector3, factor: float) -> Vector3:
	var to := Util.flat(target - position)
	var d := to.length()
	if d < 0.35:
		return Vector3.ZERO
	return to / d * factor * clampf(d / 2.0, 0.25, 1.0)


func _ai_outfield(delta: float) -> void:
	var b := main.ball
	wants_sprint = false

	if has_ball():
		has_ball_time += delta
		if restart_kind != "":
			if has_ball_time > 0.8:
				_ai_take_restart()
			return
		if think_timer <= 0.0:
			think_timer = randf_range(0.15, 0.3)
			if _ai_try_shoot():
				return
			if _ai_try_pass():
				return
			if has_ball_time > 4.5:
				_ai_bail_out()
				return
		_ai_dribble()
		return

	var holder := b.owner_player
	if holder != null and holder.team == team:
		var spot := _support_spot()
		desired_move = _seek(spot, 1.0)
		wants_sprint = Util.flat_dist(position, spot) > 6.0
		return

	if b.pass_target == self or main.is_chaser(self):
		var target := Util.flat(b.position + b.vel * 0.25)
		var d := Util.flat_dist(position, target)
		desired_move = _seek(target, 1.0)
		wants_sprint = d > 3.0
		if holder != null and holder.team != team and d < 1.8:
			var rate := Main.AI_TACKLE_RATE_VS_HUMAN if holder.is_human else 1.2
			if randf() < rate * delta:
				start_tackle()
		return

	desired_move = _seek(_defend_spot(), 0.9)
	wants_sprint = Util.flat_dist(position, _defend_spot()) > 5.0


func _ai_dribble() -> void:
	var goal := Vector3(Main.HALF_L * attack_dir, 0, 0)
	var steer := Util.flat(goal - position).normalized()
	# near the boards / byline: cut back inside instead of running into the wall
	var dist_x := absf(goal.x - position.x)
	var near_wall := absf(position.z) > Main.HALF_W - 3.0
	if near_wall or (dist_x < 5.0 and absf(position.z) > Main.GOAL_W):
		var inside := Vector3(goal.x - attack_dir * 9.0, 0, position.z * 0.3)
		steer = Util.flat(inside - position).normalized()
	var opp := main.nearest_opponent(self)
	if opp != null:
		var away := Util.flat(position - opp.position)
		var d := away.length()
		if d < 3.5 and d > 0.01:
			steer += away / d * (3.5 - d) * 0.45
	desired_move = steer.normalized()


func _ai_try_shoot() -> bool:
	var gx := Main.HALF_L * attack_dir
	var dist_x := absf(gx - position.x)
	if dist_x > Main.AI_SHOOT_RANGE or absf(position.z) > 12.0:
		return false
	var chance := remap(dist_x, Main.AI_SHOOT_RANGE, 4.0, 0.2, 0.85)
	if randf() > chance:
		return false
	var aim_z := randf_range(-Main.GOAL_W * 0.5 + 0.3, Main.GOAL_W * 0.5 - 0.3)
	shoot_at(Vector3(gx, 0, aim_z), randf_range(0.3, 0.8), randf_range(0.3, 1.6), Main.AI_SHOT_ERROR)
	return true


func _ai_try_pass() -> bool:
	var opp := main.nearest_opponent(self)
	var pressured := opp != null and Util.flat_dist(opp.position, position) < 2.2
	var mate := main.best_open_teammate(self)
	if mate == null:
		return false
	var forward_gain := (mate.position.x - position.x) * attack_dir
	if pressured and randf() < 0.6:
		pass_to(mate)
		return true
	if forward_gain > 4.0 and randf() < 0.25:
		pass_to(mate)
		return true
	if has_ball_time > 3.5 and randf() < 0.4:
		pass_to(mate)
		return true
	return false


func _ai_take_restart() -> void:
	var gx := Main.HALF_L * attack_dir
	if restart_kind == "corner":
		# whip it into the box
		long_kick(Vector3(gx - attack_dir * randf_range(6.0, 11.0), 0, randf_range(-6.0, 6.0)), randf_range(0.55, 0.8))
		return
	var mate := main.best_open_teammate(self)
	if mate != null:
		pass_to(mate)
	else:
		_ai_bail_out()


## Last resort when held too long: pass to anyone, else hoof it towards the middle.
func _ai_bail_out() -> void:
	var best: Player = null
	var best_d := INF
	for m in main.team_list(team):
		if m == self:
			continue
		var d := Util.flat_dist(m.position, position)
		if d > 3.0 and d < best_d:
			best_d = d
			best = m
	if best != null:
		pass_to(best)
	else:
		pass_towards(Vector3(0, 0, 0))


func _support_spot() -> Vector3:
	var b := main.ball.position
	var x := home_pos.x + attack_dir * Main.SUPPORT_PUSH + b.x * 0.45
	var z := home_pos.z * 1.15
	var spot := Vector3(x, 0, z) + jitter
	# stay onside
	var line := main.offside_line(team)
	if spot.x * attack_dir > 0.0 and (spot.x - line) * attack_dir > -0.8:
		spot.x = line - attack_dir * 1.0
	spot.x = clampf(spot.x, -Main.HALF_L + 2.0, Main.HALF_L - 2.0)
	spot.z = clampf(spot.z, -Main.HALF_W + 1.5, Main.HALF_W - 1.5)
	return spot


func _defend_spot() -> Vector3:
	# mark the most dangerous attacker that isn't on the ball: stand goal-side of him
	var own_goal := Vector3(-Main.HALF_L * attack_dir, 0, 0)
	var b := main.ball.position
	# zone: formation spot shifted with the ball
	var spot := Vector3(home_pos.x + b.x * 0.55, 0, home_pos.z * 0.85 + b.z * 0.25)
	# pick up an attacker who wanders into the zone
	var mark := mark_target
	if mark != null and Util.flat_dist(mark.position, spot) < Main.MARK_RADIUS:
		var to_goal := Util.flat(own_goal - mark.position).normalized()
		spot = mark.position + to_goal * 1.6
	spot.x = clampf(spot.x, -Main.HALF_L + 1.5, Main.HALF_L - 1.5)
	spot.z = clampf(spot.z, -Main.HALF_W + 1.0, Main.HALF_W - 1.0)
	return spot


func in_own_box() -> bool:
	var own_x := -Main.HALF_L * attack_dir
	return absf(position.x - own_x) < Main.BOX_DEPTH and absf(position.z) < Main.BOX_HALF_W


func _ai_keeper(delta: float) -> void:
	var b := main.ball
	var own_x := -Main.HALF_L * attack_dir
	wants_sprint = false

	if has_ball():
		has_ball_time += delta
		desired_move = Vector3.ZERO
		face_towards(Vector3(attack_dir, 0, 0))
		if has_ball_time > 0.9:
			var mate := main.best_open_teammate(self)
			if mate != null and randf() < 0.7:
				pass_to(mate)
			else:
				long_kick(Vector3(0, 0, randf_range(-6.0, 6.0)), randf_range(0.6, 1.0))
		return

	var line_x := own_x + attack_dir * 0.9
	var half := Main.GOAL_W * 0.5
	var target := Vector3(line_x, 0, clampf(b.position.z * 0.45, -half + 0.4, half - 0.4))
	var bv := b.vel
	var reaction: float = Main.KEEPER_REACTION[team]
	var incoming := b.owner_player == null and signf(bv.x) == -attack_dir and absf(bv.x) > 6.0
	if incoming:
		if b.time_since_kick > reaction:
			var t := (line_x - b.position.x) / bv.x
			if t > 0.0 and t < 1.4:
				target.z = clampf(b.position.z + bv.z * t, -half - 0.3, half + 0.3)
				wants_sprint = true   # dive
		else:
			target = position   # still reacting
	elif b.owner_player == null and absf(b.position.x - own_x) < Main.KEEPER_RUSH_DEPTH and absf(b.position.z) < Main.KEEPER_RUSH_HALF_W and b.flat_speed() < 9.0:
		target = Util.flat(b.position)  # come and claim it
	desired_move = _seek(target, 1.0)
