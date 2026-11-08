extends RefCounted
## How a footballer looks: height, build, skin, hair, beard. Rolled once from a seed (the player's name),
## so the same player always looks the same; the beard and grey hair follow his age.
## Loaded by path (no class_name): `const PlayerLook := preload("res://scripts/player_look.gd")`.

const HEIGHT_MEAN := 1.81
const HEIGHT_SD := 0.07
const HEIGHT_MIN := 1.50       # Marcel: 1.50–2.15 m covers every real pro
const HEIGHT_MAX := 2.15
const MODEL_HEIGHT := 1.863    # top of the head of player.glb at scale 1

const SKIN := [Color(0.98, 0.84, 0.72), Color(0.94, 0.76, 0.62), Color(0.85, 0.64, 0.48), Color(0.72, 0.52, 0.38),
	Color(0.58, 0.40, 0.28), Color(0.45, 0.30, 0.21), Color(0.33, 0.22, 0.16)]
const HAIR := [[Color(0.07, 0.06, 0.05), 35.0], [Color(0.18, 0.11, 0.07), 30.0], [Color(0.36, 0.23, 0.12), 15.0],
	[Color(0.55, 0.38, 0.2), 6.0], [Color(0.86, 0.72, 0.42), 9.0], [Color(0.66, 0.3, 0.12), 5.0]]
const GREY := Color(0.74, 0.74, 0.72)
const THINNING := ["receding", "horseshoe", "thin_crown", "bald"]
const LONG := ["medium", "medium_part", "bob", "long", "long_straight", "dreads_long", "ponytail", "man_bun", "curly_mop", "mullet"]
const TEEN_BEARDS := ["moustache", "goatee"]


## role "GK"/"OUT", slot = index in the team list (0 keeper, 2-3 centre-backs in the 4-3-3).
static func make(seed_text: String, role: String, slot: int, age: int, hair_styles: Array, beard_styles: Array) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(seed_text)
	if age <= 0:
		age = 17 + int(round((rng.randf() + rng.randf()) * 0.5 * 19.0))   # 17–36, most around 26
	var h := rng.randfn(HEIGHT_MEAN, HEIGHT_SD)
	if role == "GK":
		h += 0.06
	elif slot == 2 or slot == 3:
		h += 0.03
	h = clampf(h, HEIGHT_MIN, HEIGHT_MAX)
	var look := {
		"age": age,
		"height": h,
		"shoulders": clampf(rng.randfn(1.0, 0.05) + (h - HEIGHT_MEAN) * 0.5, 0.86, 1.18),
		"muscle": clampf(rng.randfn(1.0, 0.07), 0.84, 1.24),
		"belly": clampf(rng.randfn(0.98, 0.05) + maxf(0.0, age - 29) * 0.008, 0.88, 1.28),
	}
	var t := rng.randf() * (SKIN.size() - 1)
	look["skin"] = (SKIN[int(t)] as Color).lerp(SKIN[mini(int(t) + 1, SKIN.size() - 1)], t - int(t))
	look["hair_color"] = _weighted_color(rng)
	look["greys"] = rng.randf() < 0.55
	look["grey_jitter"] = rng.randf_range(-0.15, 0.15)
	# hairstyle: thinning gets likelier with age, long hair a bit rarer
	var weights := []
	for s in hair_styles:
		var w := 1.0
		if s in THINNING:
			w = 0.15 + maxf(0.0, age - 26) * 0.25
		elif s in LONG:
			w = 0.6
		weights.append(w)
	look["hair"] = _pick(rng, hair_styles, weights)
	look["beard_style"] = beard_styles[rng.randi() % beard_styles.size()] if not beard_styles.is_empty() else ""
	look["teen_beard"] = TEEN_BEARDS[rng.randi() % TEEN_BEARDS.size()]
	look["clean_shaven"] = rng.randf() < 0.3
	look["beard_roll"] = rng.randf()
	return look


## Beard for this age: "" (none) or [style, stage]. A 17-year-old has fluff at most, a 33-year-old a full beard.
static func beard(look: Dictionary) -> Array:
	var age: int = look["age"]
	var roll: float = look["beard_roll"]
	if age < 19:
		return [look["teen_beard"], "stubble"] if roll < 0.25 else []
	if look["clean_shaven"]:
		return []
	var growth := clampf((age - 18) / 13.0, 0.0, 1.0) + (roll - 0.5) * 0.5
	var stage := "stubble" if growth < 0.35 else ("short" if growth < 0.7 else "full")
	return [look["beard_style"], stage]


static func hair_color(look: Dictionary) -> Color:
	var c: Color = look["hair_color"]
	if look["greys"] and look["age"] >= 31:
		c = c.lerp(GREY, clampf((look["age"] - 31) / 12.0 + look["grey_jitter"], 0.0, 0.85))
	return c


static func _weighted_color(rng: RandomNumberGenerator) -> Color:
	var total := 0.0
	for e in HAIR:
		total += e[1]
	var r := rng.randf() * total
	for e in HAIR:
		r -= e[1]
		if r <= 0.0:
			return e[0]
	return HAIR[0][0]


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
