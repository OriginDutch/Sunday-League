class_name Ball
extends Node3D
## Arcade ball: hand-rolled physics (no physics engine) so it always does what we want.
## The ball can leave the pitch; Main detects that and awards the restart.

const RADIUS := 0.22
const GRAVITY := 22.0
const ROLL_DECEL := 3.0        # m/s² constant rolling resistance
const ROLL_DRAG := 0.3         # extra speed-proportional drag on the ground
const AIR_DRAG := 0.1
const BOUNCE := 0.5
const POST_R := 0.06
const FRAME_BOUNCE := 0.65

var vel := Vector3.ZERO
var owner_player: Player = null   # who is dribbling it right now
var last_touch: Player = null
var pass_target: Player = null    # intended receiver of the last pass
var pass_meet := Vector3.INF      # where passer and receiver are supposed to meet
var pass_lob := false             # last pass went through the air
var pass_through := false         # last pass was played into space: the receiver runs onto it
var time_since_kick := 99.0
var hold_time := 0.0               # how long the current owner has had it
var _last_owner: Player = null
var offside_players: Array[Player] = []   # players caught offside by the last kick
var main: Main
var visual: Node3D


func setup(m: Main) -> void:
	main = m
	visual = Node3D.new()
	add_child(visual)
	Util.sphere(visual, RADIUS, Vector3.ZERO, Color(0.97, 0.97, 0.97))
	# two dark bands so you can see it roll
	for i in 2:
		var band := MeshInstance3D.new()
		var tm := TorusMesh.new()
		tm.inner_radius = RADIUS * 0.96
		tm.outer_radius = RADIUS * 1.03
		tm.rings = 16
		tm.ring_segments = 6
		band.mesh = tm
		band.material_override = Util.mat(Color(0.1, 0.1, 0.12))
		band.rotation_degrees = Vector3(90.0 * i, 0.0, 90.0 * (1 - i))
		visual.add_child(band)


func reset_to(pos: Vector3) -> void:
	position = Vector3(pos.x, RADIUS, pos.z)
	vel = Vector3.ZERO
	owner_player = null
	pass_target = null
	last_touch = null
	offside_players.clear()
	time_since_kick = 99.0


## The ball has already gone past the point where its receiver was meant to meet it (through-balls
## and lobs that run on after landing): the receiver should chase it instead of waiting there.
func past_meet() -> bool:
	if pass_meet == Vector3.INF:
		return false
	var v := Vector3(vel.x, 0, vel.z)
	if v.length() < 0.5:
		return true
	return Vector3(pass_meet.x - position.x, 0, pass_meet.z - position.z).dot(v) < 0.0


func flat_speed() -> float:
	return Vector2(vel.x, vel.z).length()


func kick(v: Vector3, by: Player, receiver: Player = null) -> void:
	owner_player = null
	vel = v
	if receiver != null and by != null:
		main.stats["passes"][by.team] += 1
	if main.sfx != null and main.mode == "match":
		main.sfx.kick(v.length())
	last_touch = by
	pass_target = receiver
	pass_meet = Vector3.INF
	pass_lob = false
	pass_through = false
	time_since_kick = 0.0
	if by != null:
		by.touch_cooldown = 0.3
		var exempt := by.restart_kind in ["throw-in", "corner", "goal kick"]
		by.restart_kind = ""
		by.protect = 0.0
		# start just in front of the kicker so we don't instantly re-collect it
		var fwd := Util.flat(v).normalized()
		position = Vector3(by.position.x, RADIUS, by.position.z) + fwd * 0.7
		if exempt:
			offside_players.clear()   # no offside from throw-ins, corners, goal kicks
		else:
			main.mark_offside(by)


func step(delta: float) -> void:
	time_since_kick += delta
	if pass_target != null and time_since_kick > 3.5:
		pass_target = null

	if owner_player != null:
		_dribble(delta)
		return

	vel.y -= GRAVITY * delta
	position += vel * delta
	if position.y < RADIUS:
		position.y = RADIUS
		if vel.y < -2.0:
			# landing: the grass takes a lot of the pace off
			var damp := clampf(1.0 - absf(vel.y) * 0.04, 0.55, 0.9)
			vel.x *= damp
			vel.z *= damp
			vel.y = -vel.y * BOUNCE
		else:
			vel.y = 0.0

	var h := Vector2(vel.x, vel.z)
	var spd := h.length()
	if spd > 0.0:
		var on_ground := position.y <= RADIUS + 0.02
		var decel := (ROLL_DECEL + ROLL_DRAG * spd) if on_ground else (AIR_DRAG * spd)
		var new_spd := maxf(0.0, spd - decel * delta)
		h = h * (new_spd / spd)
		vel.x = h.x
		vel.z = h.y

	_collide_goal_frame()
	_spin(delta)


func _dribble(delta: float) -> void:
	var p := owner_player
	var target := Vector3(p.position.x, RADIUS, p.position.z) + p.facing * 0.62
	if p.restart_kind != "":
		target = Vector3(p.position.x, RADIUS, p.position.z)  # held for a throw-in / set piece
		position = target
		vel = Vector3.ZERO
		return
	if p != _last_owner:
		_last_owner = p
		hold_time = 0.0
	hold_time += delta
	# ease the ball onto the foot when receiving (no teleport), then keep it tight to the foot
	var follow := 8.0 if hold_time < 0.3 else 22.0
	position = position.lerp(target + p.vel * (1.0 / follow), clampf(delta * follow, 0.0, 1.0))
	vel = p.vel
	_spin(delta)


func _collide_goal_frame() -> void:
	var gx := Main.HALF_L
	var half := Main.GOAL_W * 0.5
	for s in [-1.0, 1.0]:
		var sx: float = s
		# posts
		if position.y < Main.GOAL_H:
			for t in [-1.0, 1.0]:
				var sz: float = t
				var d := Vector2(position.x - sx * gx, position.z - sz * half)
				var r := RADIUS + POST_R
				if d.length() < r and d.length() > 0.0001:
					var n := d.normalized()
					position.x = sx * gx + n.x * r
					position.z = sz * half + n.y * r
					var v2 := Vector2(vel.x, vel.z)
					if v2.dot(n) < 0.0:
						v2 = (v2 - 2.0 * v2.dot(n) * n) * FRAME_BOUNCE
						vel.x = v2.x
						vel.z = v2.y
		# crossbar
		if absf(position.z) < half:
			var d2 := Vector2(position.x - sx * gx, position.y - Main.GOAL_H)
			var r2 := RADIUS + POST_R
			if d2.length() < r2 and d2.length() > 0.0001:
				var n2 := d2.normalized()
				position.x = sx * gx + n2.x * r2
				position.y = Main.GOAL_H + n2.y * r2
				var vxy := Vector2(vel.x, vel.y)
				if vxy.dot(n2) < 0.0:
					vxy = (vxy - 2.0 * vxy.dot(n2) * n2) * FRAME_BOUNCE
					vel.x = vxy.x
					vel.y = vxy.y
		# inside the net: keep it there
		var inside_x := sx * position.x > gx and sx * position.x < gx + Main.GOAL_DEPTH + 0.5
		if inside_x and absf(position.z) < half and position.y < Main.GOAL_H:
			var back := gx + Main.GOAL_DEPTH - RADIUS
			if sx * position.x > back:
				position.x = sx * back
				vel.x = -vel.x * 0.15
			if absf(position.z) > half - RADIUS:
				position.z = signf(position.z) * (half - RADIUS)
				vel.z = -vel.z * 0.2
			if position.y > Main.GOAL_H - RADIUS:
				position.y = Main.GOAL_H - RADIUS
				vel.y = minf(vel.y, 0.0)
			vel.x *= 0.96
			vel.z *= 0.96


func _spin(delta: float) -> void:
	var h := Util.flat(vel)
	var spd := h.length()
	if spd > 0.05:
		var axis := Vector3.UP.cross(h / spd).normalized()
		visual.rotate(axis, spd * delta / RADIUS)
