extends MultiMeshInstance3D
## Every occupied seat gets a fan, drawn as one MultiMesh (Marcel, 2026-11-08: "ik wil ze zeker wél zien").
## The fans react to goals through shader uniforms. Loaded by path (no class_name).

const SHADER := preload("res://scripts/crowd.gdshader")
const PART_SHIRT := Color(1, 0, 0)
const PART_SKIN := Color(0, 1, 0)
const PART_TROUSERS := Color(0, 0, 1)
const TROUSERS := ["2e3440", "3b4a6b", "4a4a4a", "5a4632", "1f2a44", "6b6b5e"]

var supports_us := true
var _mat: ShaderMaterial
var _jump_t := 0.0
var _slump_t := 0.0


## seats: [{pos, yaw}], shirts: Array[Color] to pick from.
func setup(seats: Array, shirts: Array, ours: bool) -> void:
	supports_us = ours
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = _fan_mesh()
	mm.instance_count = seats.size()
	for i in seats.size():
		var s: Dictionary = seats[i]
		var basis := Basis(Vector3.UP, float(s["yaw"]))
		mm.set_instance_transform(i, Transform3D(basis, s["pos"]))
		var shirt: Color = shirts[randi() % shirts.size()]
		var l := shirt.srgb_to_linear()
		var skin := randi() % 3
		var trousers := randi() % TROUSERS.size()
		mm.set_instance_custom_data(i, Color(l.r, l.g, l.b, float(skin + 3 * trousers) / 32.0))
	multimesh = mm
	_mat = ShaderMaterial.new()
	_mat.shader = SHADER
	var pal := PackedVector3Array()
	for h in TROUSERS:
		var c := Color(h).srgb_to_linear()
		pal.append(Vector3(c.r, c.g, c.b))
	_mat.set_shader_parameter("trousers_palette", pal)
	material_override = _mat
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func react(kind: String) -> void:
	if not supports_us:
		kind = {"goal_for": "goal_against", "goal_against": "goal_for", "save": "chance", "chance": "save"}.get(kind, kind)
	match kind:
		"goal_for":
			_jump_t = 2.4
			_slump_t = 0.0
		"goal_against":
			_slump_t = 2.2
		"save", "tackle", "chance":
			_jump_t = maxf(_jump_t, 0.5)


func _process(delta: float) -> void:
	if _mat == null:
		return
	_jump_t = maxf(0.0, _jump_t - delta)
	_slump_t = maxf(0.0, _slump_t - delta)
	_mat.set_shader_parameter("jump", clampf(_jump_t / 0.4, 0.0, 1.0))
	_mat.set_shader_parameter("slump", clampf(_slump_t / 0.4, 0.0, 1.0))


# ------------------------------------------------------------------ mesh (same seated figure as the big stand)

func _fan_mesh() -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	_box(st, Vector3(0.32, 0.15, 0.44), Vector3(0, 0.52, 0.16), PART_TROUSERS)
	_box(st, Vector3(0.26, 0.45, 0.13), Vector3(0, 0.24, 0.36), PART_TROUSERS)
	_box(st, Vector3(0.32, 0.5, 0.22), Vector3(0, 0.82, -0.06), PART_SHIRT)
	for s in [-1, 1]:
		_box(st, Vector3(0.08, 0.44, 0.12), Vector3(s * 0.2, 0.81, 0), PART_SHIRT)
	_ico(st, 0.11, Vector3(0, 1.21, -0.04), PART_SKIN)
	return st.commit()


func _box(st: SurfaceTool, size: Vector3, center: Vector3, part: Color) -> void:
	var h := size * 0.5
	var c: Array[Vector3] = []
	for x in [-h.x, h.x]:
		for y in [-h.y, h.y]:
			for z in [-h.z, h.z]:
				c.append(center + Vector3(x, y, z))
	for q in [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]:
		_tri(st, c[q[0]], c[q[1]], c[q[2]], center, part)
		_tri(st, c[q[0]], c[q[2]], c[q[3]], center, part)


func _ico(st: SurfaceTool, r: float, center: Vector3, part: Color) -> void:
	var t := (1.0 + sqrt(5.0)) / 2.0
	var v: Array[Vector3] = [
		Vector3(-1, t, 0), Vector3(1, t, 0), Vector3(-1, -t, 0), Vector3(1, -t, 0),
		Vector3(0, -1, t), Vector3(0, 1, t), Vector3(0, -1, -t), Vector3(0, 1, -t),
		Vector3(t, 0, -1), Vector3(t, 0, 1), Vector3(-t, 0, -1), Vector3(-t, 0, 1)]
	var f := [[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4],
		[11, 10, 2], [10, 7, 6], [7, 1, 8], [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
		[4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]]
	for tri in f:
		_tri(st, center + v[tri[0]].normalized() * r, center + v[tri[1]].normalized() * r,
			center + v[tri[2]].normalized() * r, center, part)


func _tri(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, inside: Vector3, part: Color) -> void:
	var n := (b - a).cross(c - a)
	if n.dot((a + b + c) / 3.0 - inside) < 0.0:
		var tmp := b
		b = c
		c = tmp
		n = -n
	n = n.normalized()
	for p in [a, c, b]:
		st.set_normal(n)
		st.set_color(part)
		st.add_vertex(p)
