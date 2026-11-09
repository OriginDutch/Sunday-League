class_name Grounds
extends Node3D
## Seating slots around the pitch, the furniture you bought, and the crowd.

## Layout (GDD §10a): 28 sections of 11.5 m (9 per touchline, 5 behind each goal).
## Each section = 5 spots of 2 m (a bench or up to 4 chairs) = 20 seats in a row + 1.5 m aisle.
## In front of each section: an ad board and a rope. Dugouts in front of the middle far section.
const SPOT_SPACING := 2.0
const SEAT_OFFSET := 4.0          # metres behind the line to the seat row
const BOARD_OFFSET := 1.4         # ad boards, closest to the pitch
const ROPE_OFFSET := 2.2          # rope barrier
const STAND_OFFSET := 3.0         # standing (non-paying) fans, between rope and seats
const FanCrowd = preload("res://scripts/fan_crowd.gd")
const STANDING_SPACING := 0.6     # standing fans along the touchlines and behind the goals, two rows
const FLAG_CHANCE := 0.03         # per hard-core place (Marcel: starting value), grows with the crowd
const CHAIR_OFFSETS := [-0.75, -0.25, 0.25, 0.75]   # seat positions within a spot
const END_EXTRA := 2.5          # sections behind the goals sit further back (clear of the nets)
const DUGOUT_SECTION := 13        # middle of the West side (camera side), with the tunnel (Marcel 2026-11-08)
const DUGOUT_CLEAR_X := 7.5       # no standing fans in front of the dugouts
# open bleachers (block 4): procedural for now
const BL_FIRST_D := 4.0           # first row, metres behind the line (same as the chairs)
const BL_TREAD := 0.8             # row depth
const BL_RISE := 0.38             # row height step
const BL_FIRST_H := 0.45          # seat height of the first row
const STAND_FRONT_D := 2.9        # The Shed / main stand: front wall this far behind the line (behind the rope)
const StandClip = preload("res://scripts/stand_clip.gdshader")

var state: ClubState
var furniture_root: Node3D
var marker_root: Node3D
var crowd_root: Node3D
var pitchside_root: Node3D
var away_root: Node3D             # extras of the current away ground (clubhouse, hedges, trees)
var board_labels: Array[Label3D] = []
var active_slots: Dictionary = {}   # the furniture on show: yours, or the home club's at an away ground
var away_mode := false
var markers: Array[MeshInstance3D] = []
var section_markers: Array[MeshInstance3D] = []
var crowds: Array = []            # FanCrowd nodes (home crowd, travelling fans)
var _seat_spots: Array = []       # positions of all fans (for chant bubbles)
var free_mat: StandardMaterial3D
var hover_mat: StandardMaterial3D


func setup(s: ClubState) -> void:
	state = s
	furniture_root = Node3D.new()
	add_child(furniture_root)
	marker_root = Node3D.new()
	add_child(marker_root)
	crowd_root = Node3D.new()
	add_child(crowd_root)
	pitchside_root = Node3D.new()
	add_child(pitchside_root)
	away_root = Node3D.new()
	add_child(away_root)
	_build_pitchside()
	active_slots = state.slots
	free_mat = Util.mat(Color(1, 1, 1, 0.35), true)
	hover_mat = Util.mat(Color(1.0, 0.85, 0.1, 0.9), true)
	for i in slot_count():
		var m := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(1.8, 0.04, 0.9)
		m.mesh = bm
		m.material_override = free_mat
		m.position = slot_position(i) + Vector3(0, 0.03, 0)
		m.rotation.y = slot_yaw(i)
		m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		marker_root.add_child(m)
		markers.append(m)
	for sec in section_count():
		var m := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(ClubState.SECTION_W - 0.8, 0.04, 3.2)
		m.mesh = bm
		m.material_override = free_mat
		var f := section_frame(sec)
		m.position = section_point(sec, 0.0, SEAT_OFFSET + 1.2) + Vector3(0, 0.03, 0)
		m.rotation.y = f["yaw"]
		m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		marker_root.add_child(m)
		section_markers.append(m)
	marker_root.visible = false
	rebuild_furniture()


static func section_count() -> int:
	return ClubState.SECTIONS_LONG * 2 + ClubState.SECTIONS_SHORT * 2


static func slot_count() -> int:
	return section_count() * ClubState.SPOTS_PER_SECTION


## Sections 0..8 far touchline (west→east), 9..17 near touchline, 18..22 west end, 23..27 east end.
## Returns the point on the line in front of the section's middle, plus the yaw that faces the pitch.
static func section_frame(sec: int) -> Dictionary:
	var L := ClubState.SECTIONS_LONG
	var S := ClubState.SECTIONS_SHORT
	var w := ClubState.SECTION_W
	if sec < L:
		return {"line": Vector3((sec - (L - 1) * 0.5) * w, 0, -Main.HALF_W), "yaw": 0.0}
	if sec < 2 * L:
		var k := sec - L
		return {"line": Vector3((k - (L - 1) * 0.5) * w, 0, Main.HALF_W), "yaw": PI}
	if sec < 2 * L + S:
		var k := sec - 2 * L
		return {"line": Vector3(-Main.HALF_L - END_EXTRA, 0, (k - (S - 1) * 0.5) * w), "yaw": PI * 0.5}
	var k := sec - 2 * L - S
	return {"line": Vector3(Main.HALF_L + END_EXTRA, 0, (k - (S - 1) * 0.5) * w), "yaw": -PI * 0.5}


## A point in a section's local frame (x along the line, d metres back from it) in world space.
static func section_point(sec: int, x: float, d: float) -> Vector3:
	var f := section_frame(sec)
	return f["line"] + Vector3(x, 0, -d).rotated(Vector3.UP, f["yaw"])


static func slot_position(i: int) -> Vector3:
	var sec := i / ClubState.SPOTS_PER_SECTION
	var k := i % ClubState.SPOTS_PER_SECTION
	var x := (k - (ClubState.SPOTS_PER_SECTION - 1) * 0.5) * SPOT_SPACING
	return section_point(sec, x, SEAT_OFFSET)


static func slot_yaw(i: int) -> float:
	return section_frame(i / ClubState.SPOTS_PER_SECTION)["yaw"]   # face the pitch


func nearest_free_slot(p: Vector3, item: String, max_dist: float = 3.0) -> int:
	if item in ClubState.SECTION_ITEMS:
		var bs := -1
		var bd := 7.0
		for sec in section_count():
			if not state.can_build(item, sec):
				continue
			var d := Util.flat_dist(section_point(sec, 0.0, SEAT_OFFSET + 1.2), p)
			if d < bd:
				bd = d
				bs = sec
		return bs
	var best := -1
	var best_d := max_dist
	for i in slot_count():
		if not state.can_place(item, i):
			continue
		var d := Util.flat_dist(slot_position(i), p)
		if d < best_d:
			best_d = d
			best = i
	return best


func show_markers(on: bool, item: String = "", hover: int = -1) -> void:
	marker_root.visible = on
	var sec_item := item in ClubState.SECTION_ITEMS
	for i in markers.size():
		markers[i].visible = item != "" and not sec_item and state.can_place(item, i)
		markers[i].material_override = hover_mat if i == hover and not sec_item else free_mat
	for i in section_markers.size():
		section_markers[i].visible = sec_item and state.can_build(item, i)
		var m := free_mat
		if item == "hardcore" and state.is_hardcore(i):
			m = _hard_mat()
		section_markers[i].material_override = hover_mat if i == hover and sec_item else m


var _hard_m: StandardMaterial3D


func _hard_mat() -> StandardMaterial3D:
	if _hard_m == null:
		_hard_m = Util.mat(Color(Main.HOME_SHIRT, 0.7), true)
	return _hard_m


func rebuild_furniture() -> void:
	for c in furniture_root.get_children():
		c.queue_free()
	if not away_mode:
		active_slots = state.slots
		for key in state.sections:
			var sec := int(key)
			if state.is_building(sec):
				continue
			var stage := state.stage_of(sec)
			if stage == "bleachers":
				_bleachers(sec, int(state.sections[key]["rows"]))
			else:
				_stand(sec, stage, int(state.sections[key]["rows"]))
		for b in state.builds:
			_construction(int(b["sec"]), int(b["rows"]), state.ready_label(b))
		# stairs where two finished bleacher sections meet (Marcel, 2026-11-07)
		for key in state.sections:
			var a := int(key)
			var nb := _next_in_side(a)
			if nb >= 0 and state.sections.has(str(nb)) and not state.is_building(a) and not state.is_building(nb) \
					and state.stage_of(a) == "bleachers" and state.stage_of(nb) == "bleachers":
				_bleacher_stairs(a, nb, int(state.sections[key]["rows"]), int(state.sections[str(nb)]["rows"]))
	for key in active_slots:
		var i := int(key)
		var item: String = active_slots[key]
		var n_chairs := _chairs(active_slots, str(key))
		var root := Node3D.new()
		root.position = slot_position(i)
		root.rotation.y = slot_yaw(i)
		furniture_root.add_child(root)
		var wood := Color(0.6, 0.42, 0.22)
		var metal := Color(0.3, 0.3, 0.32)
		if item == "bench":
			Util.box(root, Vector3(1.9, 0.08, 0.45), Vector3(0, 0.45, 0), wood)
			Util.box(root, Vector3(0.08, 0.45, 0.4), Vector3(-0.85, 0.22, 0), metal)
			Util.box(root, Vector3(0.08, 0.45, 0.4), Vector3(0.85, 0.22, 0), metal)
		else:
			for c in n_chairs:
				var cx: float = CHAIR_OFFSETS[c]
				Util.box(root, Vector3(0.44, 0.06, 0.46), Vector3(cx, 0.45, 0), Color(0.15, 0.45, 0.25))
				Util.box(root, Vector3(0.44, 0.5, 0.06), Vector3(cx, 0.72, -0.22), Color(0.15, 0.45, 0.25))
				for lx in [-0.18, 0.18]:
					for lz in [-0.2, 0.2]:
						var fx: float = lx
						var fz: float = lz
						Util.box(root, Vector3(0.04, 0.45, 0.04), Vector3(cx + fx, 0.22, fz), metal)


## Ad boards, rope and dugouts — fixed for now (sponsors and barrier upgrades come later).
func _build_pitchside() -> void:
	var half := ClubState.SECTION_W * 0.5
	var post := Color(0.85, 0.85, 0.82)
	var rope := Color(0.9, 0.75, 0.15)
	for sec in section_count():
		var root := Node3D.new()
		var f := section_frame(sec)
		root.position = f["line"]
		root.rotation.y = f["yaw"]
		pitchside_root.add_child(root)
		# rope on posts along the whole section front
		for px in [-half + 0.3, -half * 0.33, half * 0.33, half - 0.3]:
			var x: float = px
			Util.box(root, Vector3(0.06, 1.0, 0.06), Vector3(x, 0.5, -ROPE_OFFSET), post)
		Util.box(root, Vector3(ClubState.SECTION_W - 0.6, 0.03, 0.03), Vector3(0, 0.9, -ROPE_OFFSET), rope)
		if sec == DUGOUT_SECTION:
			for side in [-1.0, 1.0]:
				_dugout(root, side * 3.2)
			continue
		# ad board: blank club board until sponsors exist
		Util.box(root, Vector3(8.0, 0.8, 0.08), Vector3(0, 0.45, -BOARD_OFFSET), Color(0.95, 0.95, 0.93))
		Util.box(root, Vector3(0.06, 0.45, 0.4), Vector3(-3.8, 0.22, -BOARD_OFFSET - 0.2), Color(0.3, 0.3, 0.32))
		Util.box(root, Vector3(0.06, 0.45, 0.4), Vector3(3.8, 0.22, -BOARD_OFFSET - 0.2), Color(0.3, 0.3, 0.32))
		var l := Label3D.new()
		l.text = "YOUR AD HERE"
		l.font_size = 64
		l.pixel_size = 0.009
		l.modulate = Color(0.55, 0.55, 0.55)
		l.outline_size = 0
		l.position = Vector3(0, 0.45, -BOARD_OFFSET + 0.05)
		root.add_child(l)
		board_labels.append(l)


func _dugout(root: Node3D, x: float) -> void:
	var shell := Color(0.2, 0.25, 0.3)
	var roof := Color(0.55, 0.7, 0.8)
	var d := 1.7   # centre, metres back from the line
	Util.box(root, Vector3(2.8, 1.7, 0.08), Vector3(x, 0.85, -d - 0.6), shell)            # back
	Util.box(root, Vector3(0.08, 1.7, 1.2), Vector3(x - 1.4, 0.85, -d), shell)            # sides
	Util.box(root, Vector3(0.08, 1.7, 1.2), Vector3(x + 1.4, 0.85, -d), shell)
	Util.box(root, Vector3(2.9, 0.06, 1.3), Vector3(x, 1.72, -d), roof)                   # roof
	Util.box(root, Vector3(2.5, 0.08, 0.4), Vector3(x, 0.45, -d - 0.3), Color(0.6, 0.42, 0.22))  # bench


## Open aluminium bleachers: one bench plank + footboard per row, frame, back rail.
func _bleachers(sec: int, rows: int) -> void:
	var root := Node3D.new()
	var f := section_frame(sec)
	root.position = f["line"]
	root.rotation.y = f["yaw"]
	furniture_root.add_child(root)
	var alu := Color(0.72, 0.74, 0.76)
	var frame := Color(0.42, 0.44, 0.47)
	var w := 10.2
	for r in rows:
		var d := BL_FIRST_D + r * BL_TREAD
		var h := BL_FIRST_H + r * BL_RISE
		Util.box(root, Vector3(w, 0.05, 0.3), Vector3(0, h, -d), alu)                      # seat plank
		Util.box(root, Vector3(w, 0.04, 0.3), Vector3(0, h - 0.42, -d + 0.3), alu)       # footboard
	var back_d := BL_FIRST_D + (rows - 1) * BL_TREAD + 0.25
	var top_h := BL_FIRST_H + (rows - 1) * BL_RISE
	for x in [-5.0, -2.5, 0.0, 2.5, 5.0]:
		var fx: float = x
		# a sloped stringer and posts down to the ground
		for r in rows:
			var h := BL_FIRST_H + r * BL_RISE
			Util.box(root, Vector3(0.06, h, 0.06), Vector3(fx, h * 0.5, -(BL_FIRST_D + r * BL_TREAD)), frame)
		Util.box(root, Vector3(0.06, 1.0, 0.06), Vector3(fx, top_h + 0.5, -back_d), frame)
	Util.box(root, Vector3(w, 0.05, 0.05), Vector3(0, top_h + 1.0, -back_d), alu)       # back rail
	Util.box(root, Vector3(w, 0.05, 0.05), Vector3(0, top_h + 0.55, -back_d), alu)


# ------------------------------------------------------------------ The Shed / main stand (GDD §10h2)

var _stand_scenes := {}
var _stand_info := {}
var _clip_mats := {}


static func stand_model(stage: String, rows: int, sec: int) -> String:
	if stage == "shed":
		return "res://assets/models/the_shed_%d.glb" % rows
	if stage == "main":
		return "res://assets/models/main_stand_%d%s.glb" % [rows, "_tunnel" if sec == ClubState.TUNNEL_SECTION else ""]
	return ""


## Seats ([x, y, z, row] in the model's space) and the roof profile of a stand variant.
func stand_info(stage: String, rows: int, sec: int) -> Dictionary:
	var path := stand_model(stage, rows, sec)
	if path == "":
		return {}
	if not _stand_info.has(path):
		var f := FileAccess.open(path.replace(".glb", "_seats.json"), FileAccess.READ)
		_stand_info[path] = JSON.parse_string(f.get_as_text()) if f != null else {}
	return _stand_info[path]


## Materials swapped for the sight-line clip shader (same colour, roughness, metal).
func _clip_mat(m: Material) -> Material:
	if not (m is BaseMaterial3D):
		return m
	if not _clip_mats.has(m):
		var b := m as BaseMaterial3D
		var sm := ShaderMaterial.new()
		sm.shader = StandClip
		sm.set_shader_parameter("albedo", b.albedo_color)
		sm.set_shader_parameter("roughness", b.roughness)
		sm.set_shader_parameter("metallic", b.metallic)
		_clip_mats[m] = sm
	return _clip_mats[m]


func clipify(n: Node) -> void:
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		if mi.mesh != null:
			for i in mi.mesh.get_surface_count():
				var m := mi.get_active_material(i)
				if m != null:
					mi.set_surface_override_material(i, _clip_mat(m))
	for c in n.get_children():
		clipify(c)


func _stand(sec: int, stage: String, rows: int) -> void:
	var path := stand_model(stage, rows, sec)
	if not ResourceLoader.exists(path):
		push_warning("Stand model missing (run godot --path . --headless --import): " + path)
		return
	if not _stand_scenes.has(path):
		_stand_scenes[path] = load(path)
	var root := Node3D.new()
	var f := section_frame(sec)
	root.position = f["line"]
	root.rotation.y = f["yaw"]
	furniture_root.add_child(root)
	var inst: Node3D = _stand_scenes[path].instantiate()
	inst.position = Vector3(0, 0, -STAND_FRONT_D)
	root.add_child(inst)
	clipify(inst)
	# side walls (Marcel): full at an open end, none between equal neighbours, between unequal ones only
	# the strip between the lower and the higher roof (drawn by the taller one)
	var me: Dictionary = stand_info(stage, rows, sec).get("profile", {})
	if me.is_empty():
		return
	# along a side the section number goes up towards +x (long sides) or +z (ends)
	var along := Vector3.RIGHT if sec < 2 * ClubState.SECTIONS_LONG else Vector3.BACK
	var next_x := signf(along.rotated(Vector3.UP, -float(f["yaw"])).x)
	for pair in [[_prev_in_side(sec), -next_x], [_next_in_side(sec), next_x]]:
		var nb: int = pair[0]
		var local_x: float = pair[1]
		var them: Dictionary = {}
		if nb >= 0 and state.sections.has(str(nb)) and not state.is_building(nb) and state.stage_of(nb) in ["shed", "main"]:
			them = stand_info(state.stage_of(nb), int(state.sections[str(nb)]["rows"]), nb).get("profile", {})
		var pts := _side_wall(me, them)
		if pts.size() >= 3:
			_wall_prism(root, pts, local_x * (ClubState.SECTION_W * 0.5 + 0.06), Color(String(me.get("color", "#9BA6AA"))))


static func _roof_at(p: Dictionary, y: float) -> float:
	var fy: float = p["front_y"]
	var by: float = p["back_y"]
	return float(p["front_z"]) + (float(p["back_z"]) - float(p["front_z"])) * (y - fy) / (by - fy)


## Side wall polygon in the model's (y back, z up) plane; empty = no wall.
static func _side_wall(me: Dictionary, them: Dictionary) -> PackedVector2Array:
	var wy: float = me["wall_y"]
	if them.is_empty():
		var sy: float = me["side_front_y"]
		return PackedVector2Array([Vector2(sy, 0.0), Vector2(wy, 0.0), Vector2(wy, _roof_at(me, wy)), Vector2(sy, _roof_at(me, sy))])
	if float(them["back_z"]) >= float(me["back_z"]) - 0.01:
		return PackedVector2Array()   # equal or taller neighbour: nothing (the taller one draws the strip)
	var fy: float = me["front_y"]
	var nbw := minf(float(them["wall_y"]), wy)
	return PackedVector2Array([Vector2(fy, _roof_at(them, fy)), Vector2(nbw, _roof_at(them, nbw)), Vector2(nbw, 0.0),
		Vector2(wy, 0.0), Vector2(wy, _roof_at(me, wy)), Vector2(fy, _roof_at(me, fy))])


## A thin wall from a (y back, z up) polygon at local x, in a section root (model sits STAND_FRONT_D back).
func _wall_prism(root: Node3D, pts: PackedVector2Array, x: float, col: Color) -> void:
	var tris := Geometry2D.triangulate_polygon(pts)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var to3 := func(p: Vector2, xx: float) -> Vector3: return Vector3(xx, p.y, -p.x - STAND_FRONT_D)
	for side in [-0.05, 0.05]:
		for i in range(0, tris.size(), 3):
			for j in 3:
				st.add_vertex(to3.call(pts[tris[i + j]], x + side))
	for i in pts.size():
		var a := pts[i]
		var b := pts[(i + 1) % pts.size()]
		st.add_vertex(to3.call(a, x - 0.05)); st.add_vertex(to3.call(b, x - 0.05)); st.add_vertex(to3.call(b, x + 0.05))
		st.add_vertex(to3.call(a, x - 0.05)); st.add_vertex(to3.call(b, x + 0.05)); st.add_vertex(to3.call(a, x + 0.05))
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.roughness = 0.7
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	mi.material_override = _clip_mat(m)
	root.add_child(mi)


static func _prev_in_side(sec: int) -> int:
	var L := ClubState.SECTIONS_LONG
	var S := ClubState.SECTIONS_SHORT
	var starts := [0, L, 2 * L, 2 * L + S]
	return -1 if sec in starts else sec - 1


## The next section along the same side, or -1 at the end of a side.
static func _next_in_side(sec: int) -> int:
	var L := ClubState.SECTIONS_LONG
	var S := ClubState.SECTIONS_SHORT
	var ends := [L, 2 * L, 2 * L + S, 2 * L + 2 * S]
	return -1 if (sec + 1) in ends else sec + 1


## Stair aisle in the gap between two bleacher sections, up to the lower of the two;
## the taller one gets a side rail above that.
func _bleacher_stairs(a: int, b: int, rows_a: int, rows_b: int) -> void:
	var root := Node3D.new()
	var f := section_frame(a)
	root.position = f["line"]
	root.rotation.y = f["yaw"]
	furniture_root.add_child(root)
	var x_axis := Vector3(1, 0, 0).rotated(Vector3.UP, f["yaw"])
	var side := signf(x_axis.dot(section_frame(b)["line"] - f["line"]))
	var cx := side * ClubState.SECTION_W * 0.5      # middle of the gap
	var alu := Color(0.72, 0.74, 0.76)
	var frame := Color(0.42, 0.44, 0.47)
	var low := mini(rows_a, rows_b)
	# two steps per row, from footboard level up to the top seat row of the lower section
	var steps := low * 2
	for i in steps:
		var h := (BL_FIRST_H - 0.42) + (i + 1) * (BL_RISE * 0.5)
		var d := BL_FIRST_D + 0.3 - 0.5 + i * (BL_TREAD * 0.5)
		Util.box(root, Vector3(1.2, 0.05, BL_TREAD * 0.5), Vector3(cx, h, -d), alu)
		Util.box(root, Vector3(0.05, h, 0.05), Vector3(cx - 0.6, h * 0.5, -d), frame)
		Util.box(root, Vector3(0.05, h, 0.05), Vector3(cx + 0.6, h * 0.5, -d), frame)
	# side rail on the taller section's edge above the shared height
	if rows_a != rows_b:
		var tall_x := cx - side * 0.65 if rows_a > rows_b else cx + side * 0.65
		var hi := maxi(rows_a, rows_b)
		for r in range(low, hi):
			var h := BL_FIRST_H + r * BL_RISE
			Util.box(root, Vector3(0.05, 0.9, 0.05), Vector3(tall_x, h + 0.45, -(BL_FIRST_D + r * BL_TREAD)), frame)
		var r0 := BL_FIRST_D + low * BL_TREAD
		var r1 := BL_FIRST_D + (hi - 1) * BL_TREAD
		var h0 := BL_FIRST_H + low * BL_RISE + 0.9
		var h1 := BL_FIRST_H + (hi - 1) * BL_RISE + 0.9
		var mid := Vector3(tall_x, (h0 + h1) * 0.5, -(r0 + r1) * 0.5)
		var len := Vector2(r1 - r0, h1 - h0).length() + 0.1
		var rail := Util.box(root, Vector3(0.05, 0.05, len), mid, alu)
		if rail is Node3D:
			(rail as Node3D).rotation.x = atan2(h1 - h0, r1 - r0)


## Construction site: fence around the footprint, a crane-ish mast and a sign with the ready date.
func _construction(sec: int, rows: int, ready: String) -> void:
	var root := Node3D.new()
	var f := section_frame(sec)
	root.position = f["line"]
	root.rotation.y = f["yaw"]
	furniture_root.add_child(root)
	var depth := rows * BL_TREAD + 1.0
	var d0 := BL_FIRST_D - 0.6
	var fence := Color(0.95, 0.55, 0.15)
	Util.box(root, Vector3(10.6, 1.1, 0.05), Vector3(0, 0.55, -d0), fence)
	Util.box(root, Vector3(10.6, 1.1, 0.05), Vector3(0, 0.55, -d0 - depth), fence)
	Util.box(root, Vector3(0.05, 1.1, depth), Vector3(-5.3, 0.55, -d0 - depth * 0.5), fence)
	Util.box(root, Vector3(0.05, 1.1, depth), Vector3(5.3, 0.55, -d0 - depth * 0.5), fence)
	# half-built frame inside
	for x in [-4.0, 0.0, 4.0]:
		var fx: float = x
		Util.box(root, Vector3(0.08, 1.6, 0.08), Vector3(fx, 0.8, -d0 - depth * 0.6), Color(0.42, 0.44, 0.47))
	Util.box(root, Vector3(0.6, 0.6, 0.6), Vector3(3.0, 0.3, -d0 - depth * 0.35), Color(0.55, 0.4, 0.25))   # pallet
	var l := Label3D.new()
	l.text = "UNDER CONSTRUCTION\nready: %s" % ready
	l.font_size = 64
	l.pixel_size = 0.01
	l.outline_size = 10
	l.position = Vector3(0, 2.2, -d0)
	root.add_child(l)


static func _chairs(slots: Dictionary, key: String) -> int:
	if not slots.has(key):
		return 0
	var v: String = slots[key]
	return int(v.substr(7)) if v.begins_with("chairs:") else 0


## Your own ground: your furniture, blank boards, no away extras.
func use_home() -> void:
	away_mode = false
	active_slots = state.slots
	for c in away_root.get_children():
		c.queue_free()
	for l in board_labels:
		l.text = "YOUR AD HERE"
	rebuild_furniture()


## A simple seeded away ground (GDD block 3, first version): the same club always gets the same
## ground. Benches/chairs, a clubhouse, hedges and trees; bigger with a stronger club / higher level.
## Returns how many home fans turn up.
func use_away(team_name: String, strength: float, level: int = 0) -> int:
	away_mode = true
	for c in away_root.get_children():
		c.queue_free()
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(team_name)
	var size := clampf((strength - 0.92) / 0.16, 0.0, 1.0) + level * 0.5   # 0..1 at the bottom level
	# furniture: a few spots on the far side around halfway, sometimes some behind a goal
	var slots := {}
	var spots := rng.randi_range(2, 5) + int(size * 6.0)
	var far_secs := [4, 3, 5, 2, 6]
	var placed := 0
	for sec in far_secs:
		for k in ClubState.SPOTS_PER_SECTION:
			if placed >= spots:
				break
			if sec == DUGOUT_SECTION and rng.randf() < 0.5:
				continue
			if rng.randf() < 0.75:
				slots[str(sec * ClubState.SPOTS_PER_SECTION + k)] = "bench" if rng.randf() < 0.5 else "chairs:%d" % rng.randi_range(2, 4)
				placed += 1
	if rng.randf() < 0.35:
		var end_sec := 2 * ClubState.SECTIONS_LONG + rng.randi_range(0, 2 * ClubState.SECTIONS_SHORT - 1)
		for k in rng.randi_range(1, 3):
			slots[str(end_sec * ClubState.SPOTS_PER_SECTION + k + 1)] = "bench"
	active_slots = slots
	# boards: some carry the home club's name, the rest stay blank
	for l in board_labels:
		l.text = team_name.to_upper() if rng.randf() < 0.3 else ""
	# clubhouse behind one corner
	var cx := (Main.HALF_L - 6.0) * (1.0 if rng.randf() < 0.5 else -1.0)
	var cz := -(Main.HALF_W + 14.0)
	var house := Node3D.new()
	house.position = Vector3(cx, 0, cz)
	house.rotation.y = rng.randf_range(-0.2, 0.2)
	away_root.add_child(house)
	var walls: Color = [Color(0.75, 0.68, 0.55), Color(0.6, 0.35, 0.25), Color(0.85, 0.85, 0.8), Color(0.45, 0.5, 0.45)][rng.randi_range(0, 3)]
	var w := rng.randf_range(10.0, 16.0) + size * 6.0
	Util.box(house, Vector3(w, 3.0, 7.0), Vector3(0, 1.5, 0), walls)
	Util.box(house, Vector3(w + 0.6, 0.3, 7.6), Vector3(0, 3.15, 0), Color(0.3, 0.3, 0.32))
	Util.box(house, Vector3(1.2, 2.1, 0.1), Vector3(-w * 0.25, 1.05, 3.52), Color(0.25, 0.18, 0.12))
	for wx in [0.0, w * 0.25]:
		var x: float = wx
		Util.box(house, Vector3(1.8, 1.0, 0.1), Vector3(x, 1.8, 3.52), Color(0.6, 0.75, 0.85))
	var sign := Label3D.new()
	sign.text = team_name.to_upper()
	sign.font_size = 72
	sign.pixel_size = 0.012
	sign.outline_size = 8
	sign.position = Vector3(0, 3.7, 3.6)
	house.add_child(sign)
	# hedges along one or two sides, and a few extra trees
	if rng.randf() < 0.6:
		Util.box(away_root, Vector3(2.0 * Main.HALF_L + 30.0, 1.6, 1.2), Vector3(0, 0.8, Main.HALF_W + 12.0), Color(0.2, 0.4, 0.2))
	if rng.randf() < 0.5:
		var hx := (Main.HALF_L + 12.0) * (1.0 if rng.randf() < 0.5 else -1.0)
		Util.box(away_root, Vector3(1.2, 1.6, 2.0 * Main.HALF_W + 20.0), Vector3(hx, 0.8, 0), Color(0.2, 0.4, 0.2))
	for i in rng.randi_range(3, 8):
		var p := Vector3(rng.randf_range(-Main.HALF_L - 25.0, Main.HALF_L + 25.0), 0, (Main.HALF_W + rng.randf_range(16.0, 30.0)) * (1.0 if rng.randf() < 0.5 else -1.0))
		var sc := rng.randf_range(0.8, 1.5)
		Util.cylinder(away_root, 0.25 * sc, 0.3 * sc, 1.6 * sc, p + Vector3(0, 0.8 * sc, 0), Color(0.4, 0.27, 0.15), 6)
		Util.cylinder(away_root, 0.0, 1.8 * sc, 3.2 * sc, p + Vector3(0, 3.0 * sc, 0), Color(0.2, 0.45, 0.2), 7)
	rebuild_furniture()
	return rng.randi_range(6, 18) + int(size * 25.0)


## World positions (and facing) of every seat you own.
func seat_list() -> Array:
	var out := []
	for key in active_slots:
		var i := int(key)
		var base := slot_position(i)
		var yaw := slot_yaw(i)
		var item: String = active_slots[key]
		var n := ClubState.BENCH_SEATS if item == "bench" else _chairs(active_slots, str(key))
		var offsets: Array = CHAIR_OFFSETS.slice(0, n)
		for o in offsets:
			var ox: float = o
			var local := Vector3(ox, 0.0, 0).rotated(Vector3.UP, yaw)
			out.append({"pos": base + local, "yaw": yaw, "sec": i / ClubState.SPOTS_PER_SECTION})
	if not away_mode:
		for key in state.sections:
			var sec := int(key)
			if state.is_building(sec):
				continue
			var yaw: float = section_frame(sec)["yaw"]
			var stage := state.stage_of(sec)
			if stage != "bleachers":
				var info := stand_info(stage, int(state.sections[key]["rows"]), sec)
				var mult: float = ClubState.STAGES[stage]["ticket"]
				var fr := section_frame(sec)
				var prof: Dictionary = info.get("profile", {})
				for sv in info.get("seats", []):
					var lp := Vector3(float(sv[0]), float(sv[1]) - 0.45, float(sv[2]) - STAND_FRONT_D)
					# room between the row and the roof above it (flags only where they fit, Marcel 2026-11-09)
					var floor_h := float(sv[1]) - 0.44
					var head := _roof_at(prof, -float(sv[2])) - floor_h if not prof.is_empty() else 99.0
					out.append({"pos": fr["line"] + lp.rotated(Vector3.UP, yaw), "yaw": yaw, "sec": sec, "mult": mult, "headroom": head})
				continue
			for r in int(state.sections[key]["rows"]):
				for i in ClubState.BLEACHER_SEATS_PER_ROW:
					var x := -4.75 + i * 0.5
					var p := section_point(sec, x, BL_FIRST_D + r * BL_TREAD) + Vector3(0, BL_FIRST_H + r * BL_RISE - 0.45, 0)
					out.append({"pos": p, "yaw": yaw, "sec": sec})
	return out


## attendance = fans of the club whose ground this is; travelling = your fans at an away ground
## (they stand together behind the near touchline). Every fan is drawn (crowd v2, scripts/fan_crowd.gd):
## the seats fill first, the rest stands along the touchlines and behind the goals.
func spawn_crowd(attendance: int, travelling: int = 0) -> void:
	clear_crowd()
	var seats := seat_list()
	seats.shuffle()
	# covered seats fill first, the dearest stand first (Marcel 2026-11-08); shuffled within each group
	var groups := {}
	for st in seats:
		var m: float = st.get("mult", 1.0)
		if not groups.has(m):
			groups[m] = []
		groups[m].append(st)
	var keys := groups.keys()
	keys.sort()
	keys.reverse()
	seats = []
	for m in keys:
		seats.append_array(groups[m])
	var seated := mini(attendance, seats.size())
	var ours := not away_mode
	var places := []
	for k in seated:
		var st: Dictionary = seats[k]
		var hard := ours and state.is_hardcore(int(st.get("sec", -1)))
		places.append({"pos": st["pos"], "yaw": st["yaw"], "hard": hard, "standing": false, "headroom": st.get("headroom", 99.0)})
	var standing_spots := _standing_spots(away_mode)
	standing_spots.shuffle()
	for k in mini(attendance - seated, standing_spots.size()):
		places.append(standing_spots[k])
	if not places.is_empty():
		_crowd(places, ours, attendance)
	if travelling > 0:
		var near := []
		for k in mini(travelling, 120):
			var x := 9.0 + (k / 2) * STANDING_SPACING + randf_range(-0.1, 0.1)   # beside the dugouts (West middle)
			near.append({"pos": Vector3(x, 0, Main.HALF_W + STAND_OFFSET + (k % 2) * 0.5), "yaw": PI, "hard": false, "standing": true})
		_crowd(near, true, travelling)
	for pl in places:
		_seat_spots.append(pl["pos"])


func _crowd(places: Array, ours: bool, attendance: int) -> void:
	var c := FanCrowd.new()
	crowd_root.add_child(c)
	c.setup(places, {
		"club_a": Main.HOME_SHIRT if ours else Main.AWAY_SHIRT, "club_b": Color(0.96, 0.96, 0.96), "ours": ours,
		"temperature": state.temperature, "flag_chance": FLAG_CHANCE * clampf(1.0 + attendance / 5000.0, 1.0, 3.0)})
	crowds.append(c)


## Free standing places: two rows between the rope and the seats on every side, not in front of the
## dugouts, not where bleachers stand.
func _standing_spots(away: bool) -> Array:
	var out := []
	var sides := [[-1.0, Main.HALF_L], [1.0, Main.HALF_L]]
	for side in sides:
		var z: float = side[0] * (Main.HALF_W + STAND_OFFSET)
		var x := -Main.HALF_L + 1.0
		while x < Main.HALF_L - 1.0:
			if not (side[0] > 0.0 and absf(x) < DUGOUT_CLEAR_X) and not (away and side[0] > 0.0 and x > 8.0 and x < 46.0):
				for row in 2:
					var zz: float = z + side[0] * row * 0.5
					out.append({"pos": Vector3(x + randf_range(-0.08, 0.08), 0, zz), "yaw": 0.0 if side[0] < 0.0 else PI,
						"hard": false, "standing": true})
			x += STANDING_SPACING
	for end in [-1.0, 1.0]:
		var xx: float = end * (Main.HALF_L + STAND_OFFSET)
		var z2 := -Main.HALF_W + 1.0
		while z2 < Main.HALF_W - 1.0:
			for row in 2:
				out.append({"pos": Vector3(xx + end * row * 0.5, 0, z2 + randf_range(-0.08, 0.08)), "yaw": -end * PI * 0.5,
					"hard": false, "standing": true})
			z2 += STANDING_SPACING
	return out


func clear_crowd() -> void:
	for c in crowds:
		c.queue_free()
	crowds.clear()
	_seat_spots.clear()


const CHANTS_IDLE := ["COME ON YOU GREENS!", "WHO ARE YA?!", "SUNDAY LEAGUE, SUNDAY LEAGUE!",
	"PASS IT!", "SHOOOOT!", "Is the bar open at half time?", "We love you lads!", "Get stuck in!",
	"My nan's quicker than him", "REF! REF!", "Wake up, number 4!", "Who's got the crisps?"]
const CHANTS := {
	"goal_for": ["GET IN!!", "YESSSSS!", "WHAT A GOAL!", "ONE-NIL TO THE SUNDAY BOYS!", "SCENES!"],
	"goal_against": ["Shocking.", "WAKE UP!", "Where was the defence?!", "Keeper's asleep!", "Oh come ON"],
	"save": ["What a save!", "HANDS LIKE BUCKETS!", "Keeper keeper keeper!"],
	"offside": ["OFFSIDE?! NEVER!", "REF YOU'RE BLIND!", "Get some glasses!", "He was level!"],
	"tackle": ["GET IN THERE!", "Proper tackle!", "Have some of that!"],
	"chance": ["Ooooh!", "So close!"],
}
var chant_timer := 3.0
var bubbles: Array[Label3D] = []


func react(kind: String) -> void:
	for c in crowds:
		c.react(kind)
	if CHANTS.has(kind) and (kind in ["goal_for", "goal_against", "offside"] or randf() < 0.4):
		var lines: Array = CHANTS[kind]
		for i in mini(3, maxi(1, _seat_spots.size() / 15)):
			chant(lines.pick_random())


## A speech bubble above a random fan.
func chant(text: String) -> void:
	if _seat_spots.is_empty():
		return
	var at: Vector3 = _seat_spots.pick_random()
	var l := Label3D.new()
	l.text = text
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.font_size = 72
	l.outline_size = 14
	l.pixel_size = 0.012
	l.modulate = Color(1, 1, 0.85)
	l.no_depth_test = true
	l.position = at + Vector3(randf_range(-0.3, 0.3), 2.6, 0)
	crowd_root.add_child(l)
	var tw := l.create_tween()
	tw.tween_property(l, "position:y", l.position.y + 1.2, 2.6)
	tw.parallel().tween_property(l, "modulate:a", 0.0, 2.6).set_delay(1.4)
	tw.tween_callback(l.queue_free)


func _process(delta: float) -> void:
	if _seat_spots.is_empty():
		return
	chant_timer -= delta
	if chant_timer <= 0.0:
		chant_timer = randf_range(9.0, 20.0)
		chant(CHANTS_IDLE.pick_random())
