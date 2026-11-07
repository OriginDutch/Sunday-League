class_name Fan
extends Node3D
## One supporter. Sits on a seat (paying) or stands along the touchline (free).
## Reacts to goals, saves and tackles.

var seated := false
var supports_us := true          # false = home fans at an away ground: they cheer for the other side
var home_spot := Vector3.ZERO     # seat position, or the group spot for standing fans
var face_yaw := 0.0
var body: Node3D
var arm_l: Node3D
var arm_r: Node3D
var t := 0.0
var phase := 0.0
var jump_t := 0.0                 # > 0 while jumping
var cheer_t := 0.0                # > 0 while arms are up
var slump_t := 0.0                # > 0 while gutted
var wander_target := Vector3.ZERO
var wander_timer := 0.0


func setup(is_seated: bool, spot: Vector3, yaw: float, shirt: Color, skin: Color) -> void:
	seated = is_seated
	home_spot = spot
	face_yaw = yaw
	position = spot
	rotation.y = yaw
	phase = randf() * TAU
	wander_target = spot
	body = Node3D.new()
	add_child(body)
	if not seated:
		Util.cylinder(body, 0.08, 0.08, 0.5, Vector3(-0.1, 0.25, 0), Color(0.2, 0.22, 0.3), 6)
		Util.cylinder(body, 0.08, 0.08, 0.5, Vector3(0.1, 0.25, 0), Color(0.2, 0.22, 0.3), 6)
	var torso_y := 0.95 if not seated else 0.85
	var torso := Util.cylinder(body, 0.2, 0.24, 0.6, Vector3(0, torso_y, 0), shirt, 8)
	torso.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	Util.sphere(body, 0.17, Vector3(0, torso_y + 0.48, 0), skin)
	arm_l = Node3D.new()
	arm_l.position = Vector3(-0.27, torso_y + 0.22, 0)
	body.add_child(arm_l)
	Util.cylinder(arm_l, 0.06, 0.06, 0.45, Vector3(0, -0.22, 0), shirt, 6)
	arm_r = Node3D.new()
	arm_r.position = Vector3(0.27, torso_y + 0.22, 0)
	body.add_child(arm_r)
	Util.cylinder(arm_r, 0.06, 0.06, 0.45, Vector3(0, -0.22, 0), shirt, 6)
	if seated:
		# legs forward over the edge of the seat
		Util.box(body, Vector3(0.36, 0.14, 0.4), Vector3(0, 0.52, 0.18), Color(0.2, 0.22, 0.3))
		Util.box(body, Vector3(0.32, 0.45, 0.14), Vector3(0, 0.25, 0.38), Color(0.2, 0.22, 0.3))
	for c in body.find_children("*", "GeometryInstance3D", true, false):
		(c as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func react(kind: String) -> void:
	if not supports_us:
		kind = {"goal_for": "goal_against", "goal_against": "goal_for", "save": "chance", "chance": "save"}.get(kind, kind)
	match kind:
		"goal_for":
			jump_t = randf_range(1.6, 2.6)
			cheer_t = jump_t + 0.6
		"goal_against":
			slump_t = randf_range(1.5, 2.5)
		"save", "tackle", "chance":
			if randf() < 0.55:
				cheer_t = randf_range(0.4, 0.9)
				if randf() < 0.4:
					jump_t = 0.5


func _process(delta: float) -> void:
	t += delta
	jump_t = maxf(0.0, jump_t - delta)
	cheer_t = maxf(0.0, cheer_t - delta)
	slump_t = maxf(0.0, slump_t - delta)

	# jumping (seated fans stand up and bounce)
	var y := 0.0
	if jump_t > 0.0:
		y = absf(sin(t * 9.0 + phase)) * 0.35 + (0.35 if seated else 0.0)
	else:
		y = sin(t * 1.3 + phase) * 0.015   # idle breathing/sway
	body.position.y = y
	body.rotation.x = 0.35 if slump_t > 0.0 else 0.0

	var arm_up := cheer_t > 0.0
	var target_rot := PI * 0.85 if arm_up else 0.0
	arm_l.rotation.z = lerpf(arm_l.rotation.z, -target_rot, clampf(delta * 12.0, 0.0, 1.0))
	arm_r.rotation.z = lerpf(arm_r.rotation.z, target_rot, clampf(delta * 12.0, 0.0, 1.0))
	if arm_up:
		arm_l.rotation.x = sin(t * 10.0 + phase) * 0.3
		arm_r.rotation.x = -sin(t * 10.0 + phase) * 0.3

	# standing fans shuffle around a little within their group
	if not seated:
		wander_timer -= delta
		if wander_timer <= 0.0:
			wander_timer = randf_range(2.0, 6.0)
			wander_target = home_spot + Vector3(randf_range(-0.9, 0.9), 0, randf_range(-0.6, 0.6))
		var to := wander_target - position
		to.y = 0.0
		if to.length() > 0.05:
			position += to.normalized() * minf(to.length(), 0.6 * delta)
