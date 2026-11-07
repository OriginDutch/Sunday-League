class_name Grounds
extends Node3D
## Seating slots around the pitch, the furniture you bought, and the crowd.

const SLOT_SPACING := 4.0
const SLOT_OFFSET := 4.0          # metres behind the touchline
const STAND_OFFSET := 1.8         # standing (non-paying) fans, between line and seats
const MAX_VISIBLE_FANS := 220
const CHAIR_OFFSETS := [-0.82, -0.27, 0.27, 0.82]   # seat positions within a section (bench or up to 4 chairs)

var state: ClubState
var furniture_root: Node3D
var marker_root: Node3D
var crowd_root: Node3D
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
	free_mat = Util.mat(Color(1, 1, 1, 0.35), true)
	hover_mat = Util.mat(Color(1.0, 0.85, 0.1, 0.9), true)
	for i in slot_count():
		var m := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(2.6, 0.04, 0.9)
		m.mesh = bm
		m.material_override = free_mat
		m.position = slot_position(i) + Vector3(0, 0.03, 0)
		m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		marker_root.add_child(m)
		markers.append(m)
	marker_root.visible = false
	rebuild_furniture()


static func slot_count() -> int:
	return ClubState.SLOTS_PER_SIDE * 2


## Slots 0..19 along the far touchline, 20..39 along the near one.
static func slot_position(i: int) -> Vector3:
	var per := ClubState.SLOTS_PER_SIDE
	var side := -1.0 if i < per else 1.0
	var k := i % per
	var x := (k - (per - 1) * 0.5) * SLOT_SPACING
	return Vector3(x, 0, side * (Main.HALF_W + SLOT_OFFSET))


static func slot_yaw(i: int) -> float:
	return 0.0 if i < ClubState.SLOTS_PER_SIDE else PI   # face the pitch


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
	for key in state.slots:
		var i := int(key)
		var item: String = state.slots[key]
		var n_chairs := state.chairs_in(str(key))
		var root := Node3D.new()
		root.position = slot_position(i)
		root.rotation.y = slot_yaw(i)
		furniture_root.add_child(root)
		var wood := Color(0.6, 0.42, 0.22)
		var metal := Color(0.3, 0.3, 0.32)
		if item == "bench":
			Util.box(root, Vector3(2.2, 0.08, 0.45), Vector3(0, 0.45, 0), wood)
			Util.box(root, Vector3(0.08, 0.45, 0.4), Vector3(-0.95, 0.22, 0), metal)
			Util.box(root, Vector3(0.08, 0.45, 0.4), Vector3(0.95, 0.22, 0), metal)
		else:
			for c in n_chairs:
				var cx: float = CHAIR_OFFSETS[c]
				Util.box(root, Vector3(0.5, 0.06, 0.5), Vector3(cx, 0.45, 0), Color(0.15, 0.45, 0.25))
				Util.box(root, Vector3(0.5, 0.5, 0.06), Vector3(cx, 0.72, -0.22), Color(0.15, 0.45, 0.25))
				for lx in [-0.2, 0.2]:
					for lz in [-0.2, 0.2]:
						var fx: float = lx
						var fz: float = lz
						Util.box(root, Vector3(0.04, 0.45, 0.04), Vector3(cx + fx, 0.22, fz), metal)


## World positions (and facing) of every seat you own.
func seat_list() -> Array:
	var out := []
	for key in state.slots:
		var i := int(key)
		var base := slot_position(i)
		var yaw := slot_yaw(i)
		var offsets: Array = CHAIR_OFFSETS.slice(0, state.seats_in(str(key)))
		for o in offsets:
			var ox: float = o
			var local := Vector3(ox, 0.0, 0).rotated(Vector3.UP, yaw)
			out.append({"pos": base + local, "yaw": yaw})
	return out


func spawn_crowd(attendance: int) -> void:
	clear_crowd()
	var seats := seat_list()
	seats.shuffle()
	var visible_count := mini(attendance, MAX_VISIBLE_FANS)
	var seated := mini(visible_count, seats.size())
	for i in seated:
		var s: Dictionary = seats[i]
		_add_fan(true, s["pos"], s["yaw"])
	# the rest stands along the far touchline in little groups, for free
	var standing := visible_count - seated
	var groups := maxi(1, int(ceil(standing / 5.0)))
	var placed := 0
	for g in groups:
		var gx := randf_range(-35.0, 35.0)
		var side := -1.0 if (g % 3 != 2) else 1.0
		var center := Vector3(gx, 0, side * (Main.HALF_W + STAND_OFFSET))
		var size := mini(randi_range(2, 6), standing - placed)
		for k in size:
			var spot := center + Vector3(randf_range(-1.2, 1.2), 0, randf_range(-0.5, 0.5))
			_add_fan(false, spot, 0.0 if side < 0.0 else PI)
			placed += 1
		if placed >= standing:
			break


func _add_fan(is_seated: bool, spot: Vector3, yaw: float) -> void:
	var f := Fan.new()
	crowd_root.add_child(f)
	var shirts := [Main.HOME_SHIRT, Main.HOME_SHIRT, Color(0.95, 0.95, 0.95), Color(0.2, 0.25, 0.35),
		Color(0.55, 0.15, 0.15), Color(0.85, 0.75, 0.3)]
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
