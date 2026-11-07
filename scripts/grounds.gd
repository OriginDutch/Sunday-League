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
const MAX_VISIBLE_FANS := 220
const CHAIR_OFFSETS := [-0.75, -0.25, 0.25, 0.75]   # seat positions within a spot
const END_EXTRA := 2.5          # sections behind the goals sit further back (clear of the nets)
const DUGOUT_SECTION := 4         # middle section of the far (main) side
const DUGOUT_CLEAR_X := 7.5       # no standing fans in front of the dugouts

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
var fans: Array[Fan] = []
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
	for i in markers.size():
		markers[i].visible = item != "" and state.can_place(item, i)
		markers[i].material_override = hover_mat if i == hover else free_mat


func rebuild_furniture() -> void:
	for c in furniture_root.get_children():
		c.queue_free()
	if not away_mode:
		active_slots = state.slots
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
			out.append({"pos": base + local, "yaw": yaw})
	return out


## attendance = fans of the club whose ground this is; travelling = your fans at an away ground
## (they stand together behind the near touchline).
func spawn_crowd(attendance: int, travelling: int = 0) -> void:
	clear_crowd()
	var seats := seat_list()
	seats.shuffle()
	var visible_count := mini(attendance, MAX_VISIBLE_FANS)
	var seated := mini(visible_count, seats.size())
	for i in seated:
		var s: Dictionary = seats[i]
		_add_fan(true, s["pos"], s["yaw"])
	for i in mini(travelling, 60):
		var spot := Vector3(randf_range(-14.0, 14.0), 0, Main.HALF_W + STAND_OFFSET + randf_range(-0.4, 0.6))
		_add_fan(false, spot, PI, true)
	# the rest stands along the far touchline in little groups, for free
	var standing := visible_count - seated
	var groups := maxi(1, int(ceil(standing / 5.0)))
	var placed := 0
	for g in groups:
		var side := -1.0 if (g % 3 != 2 or away_mode) else 1.0
		var gx := randf_range(-45.0, 45.0)
		if side < 0.0 and absf(gx) < DUGOUT_CLEAR_X:
			gx = signf(gx + 0.01) * randf_range(DUGOUT_CLEAR_X, 45.0)
		var center := Vector3(gx, 0, side * (Main.HALF_W + STAND_OFFSET))
		var size := mini(randi_range(2, 6), standing - placed)
		for k in size:
			var spot := center + Vector3(randf_range(-1.2, 1.2), 0, randf_range(-0.5, 0.5))
			_add_fan(false, spot, 0.0 if side < 0.0 else PI)
			placed += 1
		if placed >= standing:
			break


func _add_fan(is_seated: bool, spot: Vector3, yaw: float, travelling: bool = false) -> void:
	var f := Fan.new()
	crowd_root.add_child(f)
	var ours := not away_mode or travelling
	f.supports_us = ours
	var club_shirt := Main.HOME_SHIRT if ours else Main.AWAY_SHIRT
	var shirts := [club_shirt, club_shirt, Color(0.95, 0.95, 0.95), Color(0.2, 0.25, 0.35),
		Color(0.55, 0.15, 0.15) if ours else Color(0.15, 0.45, 0.25), Color(0.85, 0.75, 0.3)]
	var skins := [Color(0.98, 0.82, 0.68), Color(0.87, 0.67, 0.5), Color(0.6, 0.42, 0.3), Color(0.42, 0.28, 0.2)]
	f.setup(is_seated, spot, yaw, shirts.pick_random(), skins.pick_random())
	fans.append(f)


func clear_crowd() -> void:
	for f in fans:
		f.queue_free()
	fans.clear()


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
	for f in fans:
		f.react(kind)
	if CHANTS.has(kind) and (kind in ["goal_for", "goal_against", "offside"] or randf() < 0.4):
		var lines: Array = CHANTS[kind]
		for i in mini(2, maxi(1, fans.size() / 15)):
			chant(lines.pick_random())


## A speech bubble above a random fan.
func chant(text: String) -> void:
	if fans.is_empty():
		return
	var f: Fan = fans.pick_random()
	var l := Label3D.new()
	l.text = text
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.font_size = 72
	l.outline_size = 14
	l.pixel_size = 0.012
	l.modulate = Color(1, 1, 0.85)
	l.no_depth_test = true
	l.position = f.position + Vector3(randf_range(-0.3, 0.3), 2.6, 0)
	crowd_root.add_child(l)
	var tw := l.create_tween()
	tw.tween_property(l, "position:y", l.position.y + 1.2, 2.6)
	tw.parallel().tween_property(l, "modulate:a", 0.0, 2.6).set_delay(1.4)
	tw.tween_callback(l.queue_free)


func _process(delta: float) -> void:
	if fans.is_empty():
		return
	chant_timer -= delta
	if chant_timer <= 0.0:
		chant_timer = randf_range(9.0, 20.0)
		chant(CHANTS_IDLE.pick_random())
