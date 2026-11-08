extends Node3D
## Crowd v2 (Marcel, 2026-11-08): real fan figures — men, women, children — with baked animations
## (sit, stand up, jump, wave arms, clap, fist pump, scarf up / twirl, flags, despair), clothes by weather,
## and a hard core (flags, scarves, club wear, a share always standing). Drawn as one MultiMesh per
## body + hairstyle combination; everything else (accessories, colours, animation) is per-instance data.
## Loaded by path (no class_name): `const FanCrowd := preload("res://scripts/fan_crowd.gd")`.

const SHADER := preload("res://scripts/fan_crowd.gdshader")
const DATA_PATH := "res://assets/crowd/fans.json"
const CREST := preload("res://assets/ui/icons/crest_home.svg")

const WOMEN := 0.15          # Marcel: ~15% women, ~12% children
const CHILDREN := 0.12
const HC_STANDING := 0.6     # hard core: share that always stands
const GLASSES := 0.12

const SKIN := [Color(0.98, 0.84, 0.72), Color(0.94, 0.76, 0.62), Color(0.85, 0.64, 0.48), Color(0.72, 0.52, 0.38),
	Color(0.58, 0.40, 0.28), Color(0.45, 0.30, 0.21), Color(0.33, 0.22, 0.16), Color(0.9, 0.7, 0.56)]
const HAIR := [Color(0.07, 0.06, 0.05), Color(0.12, 0.08, 0.05), Color(0.18, 0.11, 0.07), Color(0.28, 0.17, 0.09),
	Color(0.36, 0.23, 0.12), Color(0.55, 0.38, 0.2), Color(0.86, 0.72, 0.42), Color(0.75, 0.6, 0.35),
	Color(0.66, 0.3, 0.12), Color(0.45, 0.42, 0.4), Color(0.62, 0.62, 0.6), Color(0.78, 0.78, 0.76),
	Color(0.07, 0.06, 0.05), Color(0.18, 0.11, 0.07), Color(0.12, 0.08, 0.05), Color(0.28, 0.17, 0.09)]
const HAIR_WEIGHTS := [20, 16, 16, 10, 8, 5, 5, 3, 3, 0, 0, 0, 0, 0, 0, 0]     # 9-11 = grey, by age
const TROUSERS := [Color(0.18, 0.2, 0.26), Color(0.23, 0.29, 0.42), Color(0.29, 0.29, 0.29), Color(0.35, 0.27, 0.2),
	Color(0.12, 0.16, 0.27), Color(0.42, 0.42, 0.37), Color(0.08, 0.08, 0.09), Color(0.55, 0.5, 0.42)]
const COATS := [Color(0.1, 0.1, 0.12), Color(0.16, 0.2, 0.3), Color(0.3, 0.32, 0.25), Color(0.45, 0.12, 0.12),
	Color(0.55, 0.55, 0.57), Color(0.2, 0.3, 0.22), Color(0.6, 0.45, 0.25), Color(0.75, 0.75, 0.8)]
const CASUAL := [Color(0.95, 0.95, 0.95), Color(0.2, 0.25, 0.35), Color(0.12, 0.12, 0.14), Color(0.55, 0.15, 0.15),
	Color(0.85, 0.75, 0.3), Color(0.4, 0.55, 0.75), Color(0.6, 0.6, 0.62), Color(0.35, 0.45, 0.3), Color(0.8, 0.45, 0.25)]
const HAIR_WEIGHT := {"bald": 0.6, "receding": 0.8, "horseshoe": 0.6, "afro_small": 0.5, "curly_short": 0.7,
	"curly_mop": 0.6, "slick_back": 0.6, "man_bun": 0.6}
const LONG_HAIR := ["long", "long_straight", "bob", "ponytail", "medium", "man_bun", "curly_mop"]

enum Bit { COAT, LONG_SLEEVES, SCARF, CAP, BEANIE, GLASSES, SUNGLASSES, STUBBLE, BEARD, GOATEE, MOUSTACHE, FLAG,
	PATTERN0, PATTERN1, PATTERN2, NO_HAIR, CLUB_BEANIE }

static var _data := {}
static var _anim_tex: ImageTexture
static var _meshes := {}

var clip := {}               # name -> index
var supports_us := true
var _mat: ShaderMaterial
var _time := 0.0           # crowd clock (follows the game's delta, so movie capture / fast mode stay in sync)
var _fans: Array = []        # per fan: {mmi, i, sits, hard, mask, scarf, flag, base_loop}
var _settle_at := -1.0
var _settle_kind := ""


static func load_data() -> Dictionary:
	if _data.is_empty():
		var f := FileAccess.open(DATA_PATH, FileAccess.READ)
		_data = JSON.parse_string(f.get_as_text())
		var bones: int = _data["bones"].size()
		var mats: Array = _data["matrices"]
		var sits: Array = _data["sit"]
		var frames := sits.size()
		var w := bones * 3 + 1
		var buf := PackedFloat32Array()
		buf.resize(w * frames * 4)
		for fr in frames:
			for b in bones:
				for r in 3:
					var src := (fr * bones + b) * 12 + r * 4
					var dst := ((fr * w) + b * 3 + r) * 4
					for k in 4:
						buf[dst + k] = mats[src + k]
			buf[((fr * w) + bones * 3) * 4] = sits[fr]
		var img := Image.create_from_data(w, frames, false, Image.FORMAT_RGBAF, buf.to_byte_array())
		_anim_tex = ImageTexture.create_from_image(img)
	return _data


## seats: [{pos: Vector3, yaw: float, standing: bool (a standing place), hard: bool (hard-core section)}]
## opts: club_a, club_b (Color), ours (bool), temperature ("cold" / "mild" / "sunny"), flag_chance (float)
func setup(seats: Array, opts: Dictionary) -> void:
	var d := load_data()
	var club_a: Color = opts.get("club_a", Color(0.1, 0.55, 0.25))
	supports_us = opts.get("ours", true)
	var i := 0
	for c in d["clips"]:
		clip[c] = i
		i += 1
	_mat = ShaderMaterial.new()
	_mat.shader = SHADER
	_mat.set_shader_parameter("anim", _anim_tex)
	_mat.set_shader_parameter("bones", d["bones"].size())
	_mat.set_shader_parameter("fps", float(d["fps"]))
	_mat.set_shader_parameter("seat_height", float(d["seat_height"]))
	var rows := PackedInt32Array()
	var lens := PackedInt32Array()
	var desync := PackedInt32Array()
	for c in d["clips"]:
		rows.append(int(d["clips"][c]["row"]))
		lens.append(int(d["clips"][c]["frames"]))
		desync.append(1 if c in ["sit_idle", "stand_idle", "flag_wave", "scarf_up"] else 0)
	for k in range(rows.size(), 16):
		rows.append(0); lens.append(1); desync.append(0)
	_mat.set_shader_parameter("clip_row", rows)
	_mat.set_shader_parameter("clip_len", lens)
	_mat.set_shader_parameter("clip_desync", desync)
	_mat.set_shader_parameter("clip_scarf_up", clip["scarf_up"])
	_mat.set_shader_parameter("clip_scarf_twirl", clip["scarf_twirl"])
	_mat.set_shader_parameter("clip_flag", clip["flag_wave"])
	var club_b: Color = opts.get("club_b", Color(0.95, 0.95, 0.95))
	_mat.set_shader_parameter("club_a", club_a)
	_mat.set_shader_parameter("club_b", club_b)
	_mat.set_shader_parameter("skin_pal", _lin(SKIN))
	_mat.set_shader_parameter("hair_pal", _lin(HAIR))
	_mat.set_shader_parameter("trousers_pal", _lin(TROUSERS))
	_mat.set_shader_parameter("coat_pal", _lin(COATS))
	_mat.set_shader_parameter("shirt_pal", _lin([club_a] + CASUAL + [Color.WHITE].duplicate()))
	_mat.set_shader_parameter("crest", CREST)

	# roll every fan, group them per mesh variant
	var temp: String = opts.get("temperature", "mild")
	var flag_chance: float = opts.get("flag_chance", 0.03)
	var groups := {}
	for s in seats.size():
		var seat: Dictionary = seats[s]
		var rng := RandomNumberGenerator.new()
		rng.seed = hash(Vector3i(seat["pos"] * 10.0)) + s
		var fan := _roll(rng, seat, temp, flag_chance, club_a)
		var key: String = fan["body"] + "/" + fan["hair"]
		if not groups.has(key):
			groups[key] = []
		groups[key].append(fan)
	for key in groups:
		var list: Array = groups[key]
		var parts: PackedStringArray = key.split("/")
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_custom_data = true
		mm.mesh = _variant_mesh(parts[0], parts[1])
		mm.instance_count = list.size()
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = mm
		mmi.material_override = _mat
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mmi)
		for j in list.size():
			var fan: Dictionary = list[j]
			mm.set_instance_transform(j, Transform3D(Basis(Vector3.UP, fan["yaw"]).scaled(Vector3.ONE * fan["scale"]), fan["pos"]))
			fan["mm"] = mm
			fan["i"] = j
			_fans.append(fan)
			_apply(fan, -1, fan["base"], -100.0)
	_mat.set_shader_parameter("now", 0.0)


func _roll(rng: RandomNumberGenerator, seat: Dictionary, temp: String, flag_chance: float, club_a: Color) -> Dictionary:
	var d := _data
	var r := rng.randf()
	var body := "woman" if r < WOMEN else ("child" if r < WOMEN + CHILDREN else "man")
	var hard: bool = seat.get("hard", false)
	var age := rng.randi_range(8, 14) if body == "child" else rng.randi_range(18, 75)
	# hairstyle (normal ones far likelier, thinning with age)
	var styles: Array = (d["hair_sets"][body] as Array).duplicate()
	if body == "man":
		styles.append("bald")
	var weights := []
	for st in styles:
		var w: float = HAIR_WEIGHT.get(st, 1.0)
		if st in ["bald", "receding", "horseshoe"]:
			w = 0.1 + maxf(0.0, age - 30) * 0.06
		weights.append(w)
	var hair: String = _pick(rng, styles, weights)
	var mask := 0
	# clothes
	var club := rng.randf() < (0.8 if hard else 0.4)
	var shirt := 0 if club else 1 + rng.randi() % CASUAL.size()
	if club and rng.randf() < 0.3:
		mask |= 1 << Bit.LONG_SLEEVES                     # club sweater
	var coat_p: float = {"cold": 0.75, "mild": 0.18, "sunny": 0.0}.get(temp, 0.18)
	if rng.randf() < coat_p:
		mask |= 1 << Bit.COAT
	var scarf_p: float = {"cold": 0.35, "mild": 0.15, "sunny": 0.05}.get(temp, 0.15)
	if hard:
		scarf_p = {"cold": 0.8, "mild": 0.5, "sunny": 0.2}.get(temp, 0.5)
	var scarf: bool = rng.randf() < scarf_p
	if scarf:
		mask |= 1 << Bit.SCARF
	var head_r := rng.randf()
	if temp == "cold" and head_r < 0.35:
		mask |= 1 << Bit.BEANIE
		if hard or rng.randf() < 0.3:
			mask |= 1 << Bit.CLUB_BEANIE
	elif head_r < ({"sunny": 0.25, "mild": 0.06}.get(temp, 0.0) as float):
		mask |= 1 << Bit.CAP
	if mask & ((1 << Bit.BEANIE) | (1 << Bit.CAP)) and not hair in LONG_HAIR:
		mask |= 1 << Bit.NO_HAIR
	if temp == "sunny" and rng.randf() < 0.25:
		mask |= 1 << Bit.SUNGLASSES
	elif rng.randf() < GLASSES:
		mask |= 1 << Bit.GLASSES
	if body == "man":
		var b := rng.randf()
		if b < 0.25: mask |= 1 << Bit.STUBBLE
		elif b < 0.40: mask |= 1 << Bit.BEARD
		elif b < 0.47: mask |= 1 << Bit.GOATEE
		elif b < 0.52: mask |= 1 << Bit.MOUSTACHE
	var standing: bool = seat.get("standing", false) or (hard and rng.randf() < HC_STANDING)
	var flag := hard and body != "child" and rng.randf() < flag_chance
	if flag:
		mask |= 1 << Bit.FLAG
		mask |= rng.randi_range(0, 7) << Bit.PATTERN0
		standing = true
	# colours
	var skin := rng.randi() % SKIN.size()
	var hc := _pick_i(rng, HAIR_WEIGHTS)
	if age > 45 and rng.randf() < (age - 45) / 25.0:
		hc = 9 + rng.randi() % 3
	var pal := skin | (hc << 3) | ((rng.randi() % TROUSERS.size()) << 7) | ((rng.randi() % COATS.size()) << 10) | ((rng.randi() % COATS.size()) << 13) | (shirt << 16)
	var base := "stand_idle" if standing else "sit_idle"
	if flag:
		base = "flag_wave"
	elif standing and hard:
		var q := rng.randf()
		base = "clap_stand" if q < 0.15 else ("scarf_up" if scarf and q < 0.3 else "stand_idle")
	var scale := rng.randf_range(0.66, 0.76) if body == "child" else (rng.randf_range(0.9, 0.99) if body == "woman" else rng.randf_range(0.94, 1.05))
	return {"body": body, "hair": hair, "pos": seat["pos"], "yaw": seat["yaw"], "scale": scale, "mask": mask,
		"pal": pal, "sits": not standing, "hard": hard, "scarf": scarf, "flag": flag,
		"base": clip[base], "rng": rng.randf()}


func _apply(fan: Dictionary, intro: int, loop: int, start: float) -> void:
	(fan["mm"] as MultiMesh).set_instance_custom_data(fan["i"], Color(float(intro + 1 + 32 * loop), start, float(fan["mask"]), float(fan["pal"])))
	fan["loop"] = loop
	fan["standing_now"] = not (loop in [clip["sit_idle"], clip["sit_clap"], clip["despair_sit"]])


func _now() -> float:
	return _time


func _process(delta: float) -> void:
	if _mat == null:
		return
	_time += delta
	var t := _now()
	_mat.set_shader_parameter("now", t)
	if _settle_at > 0.0 and t >= _settle_at:
		_settle_at = -1.0
		_settle()


## kind: goal_for / goal_against / chance / save / tackle (from our point of view; flipped for away fans)
func react(kind: String) -> void:
	if not supports_us:
		kind = {"goal_for": "goal_against", "goal_against": "goal_for", "save": "chance", "chance": "save"}.get(kind, kind)
	var t := _now()
	match kind:
		"goal_for":
			for fan in _fans:
				var r: float = randf()
				var cheer := "cheer_jump" if r < 0.35 else ("cheer_arms" if r < 0.6 else ("fist_pump" if r < 0.75 else "clap_stand"))
				if fan["scarf"] and randf() < 0.45:
					cheer = "scarf_up" if randf() < 0.5 else "scarf_twirl"
				if fan["flag"]:
					cheer = "flag_wave"
				_cheer(fan, clip[cheer], t + randf_range(0.0, 0.6))
			_settle_at = t + 9.0
		"chance", "save":
			for fan in _fans:
				if fan["flag"]:
					continue
				if fan["standing_now"]:
					if randf() < 0.5:
						_apply(fan, -1, clip["clap_stand" if randf() < 0.6 else "cheer_arms"], t + randf_range(0.0, 0.4))
				elif randf() < 0.35:
					_cheer(fan, clip["clap_stand" if randf() < 0.5 else ("fist_pump" if randf() < 0.5 else "cheer_arms")], t + randf_range(0.0, 0.5))
				elif randf() < 0.5:
					_apply(fan, -1, clip["sit_clap"], t + randf_range(0.0, 0.4))
			_settle_at = t + 3.5
		"goal_against":
			for fan in _fans:
				if fan["flag"]:
					continue
				_apply(fan, -1, clip["despair_stand"] if fan["standing_now"] else clip["despair_sit"], t + randf_range(0.0, 0.8))
			_settle_at = t + 4.5


func _cheer(fan: Dictionary, loop: int, start: float) -> void:
	_apply(fan, clip["stand_up"] if not fan["standing_now"] else -1, loop, start)


## Back to everyone's normal state: the sitters sit down again.
func _settle() -> void:
	var t := _now()
	for fan in _fans:
		var start := t + randf_range(0.0, 1.5)
		if fan["sits"]:
			if fan["standing_now"]:
				_apply(fan, clip["sit_down"], clip["sit_idle"], start)
			else:
				_apply(fan, -1, clip["sit_idle"], start)
		else:
			_apply(fan, -1, fan["base"], start)


# ------------------------------------------------------------------ meshes

func _variant_mesh(body: String, hair: String) -> ArrayMesh:
	var key := body + "/" + hair
	if _meshes.has(key):
		return _meshes[key]
	var d := _data
	var srcs := [d["bodies"][body]]
	if d["hairs"].has(hair):
		srcs.append(d["hairs"][hair])
	var head_bone: int = (d["bones"] as Array).find("head")
	var hc := Vector3(d["head_center"][0], d["head_center"][1], d["head_center"][2])
	var head_scale := 1.22 if body == "child" else 1.0
	var verts := PackedVector3Array()
	var normals := PackedVector3Array()
	var custom := PackedFloat32Array()
	for src in srcs:
		var pos: Array = src["pos"]
		var nrm: Array = src["nrm"]
		var part: Array = src["part"]
		var uv: Array = src["uv"]
		var bone: Array = src["bone"]
		for k in part.size():
			var v := Vector3(pos[k * 3], pos[k * 3 + 1], pos[k * 3 + 2])
			if bone[k] == head_bone and head_scale != 1.0:
				v = hc + (v - hc) * head_scale
			verts.append(v)
			normals.append(Vector3(nrm[k * 3], nrm[k * 3 + 1], nrm[k * 3 + 2]))
			custom.append(float(bone[k])); custom.append(float(part[k]))
			custom.append(float(uv[k * 2])); custom.append(float(uv[k * 2 + 1]))
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_CUSTOM0] = custom
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays, [], {},
		Mesh.ARRAY_CUSTOM_RGBA_FLOAT << Mesh.ARRAY_FORMAT_CUSTOM0_SHIFT)
	mesh.custom_aabb = AABB(Vector3(-2.0, -0.5, -2.0), Vector3(4.0, 4.0, 4.0))   # animations + flags reach outside the rest pose
	_meshes[key] = mesh
	return mesh


static func _lin(cols: Array) -> PackedVector3Array:
	var out := PackedVector3Array()
	for c in cols:
		var l: Color = (c as Color).srgb_to_linear()
		out.append(Vector3(l.r, l.g, l.b))
	return out


static func _pick(rng: RandomNumberGenerator, items: Array, weights: Array) -> String:
	var total := 0.0
	for w in weights:
		total += w
	var r := rng.randf() * total
	for i in items.size():
		r -= weights[i]
		if r <= 0.0:
			return items[i]
	return items[items.size() - 1]


static func _pick_i(rng: RandomNumberGenerator, weights: Array) -> int:
	var total := 0.0
	for w in weights:
		total += w
	var r := rng.randf() * total
	for i in weights.size():
		r -= weights[i]
		if r <= 0.0:
			return i
	return 0
