extends SceneTree
## Dev scene: a small stand of fans v2 going through calm -> chance -> goal -> conceded.
## godot --path . --script tools/dev/fan_test.gd [-- cold|mild|sunny]   (add --write-movie to record)
const FanCrowd := preload("res://scripts/fan_crowd.gd")
var crowd
var t := 0.0
var fired := {}
func _init():
	var temp := "mild"
	for a in OS.get_cmdline_user_args():
		if a in ["cold", "mild", "sunny"]:
			temp = a
	var root := Node3D.new()
	get_root().add_child(root)
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.6, 0.68, 0.76)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.75, 0.77, 0.8)
	e.ambient_light_energy = 0.7
	env.environment = e
	root.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, -30, 0)
	sun.shadow_enabled = true
	root.add_child(sun)
	var concrete := StandardMaterial3D.new()
	concrete.albedo_color = Color(0.62, 0.62, 0.6)
	var plank := StandardMaterial3D.new()
	plank.albedo_color = Color(0.75, 0.76, 0.78)
	var seats := []
	var rows := 6
	var per_row := 18
	for r in rows:
		var y := r * 0.42
		var z := -r * 0.85
		var step := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(per_row * 0.55 + 1.0, 0.42, 0.85)
		step.mesh = bm
		step.material_override = concrete
		step.position = Vector3(0, y - 0.21, z)
		root.add_child(step)
		for c in per_row:
			var x := (c - (per_row - 1) * 0.5) * 0.55
			var hard := x > 1.2
			if not hard:
				var pl := MeshInstance3D.new()
				var pm := BoxMesh.new()
				pm.size = Vector3(0.45, 0.05, 0.38)
				pl.mesh = pm
				pl.material_override = plank
				pl.position = Vector3(x, y + 0.43, z + 0.12)
				root.add_child(pl)
			seats.append({"pos": Vector3(x, y, z), "yaw": 0.0, "hard": hard, "standing": false})
	var grass := MeshInstance3D.new()
	var gp := PlaneMesh.new()
	gp.size = Vector2(40, 20)
	grass.mesh = gp
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color(0.2, 0.45, 0.18)
	grass.material_override = gm
	grass.position = Vector3(0, -0.42, 10)
	root.add_child(grass)
	crowd = FanCrowd.new()
	root.add_child(crowd)
	crowd.setup(seats, {"club_a": Color(0.1, 0.55, 0.25), "club_b": Color(0.96, 0.96, 0.96), "temperature": temp, "flag_chance": 0.12})
	var cam := Camera3D.new()
	root.add_child(cam)
	cam.position = Vector3(0, 2.6, 7.5)
	cam.look_at(Vector3(0, 1.2, -1.8))
	cam.fov = 50
func _process(d):
	t += d
	for ev in [[2.0, "chance"], [6.5, "goal_for"], [18.0, "goal_against"]]:
		if t >= ev[0] and not fired.has(ev[1]):
			fired[ev[1]] = true
			crowd.react(ev[1])
	if OS.get_environment("SHOT_AT") != "" and t >= float(OS.get_environment("SHOT_AT")) and not fired.has("shot"):
		fired["shot"] = true
		get_root().get_texture().get_image().save_png(OS.get_environment("SHOT_PATH"))
		quit()
	return false
