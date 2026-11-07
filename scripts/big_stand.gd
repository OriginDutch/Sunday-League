class_name BigStand
extends Node3D
## Big two-tier stand POC (GDD §10i).
## Structure comes from big_stand.glb (built by tools/blender/build_big_stand.py).
## Seats and fans come from big_stand_layout.json and are drawn with MultiMesh, so ~6.5k seats
## and ~1.9k fans stay cheap, and club colours can change at runtime (set_club_colours).
## Local axes: x along the touchline, y up, +z towards the pitch; origin = front face, centre, ground.

const GLB := "res://assets/models/big_stand.glb"
const LAYOUT := "res://assets/models/big_stand_layout.json"
const SHADER := preload("res://scripts/instanced_parts.gdshader")
const PREMIUM := Color("3a3f44")

const PART_CLUB := Color(1, 0, 0)    # club colour / shirt
const PART_SKIN := Color(0, 1, 0)
const PART_FIXED := Color(0, 0, 1)   # seat bracket / trousers

var primary := Color("2f6db5")
var secondary := Color("ece8dd")
var _layout: Dictionary
var _seats: MultiMesh
var _fans: MultiMesh
var _structure: Node3D


func _ready() -> void:
	var scene := load(GLB) as PackedScene
	if scene == null:
		push_error("big_stand.glb is not imported yet: open the project in the Godot editor once")
		_structure = Node3D.new()
	else:
		_structure = scene.instantiate()
	add_child(_structure)
	var f := FileAccess.open(LAYOUT, FileAccess.READ)
	_layout = JSON.parse_string(f.get_as_text())
	primary = Color(_layout["primary"])
	secondary = Color(_layout["secondary"])

	_seats = _make_multimesh(_seat_mesh(), _layout["seats"], Color("4a4f52"), 0.45)
	_fans = _make_multimesh(_fan_mesh(), _layout["fans"], Color("2e3440"), 0.8)
	_apply_colours()


## Club colours upgrade (GDD §10f): recolours seats (incl. the club name) and fans in club shirts.
func set_club_colours(p: Color, s: Color) -> void:
	primary = p
	secondary = s
	_apply_colours()


func _apply_colours() -> void:
	_recolour_structure(_structure)
	var seats: Array = _layout["seats"]
	for i in seats.size():
		var kind := int(seats[i][3])
		var c: Color = [primary, secondary, PREMIUM][kind]
		_seats.set_instance_custom_data(i, _lin(c, 0.0))
	var fans: Array = _layout["fans"]
	for i in fans.size():
		var kind := int(fans[i][3])
		var c: Color = primary if kind == 0 else (secondary if kind == 1 else Color(fans[i][4]))
		_fans.set_instance_custom_data(i, _lin(c, int(fans[i][5]) * 0.5))


## Structure materials named Club_Primary_* / Club_Secondary_* (fascia, trim) follow the club colours.
func _recolour_structure(node: Node) -> void:
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		for i in mi.mesh.get_surface_count():
			var m := mi.mesh.surface_get_material(i) as BaseMaterial3D
			if m == null:
				continue
			if m.resource_name.begins_with("Club_Primary"):
				m.albedo_color = primary
			elif m.resource_name.begins_with("Club_Secondary"):
				m.albedo_color = secondary
	for c in node.get_children():
		_recolour_structure(c)


func _lin(c: Color, a: float) -> Color:
	var l := c.srgb_to_linear()
	return Color(l.r, l.g, l.b, a)


func _make_multimesh(mesh: Mesh, items: Array, fixed: Color, rough: float) -> MultiMesh:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = mesh
	mm.instance_count = items.size()
	for i in items.size():
		var it: Array = items[i]
		mm.set_instance_transform(i, Transform3D(Basis(), Vector3(it[0], it[1], it[2])))
	var mat := ShaderMaterial.new()
	mat.shader = SHADER
	mat.set_shader_parameter("fixed_color", fixed)
	mat.set_shader_parameter("roughness_value", rough)
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.material_override = mat
	add_child(mmi)
	return mm


# ------------------------------------------------------------------ meshes (same shapes as the Blender script)

func _seat_mesh() -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	_box(st, Vector3(0.06, 0.3, 0.06), Vector3(0, 0.15, 0), Basis(), PART_FIXED)
	_box(st, Vector3(0.44, 0.05, 0.38), Vector3(0, 0.42, 0.04), Basis(Vector3.RIGHT, deg_to_rad(-4)), PART_CLUB)
	_box(st, Vector3(0.44, 0.36, 0.05), Vector3(0, 0.62, -0.17), Basis(Vector3.RIGHT, deg_to_rad(-12)), PART_CLUB)
	return st.commit()


func _fan_mesh() -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	_box(st, Vector3(0.32, 0.15, 0.44), Vector3(0, 0.52, 0.16), Basis(), PART_FIXED)
	_box(st, Vector3(0.26, 0.45, 0.13), Vector3(0, 0.24, 0.36), Basis(), PART_FIXED)
	_box(st, Vector3(0.32, 0.5, 0.22), Vector3(0, 0.82, -0.06), Basis(), PART_CLUB)
	for s in [-1, 1]:
		_box(st, Vector3(0.08, 0.44, 0.12), Vector3(s * 0.2, 0.81, 0), Basis(), PART_CLUB)
	_ico(st, 0.11, Vector3(0, 1.21, -0.04), PART_SKIN)
	return st.commit()


func _box(st: SurfaceTool, size: Vector3, center: Vector3, basis: Basis, part: Color) -> void:
	var h := size * 0.5
	var c: Array[Vector3] = []
	for x in [-h.x, h.x]:
		for y in [-h.y, h.y]:
			for z in [-h.z, h.z]:
				c.append(center + basis * Vector3(x, y, z))
	# corner index = ix*4 + iy*2 + iz
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


## Adds one flat-shaded triangle facing away from `inside` (Godot front faces are clockwise).
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
