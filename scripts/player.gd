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
var display_name := ""
var speed_mult := 1.0
var mark_target: Player = null  # who to mark when defending, assigned by Main
var run_mode := "hold"        # in possession: "hold" | "deep" | "show"
var run_timer := 0.0
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
var tackle_kind := "slide"  # "slide" (X / C) or "poke" (A / Space: standing tackle, Marcel 2026-11-08)
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


const PlayerModel := preload("res://assets/models/player.glb")
const PlayerLook := preload("res://scripts/player_look.gd")
const BodyShape := preload("res://scripts/body_shape.gd")
const NUMBER_FONT := preload("res://assets/fonts/WorkSans-Variable.ttf")
const SHORTS := Color(0.95, 0.95, 0.95)
const BOOTS := Color(0.08, 0.08, 0.09)
const GLOVES := Color(0.92, 1.0, 0.45)
const LOOPS := ["idle", "jog", "sprint", "celebrate"]
## Speed (m/s) at which the jog / sprint cycles match the feet to the ground.
const JOG_NATURAL := 6.0
const SPRINT_NATURAL := 8.4
const ANIM_BLEND := 0.15

static var _mat_cache := {}      # "Shirt|color" -> material shared by everyone with that colour

var anim: AnimationPlayer
var anim_now := ""
var oneshot_timer := 0.0         # > 0 while a one-shot (kick, slide, dive, catch, celebrate) owns the body
var shirt_number := 0
## Set by Main right after setup (same frame); the look is applied deferred, so these can still change.
var look_seed := ""
var look_age := 0
var slot := 0
var look := {}
var _model: Node3D
var _skel: Skeleton3D


func _build_visual(shirt: Color) -> void:
	visual = Node3D.new()
	add_child(visual)
	body = Node3D.new()            # stun wobble on top of the animation
	visual.add_child(body)
	var model: Node3D = PlayerModel.instantiate()
	body.add_child(model)
	anim = model.get_node("AnimationPlayer")
	for a in LOOPS:
		anim.get_animation(a).loop_mode = Animation.LOOP_LINEAR
	var colours := {"Shirt": shirt, "Shorts": SHORTS, "Socks": shirt, "Boots": BOOTS}
	var skel: Skeleton3D = model.get_node("PlayerRig/Skeleton3D")
	_model = model
	_skel = skel
	for mi in skel.get_children():
		if not mi is MeshInstance3D:
			continue
		var m: MeshInstance3D = mi
		var gloves := role == "GK" and m.name.begins_with("Hand_")
		for i in m.mesh.get_surface_count():
			var base: Material = m.mesh.surface_get_material(i)
			var key: String = base.resource_name
			if gloves and key == "Skin":
				m.set_surface_override_material(i, _kit_mat(base, "Gloves", GLOVES))
			elif colours.has(key):
				m.set_surface_override_material(i, _kit_mat(base, key, colours[key]))
	_apply_look.call_deferred()
	_add_number(skel, shirt)
	_play("idle")


## Height, build, skin, hair and beard from PlayerLook (seeded by look_seed, beard/grey by look_age).
func _apply_look() -> void:
	if _skel == null or not is_instance_valid(_skel):
		return
	var hairs := ["bald"]
	var beards := []
	for c in _skel.get_children():
		var n := String(c.name)
		if n.begins_with("Hair_"):
			hairs.append(n.substr(5))
		elif n.begins_with("Beard_"):
			var style := n.substr(6, n.rfind("_") - 6)
			if not style in beards:
				beards.append(style)
	hairs.sort()
	beards.sort()
	look = PlayerLook.make(look_seed if look_seed != "" else str(get_instance_id()), role, slot, look_age, hairs, beards)
	var beard := PlayerLook.beard(look)
	var keep_beard := "" if beard.is_empty() else "Beard_%s_%s" % beard
	var skin: Color = look["skin"]
	var hair := PlayerLook.hair_color(look)
	var skin_mat: StandardMaterial3D = null
	var hair_mat: StandardMaterial3D = null
	var beard_mat: StandardMaterial3D = null
	for c in _skel.get_children():
		if not c is MeshInstance3D:
			continue
		var m: MeshInstance3D = c
		var n := String(m.name)
		if n.begins_with("Hair_") and n != "Hair_" + look["hair"] or n.begins_with("Beard_") and n != keep_beard:
			m.queue_free()
			continue
		var gloves := role == "GK" and n.begins_with("Hand_")
		for i in m.mesh.get_surface_count():
			var base: Material = m.mesh.surface_get_material(i)
			var key: String = base.resource_name
			if key == "Skin" and not gloves:
				if skin_mat == null:
					skin_mat = base.duplicate()
					skin_mat.albedo_color = skin
				m.set_surface_override_material(i, skin_mat)
			elif key == "Hair" and n.begins_with("Beard_"):
				if beard_mat == null:
					beard_mat = base.duplicate()
					beard_mat.albedo_color = hair.lerp(skin, 0.45) if beard[1] == "stubble" else hair
				m.set_surface_override_material(i, beard_mat)
			elif key == "Hair":
				if hair_mat == null:
					hair_mat = base.duplicate()
					hair_mat.albedo_color = hair
				m.set_surface_override_material(i, hair_mat)
	var s: float = look["height"] / PlayerLook.MODEL_HEIGHT
	body.scale = Vector3.ONE * s
	var shape: SkeletonModifier3D = BodyShape.new()
	shape.setup(look, s)
	_skel.add_child(shape)


func _kit_mat(base: Material, key: String, c: Color) -> Material:
	var k := "%s|%s" % [key, c.to_html()]
	if not _mat_cache.has(k):
		var m: StandardMaterial3D = base.duplicate()
		m.albedo_color = c
		_mat_cache[k] = m
	return _mat_cache[k]


## Shirt number on the back, riding the chest bone. Set by Main after spawning (set_number).
var _number_label: Label3D


func _add_number(skel: Skeleton3D, shirt: Color) -> void:
	var bone := skel.find_bone("chest")
	var att := BoneAttachment3D.new()
	att.bone_name = "chest"
	skel.add_child(att)
	_number_label = Label3D.new()
	var bold := FontVariation.new()
	bold.base_font = NUMBER_FONT
	bold.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 800}
	_number_label.font = bold
	_number_label.font_size = 96
	_number_label.outline_size = 8
	_number_label.pixel_size = 0.0027
	var lum := shirt.get_luminance()
	_number_label.modulate = Color(0.08, 0.08, 0.08) if lum > 0.55 else Color(1, 1, 1)
	_number_label.outline_modulate = Color(1, 1, 1, 0.0) if lum > 0.55 else Color(0, 0, 0, 0.35)
	_number_label.double_sided = false
	_number_label.shaded = true
	# on the back of the chest (model faces +Z, so the back is -Z), facing backwards
	var want := Transform3D(Basis(Vector3.UP, PI), Vector3(0, 1.31, -0.163))
	_number_label.transform = skel.get_bone_global_rest(bone).affine_inverse() * want
	att.add_child(_number_label)


func set_number(n: int) -> void:
	shirt_number = n
	if _number_label:
		_number_label.text = str(n)


func _play(clip: String, blend := ANIM_BLEND, speed := 1.0) -> void:
	if anim_now != clip:
		anim.play(clip, blend)
		anim_now = clip
	anim.speed_scale = speed


## One-shot body action; the locomotion picks up again after `hold` seconds (default: the clip length).
func play_once(clip: String, speed := 1.0, hold := -1.0) -> void:
	if anim == null:
		return
	anim_now = ""
	_play(clip, 0.08, speed)
	anim.seek(0.0, true)
	oneshot_timer = hold if hold > 0.0 else anim.get_animation(clip).length / speed


func celebrate(seconds: float) -> void:
	play_once("celebrate", randf_range(0.9, 1.15), seconds)


func _process(delta: float) -> void:
	if anim == null or main == null:
		return
	if oneshot_timer > 0.0:
		oneshot_timer -= delta
		return
	if role == "GK" and has_ball():
		if anim_now != "catch":
			play_once("catch")
		return
	var spd := Util.flat(vel).length()
	if role == "GK" and wants_sprint and spd > 5.0 and main.ball.owner_player == null:
		var right := Vector3(-facing.z, 0, facing.x)     # facing +Z -> right is -X
		var side := vel.dot(right)
		if absf(side) > 4.0:
			play_once("dive_right" if side > 0.0 else "dive_left", 1.15)
			return
	if spd < 0.7:
		_play("idle")
	elif wants_sprint and spd > SPEED + 0.3:
		_play("sprint", ANIM_BLEND, clampf(spd / SPRINT_NATURAL, 0.6, 1.4))
	else:
		_play("jog", ANIM_BLEND, clampf(spd / JOG_NATURAL, 0.45, 1.4))


# ------------------------------------------------------------------ movement

func has_ball() -> bool:
	return main.ball.owner_player == self


func step(delta: float) -> void:
	touch_cooldown = maxf(0.0, touch_cooldown - delta)
	protect = maxf(0.0, protect - delta)
	stun = maxf(0.0, stun - delta)

	if tackle_timer > 0.0:
		tackle_timer -= delta
		if tackle_timer <= 0.0 and tackle_kind == "slide" and is_human and not has_ball():
			stun = maxf(stun, SLIDE_MISS_DOWN)   # missed sliding tackle: on the floor for a moment
		if is_human:
			# your lunge homes in on the ball a little, so a tackle goes where you meant it
			var to_ball := Util.flat(main.ball.position - position)
			if to_ball.length() > 0.05:
				vel = vel.slerp(to_ball.normalized() * vel.length(), clampf(delta * 8.0, 0.0, 1.0))
		if tackle_kind == "slide":
			vel = vel.move_toward(Vector3.ZERO, 12.0 * delta)
		else:
			vel = vel.move_toward(desired_move.limit_length(1.0) * SPEED, ACCEL * delta)
	else:
		var max_speed := SPRINT if wants_sprint else SPEED
		if role == "GK":
			max_speed = Main.keeper_dive(team) if wants_sprint else GK_SPEED
		max_speed *= speed_mult
		if is_human:
			max_speed *= Main.diff("human_speed_bonus")
		if has_ball():
			max_speed *= Main.diff("human_dribble_speed") if is_human else Main.AI_DRIBBLE_SPEED
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
	bob_t += delta * 14.0
	body.rotation.z = sin(bob_t) * 0.12 if stun > 0.0 else 0.0


# ------------------------------------------------------------------ actions

const MAX_PASS_SPEED := 28.0
const PASS_ARRIVAL_SPEED := 13.0  # how fast the ball should be when it reaches the receiver (was 7: too slow, easy to cut out)


## Ground-ball speed needed to cover `d` metres in `t` seconds with the ball's rolling friction.
static func pass_speed_for(d: float, t: float) -> float:
	var a := Ball.ROLL_DECEL
	var k := Ball.ROLL_DRAG
	return (d + (a / k) * t) * k / (1.0 - exp(-k * t)) - a / k


static func arrival_speed(v0: float, t: float) -> float:
	var a := Ball.ROLL_DECEL
	var k := Ball.ROLL_DRAG
	return (v0 + a / k) * exp(-k * t) - a / k


## Pass into the run of the receiver: find the moment where the ball and the running
## receiver meet, arriving at a comfortable speed.
func pass_to(receiver: Player) -> void:
	var run := receiver.vel
	if receiver.is_human or receiver.team == 0 and main.controlled == receiver:
		run = receiver.desired_move * Player.SPEED
	run *= Main.PASS_LEAD   # lead the run, but not all the way: the receiver also comes to the ball
	var best_target := receiver.position
	var best_v := 10.0
	var best_score := INF
	var t := 0.3
	while t <= 3.5:
		var target := receiver.position + run * t
		target.x = clampf(target.x, -Main.HALF_L + 1.0, Main.HALF_L - 1.0)
		target.z = clampf(target.z, -Main.HALF_W + 1.0, Main.HALF_W - 1.0)
		var d := Util.flat_dist(position, target)
		var v0 := pass_speed_for(d, t)
		if v0 <= MAX_PASS_SPEED and v0 > 0.0:
			var score := absf(arrival_speed(v0, t) - PASS_ARRIVAL_SPEED)
			if score < best_score:
				best_score = score
				best_target = target
				best_v = v0
		t += 0.05
	if best_score == INF or Util.flat_dist(position, best_target) > Main.LOB_PASS_DISTANCE:
		_lob_to(receiver, run)
		return
	var to := Util.flat(best_target - position)
	face_towards(to)
	play_once("pass", 1.2)
	main.ball.kick(to.normalized() * best_v + Vector3.UP * 0.4, self, receiver)
	main.ball.pass_meet = best_target


## Long ball through the air into the receiver's run.
func _lob_to(receiver: Player, run: Vector3) -> void:
	air_pass_to(receiver, run, 20.0, 0.9, 2.3, "shoot")


## A ball through the air into a moving receiver's run. `mps` = metres per second of flight
## (lower = higher ball), clamped to [tmin, tmax] seconds.
func air_pass_to(receiver: Player, run: Vector3, mps: float, tmin: float, tmax: float, anim := "pass") -> void:
	var t := 1.0
	var target := receiver.position
	for i in 4:   # refine flight time against the moving target
		target = receiver.position + run * t
		target.x = clampf(target.x, -Main.HALF_L + 1.0, Main.HALF_L - 1.0)
		target.z = clampf(target.z, -Main.HALF_W + 1.0, Main.HALF_W - 1.0)
		t = clampf(Util.flat_dist(position, target) / mps, tmin, tmax)
	air_ball_to(target, t, receiver, anim)


## Kick the ball so it comes down at `target` after `t` seconds.
func air_ball_to(target: Vector3, t: float, receiver: Player = null, anim := "pass") -> void:
	var to := Util.flat(target - position)
	var vh := to.length() / t * (1.0 + Ball.AIR_DRAG * t * 0.5)   # compensate air drag
	var vy := 0.5 * Ball.GRAVITY * t
	face_towards(to)
	play_once(anim, 1.1)
	main.ball.kick(to.normalized() * vh + Vector3.UP * vy, self, receiver)
	main.ball.pass_meet = Vector3(target.x, 0, target.z)
	main.ball.pass_lob = true


func _run_of(receiver: Player) -> Vector3:
	var run := receiver.vel
	if receiver.is_human or receiver.team == 0 and main.controlled == receiver:
		run = receiver.desired_move * Player.SPEED
	return run * Main.PASS_LEAD


## Flight time of a half-high pass (A A) over `d` metres (Ball.GRAVITY 22: 0.70 s ≈ 1.5 m top,
## 0.82 s ≈ 2 m). Marcel: max 1.5 m up to ~18 m, rising to ~2 m at 25 m; beyond that the ball's
## speed (31 m/s) is the limit and it climbs a little more.
static func lofted_time(d: float) -> float:
	return maxf(0.70 + clampf((d - 18.0) / 7.0, 0.0, 1.0) * 0.12, d / 31.0)


## Half-high pass (A A): over a leg, quicker than a lob.
func lofted_pass_to(receiver: Player) -> void:
	var run := _run_of(receiver)
	var target := receiver.position
	var t := 0.7
	for i in 4:
		target = receiver.position + run * t
		target.x = clampf(target.x, -Main.HALF_L + 1.0, Main.HALF_L - 1.0)
		target.z = clampf(target.z, -Main.HALF_W + 1.0, Main.HALF_W - 1.0)
		t = lofted_time(Util.flat_dist(position, target))
	air_ball_to(target, t, receiver, "pass")


## High lob / long ball (X).
func lob_pass_to(receiver: Player) -> void:
	air_pass_to(receiver, _run_of(receiver), 18.0, 1.0, 1.7, "shoot")   # top ~3–8 m


## A cross into the box (X from the flank): to a teammate's run, or to `spot` when nobody's there.
func cross_to(receiver: Player, spot: Vector3) -> void:
	if receiver != null:
		air_pass_to(receiver, _run_of(receiver), 20.0, 0.9, 1.4, "shoot")   # top ~2–5 m
	else:
		air_ball_to(spot, clampf(Util.flat_dist(position, spot) / 20.0, 0.9, 1.4), null, "shoot")


## Through-ball into the space ahead of the receiver. style: ground (Y), lofted (Y Y), lob (LB+Y).
func through_to(receiver: Player, style: String) -> void:
	var fwd := Vector3(attack_dir, 0, 0)
	var rv := Util.flat(receiver.vel)
	var dir := fwd
	if rv.length() > 1.0:
		dir = (fwd + rv.normalized() * 0.6).normalized()
	var lead: float = {"ground": 9.0, "lofted": 8.0}.get(style, 13.0)
	var target := receiver.position + dir * lead
	target.x = clampf(target.x, -Main.HALF_L + 3.0, Main.HALF_L - 3.0)
	target.z = clampf(target.z, -Main.HALF_W + 1.5, Main.HALF_W - 1.5)
	var run_t := Util.flat_dist(receiver.position, target) / Player.SPRINT
	var d := Util.flat_dist(position, target)
	match style:
		"lofted":
			air_ball_to(target, clampf(d / 20.0, 0.6, 0.8), receiver, "pass")   # top max ~2 m (Marcel)
		"lob":
			air_ball_to(target, clampf(maxf(run_t, d / 18.0), 1.0, 1.7), receiver, "shoot")
		_:
			var to := Util.flat(target - position)
			var v0 := clampf(pass_speed_for(d, maxf(run_t, 0.4)), 8.0, MAX_PASS_SPEED)
			face_towards(to)
			play_once("pass", 1.2)
			main.ball.kick(to.normalized() * v0 + Vector3.UP * 0.4, self, receiver)
			main.ball.pass_meet = Vector3(target.x, 0, target.z)
	main.ball.pass_through = true


## Into space along a direction when nobody is there to receive it (air: lofted/lob kinds).
func air_ball_towards(point: Vector3, mps: float, tmin: float, tmax: float, anim := "pass") -> void:
	var to := Util.flat(point - position)
	if to.length() > 35.0:
		point = position + to.normalized() * 35.0
	air_ball_to(point, clampf(Util.flat_dist(position, point) / mps, tmin, tmax), null, anim)


## Chip shot (LB+B / Ctrl+RMB): a high, slower ball that drops under the bar at `target`.
func chip_at(target: Vector3, power: float) -> void:
	main.stats["shots"][team] += 1
	var to := Util.flat(target - position)
	var d := to.length()
	var dir := to.normalized()
	var spread := 0.02 + 0.04 * power
	dir = dir.rotated(Vector3.UP, randf_range(-spread, spread))
	var t := clampf(d / lerpf(14.0, 20.0, power), 0.8, 1.4)
	var vh := d / t * (1.0 + Ball.AIR_DRAG * t * 0.5)
	var vy := (2.1 - Ball.RADIUS + 0.5 * Ball.GRAVITY * t * t) / t   # comes down just under the bar
	face_towards(dir)
	play_once("shoot", 1.0)
	main.ball.kick(dir * vh + Vector3.UP * vy, self, null)


func pass_towards(point: Vector3) -> void:
	var to := Util.flat(point - position)
	# arrive at the point at roughly the comfortable speed
	var spd := clampf(sqrt(PASS_ARRIVAL_SPEED * PASS_ARRIVAL_SPEED + 2.0 * (Ball.ROLL_DECEL + Ball.ROLL_DRAG * 10.0) * to.length()), 8.0, MAX_PASS_SPEED)
	face_towards(to)
	play_once("pass", 1.2)
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
	play_once("shoot", 1.15)
	main.ball.kick(dir * spd + Vector3.UP * vy, self, null)


func long_kick(target: Vector3, power: float) -> void:
	# keeper punt/goal kick: a lofted ball towards the target
	var to := Util.flat(target - position)
	var spd := lerpf(11.0, 22.0, power)
	face_towards(to)
	play_once("shoot", 1.0)
	main.ball.kick(to.normalized() * spd + Vector3.UP * lerpf(4.0, 8.0, power), self, null)


const SLIDE_MISS_DOWN := 0.5
const POKE_TIME := 0.25


## Standing tackle (A / Space): stick a leg out, no lunge. Shorter reach and less chance than a slide,
## but you stay on your feet when you miss.
func start_poke() -> void:
	if tackle_timer > 0.0 or stun > 0.0:
		return
	var to := Util.flat(main.ball.position - position)
	if to.length() > 0.01:
		face_towards(to)
		vel = to.normalized() * maxf(vel.length(), 3.5)   # a small step in, not a lunge
	tackle_kind = "poke"
	tackle_timer = POKE_TIME
	play_once("pass", 1.6)


func start_tackle() -> void:
	if tackle_timer > 0.0 or stun > 0.0:
		return
	tackle_kind = "slide"
	var to := Util.flat(main.ball.position - position)
	if to.length() > 0.01:
		vel = to.normalized() * (Main.HUMAN_TACKLE_LUNGE if is_human else Main.AI_TACKLE_LUNGE)
		face_towards(to)
	tackle_timer = 0.35
	play_once("slide", 1.35)


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


## Keep a bit of room from teammates (Marcel, 2026-11-08: players bunched up). Not for the chaser or
## the pass receiver — they go for the ball. Returns a push to add to desired_move.
func _separation() -> Vector3:
	var push := Vector3.ZERO
	for q in main.team_list(team):
		if q == self or q.role == "GK":
			continue
		var d := Util.flat(position - q.position)
		var l := d.length()
		if l < Main.SEPARATION_RADIUS and l > 0.01:
			push += d / l * (1.0 - l / Main.SEPARATION_RADIUS)
		elif l <= 0.01:
			push += Vector3(randf_range(-1, 1), 0, randf_range(-1, 1)).normalized()
	return push * Main.SEPARATION_STRENGTH


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
		_update_run(delta, holder)
		var spot := _attack_spot(holder)
		desired_move = (_seek(spot, 1.0) + _separation()).limit_length(1.0)
		wants_sprint = run_mode != "hold" or Util.flat_dist(position, spot) > 6.0
		return

	if b.pass_target == self and b.pass_meet != Vector3.INF and Util.flat_dist(position, b.position) > 6.0 and not (b.pass_through and b.past_meet()):
		# ground pass: come towards the ball rather than wait for it. lob: get under it.
		var meet := b.pass_meet if (b.pass_lob or b.pass_through) else b.pass_meet.lerp(Util.flat(b.position), 0.35)
		desired_move = _seek(meet, 1.0)
		wants_sprint = Util.flat_dist(position, meet) > 2.0
		return
	if b.pass_target == self or main.is_chaser(self):
		var target := Util.flat(b.position + b.vel * 0.25)
		var d := Util.flat_dist(position, target)
		if holder != null and holder.team != team:
			# jockey: stay goal-side at a little distance instead of running into the carrier
			var own_goal := Vector3(-Main.HALF_L * attack_dir, 0, 0)
			var gap := Main.AI_JOCKEY_DISTANCE if holder.is_human else Main.AI_JOCKEY_DISTANCE_AI
			target = holder.position + Util.flat(own_goal - holder.position).normalized() * gap
		desired_move = _seek(target, 1.0)
		wants_sprint = d > 3.0
		if holder != null and holder.team != team and d < Main.AI_TACKLE_START_RANGE:
			var rate := Main.diff("ai_tackle_rate_vs_human") if holder.is_human else Main.AI_TACKLE_RATE
			if randf() < rate * delta:
				start_tackle()
		return

	# read an opponent's pass and cut it out
	if holder == null and b.last_touch != null and b.last_touch.team != team and b.flat_speed() > 5.0:
		var ip := _intercept_point()
		if ip != Vector3.INF:
			desired_move = _seek(ip, 1.0)
			wants_sprint = true
			return

	# second man: cover goal-side of the ball carrier, ready to step in
	if holder != null and holder.team != team and main.is_second_presser(self):
		var own_goal := Vector3(-Main.HALF_L * attack_dir, 0, 0)
		var to_goal := Util.flat(own_goal - holder.position).normalized()
		# cover goal-side but a few metres towards the middle, not in a line behind the presser
		var side := Vector3(-to_goal.z, 0, to_goal.x)
		if side.dot(Vector3(0, 0, -holder.position.z)) < 0.0:
			side = -side
		var cover := holder.position + to_goal * Main.COVER_DISTANCE + side * Main.COVER_SIDE
		desired_move = (_seek(cover, 1.0) + _separation()).limit_length(1.0)
		wants_sprint = Util.flat_dist(position, cover) > 4.0
		return

	# the zone owner presses the carrier (no spacing push); everyone else keeps some room
	var presser := main.zone_owner(team) == self
	desired_move = _seek(_defend_spot(), 0.9) if presser else (_seek(_defend_spot(), 0.9) + _separation()).limit_length(1.0)
	wants_sprint = Util.flat_dist(position, _defend_spot()) > 5.0


## Where on the moving ball's path (next ~1.2 s) this player could get to first, or INF.
func _intercept_point() -> Vector3:
	var b := main.ball
	var bp := Util.flat(b.position)
	var bv := Util.flat(b.vel)
	var t := 0.15
	while t <= 1.2:
		var p := bp + bv * t
		var d := Util.flat_dist(position, p)
		if d > Main.INTERCEPT_RANGE:
			t += 0.15
			continue
		if d / (Player.SPRINT * speed_mult) <= t + 0.1:
			return p
		t += 0.15
	return Vector3.INF


func _ai_dribble() -> void:
	var goal := Vector3(Main.HALF_L * attack_dir, 0, 0)
	var to_goal := Util.flat(goal - position).normalized()
	# near the boards / byline: cut back inside instead of running into the wall
	var dist_x := absf(goal.x - position.x)
	if absf(position.z) > Main.HALF_W - 3.0 or (dist_x < 5.0 and absf(position.z) > Main.GOAL_W):
		var inside := Vector3(goal.x - attack_dir * 9.0, 0, position.z * 0.3)
		to_goal = Util.flat(inside - position).normalized()
	# look for space: try a fan of directions around goal-wards, pick the one with most room
	var best_dir := to_goal
	var best_score := -INF
	for deg in [0.0, -20.0, 20.0, -45.0, 45.0]:
		var a: float = deg
		var dir := to_goal.rotated(Vector3.UP, deg_to_rad(a))
		var probe := position + dir * 4.0
		if absf(probe.z) > Main.HALF_W - 1.0 or absf(probe.x) > Main.HALF_L - 1.0:
			continue
		var room := 6.0
		for o in main.team_list(1 - team):
			room = minf(room, Util.flat_dist(o.position, probe))
		var score := room - absf(a) * 0.06
		if score > best_score:
			best_score = score
			best_dir = dir
	desired_move = best_dir


func _ai_try_shoot() -> bool:
	var gx := Main.HALF_L * attack_dir
	var dist_x := absf(gx - position.x)
	if dist_x > Main.AI_SHOOT_RANGE or absf(position.z) > 16.0:
		return false
	var chance := remap(dist_x, Main.AI_SHOOT_RANGE, 4.0, 0.08, 0.85)
	if randf() > chance:
		return false
	var aim_z := randf_range(-Main.GOAL_W * 0.5 + 0.3, Main.GOAL_W * 0.5 - 0.3)
	shoot_at(Vector3(gx, 0, aim_z), randf_range(0.3, 0.8), randf_range(0.3, 1.6), Main.diff("ai_shot_error"))
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
	main.stats["bailouts"][team] += 1
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


## How far this player's formation spot is from his own goal line (GK ~1, CB ~12, ST ~50).
func form_depth() -> float:
	return (home_pos.x + Main.HALF_L * attack_dir) * attack_dir


# ---------------------------------------------------------------- in possession

## Every few seconds an attacker picks what to do: go in behind, come short, or hold position.
func _update_run(delta: float, holder: Player) -> void:
	run_timer -= delta
	if run_timer > 0.0:
		return
	run_timer = randf_range(2.5, 5.0)
	var d := form_depth()
	var deep := 0.5 if d > 40.0 else (0.25 if d > 22.0 else 0.0)
	var show := 0.25 if d > 40.0 else (0.35 if d > 22.0 else 0.2)
	var r := randf()
	if r < deep:
		run_mode = "deep"
	elif r < deep + show and main.count_run_mode(team, "show") < Main.MAX_SHOW_RUNNERS:
		run_mode = "show"
	else:
		run_mode = "hold"
	if holder == self:
		run_mode = "hold"


func _attack_spot(holder: Player) -> Vector3:
	var line := main.offside_line(team)
	var spot: Vector3
	match run_mode:
		"deep":
			# run along the last line, drifting inside, ready to go in behind
			var lane_z := home_pos.z * 0.6
			spot = Vector3(line - attack_dir * 0.8, 0, lane_z)
		"show":
			# come short: get free about 9 m from the ball carrier
			var away := Util.flat(position - holder.position)
			if away.length() < 0.1:
				away = Vector3(0, 0, 1)
			spot = holder.position + away.normalized() * 9.0 - Vector3(attack_dir * 2.0, 0, 0)
		_:
			spot = _support_spot()
	# never stand offside
	if spot.x * attack_dir > 0.0 and (spot.x - line) * attack_dir > -0.8:
		spot.x = line - attack_dir * 1.0
	spot.x = clampf(spot.x, -Main.HALF_L + 2.0, Main.HALF_L - 2.0)
	spot.z = clampf(spot.z, -Main.HALF_W + 1.5, Main.HALF_W - 1.5)
	return spot


func _support_spot() -> Vector3:
	var b := main.ball.position
	var x := home_pos.x + attack_dir * Main.SUPPORT_PUSH + b.x * 0.45
	var z := home_pos.z * 1.15
	var spot := Vector3(x, 0, z) + jitter
	spot.x = clampf(spot.x, -Main.HALF_L + 2.0, Main.HALF_L - 2.0)
	spot.z = clampf(spot.z, -Main.HALF_W + 1.5, Main.HALF_W - 1.5)
	return spot


# ---------------------------------------------------------------- out of possession

## Layered block: the back line drops with the ball, midfield and attack keep their distance
## behind it (compressing when the ball is deep), so the team never collapses into one line.
func zone_spot() -> Vector3:
	var own_goal_x := -Main.HALF_L * attack_dir
	var b := main.ball.position
	var ball_depth := (b.x - own_goal_x) * attack_dir
	var back_line := clampf(ball_depth * Main.BLOCK_LINE_FACTOR, Main.BLOCK_MIN_DEPTH, Main.BLOCK_MAX_DEPTH)
	var spacing := clampf(0.55 + ball_depth / 150.0, 0.6, 1.0)
	var depth := back_line + (form_depth() - Main.BLOCK_FORM_BACK) * spacing
	return Vector3(own_goal_x + attack_dir * depth, 0, home_pos.z * 0.85 + b.z * 0.3)


func _defend_spot() -> Vector3:
	var own_goal := Vector3(-Main.HALF_L * attack_dir, 0, 0)
	var spot := zone_spot()
	var holder := main.ball.owner_player
	# step out to the ball carrier when he comes into your zone
	if holder != null and holder.team != team and main.zone_owner(team) == self:
		var to_goal := Util.flat(own_goal - holder.position).normalized()
		spot = holder.position + to_goal * Main.STEP_OUT_DISTANCE
	else:
		# pick up an attacker who wanders into the zone
		var mark := mark_target
		if mark != null and Util.flat_dist(mark.position, spot) < Main.MARK_RADIUS:
			var to_goal := Util.flat(own_goal - mark.position).normalized()
			spot = mark.position + to_goal * Main.MARK_DISTANCE
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
	var reaction: float = Main.keeper_reaction(team)
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
