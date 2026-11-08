extends RefCounted
## Player settings (GDD §10e settings screen): sound, match length, camera speed, light/dark.
## Saved to user://settings.json, separate from the club save. Loaded by path (no class_name).

const PATH := "user://settings.json"

static var music := 70          # 0–100 (no music yet; the bus exists for later)
static var effects := 80        # kicks, whistle
static var crowd := 100         # cheers
static var half_minutes := 3    # 1–10 minutes per half
static var camera_speed := 50   # 0–100 → 0.5× … 1.5× hub/build camera
static var dark := false        # light is the default (GDD); dark mode is an option


static func load_all() -> void:
	if FileAccess.file_exists(PATH):
		var f := FileAccess.open(PATH, FileAccess.READ)
		var d = JSON.parse_string(f.get_as_text())
		if d is Dictionary:
			music = int(d.get("music", music))
			effects = int(d.get("effects", effects))
			crowd = int(d.get("crowd", crowd))
			half_minutes = clampi(int(d.get("half_minutes", half_minutes)), 1, 10)
			camera_speed = int(d.get("camera_speed", camera_speed))
			dark = bool(d.get("dark", dark))
	_ensure_buses()
	apply_audio()


static func save() -> void:
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	if f == null:
		return
	f.store_string(JSON.stringify({"music": music, "effects": effects, "crowd": crowd,
		"half_minutes": half_minutes, "camera_speed": camera_speed, "dark": dark}))


static func _ensure_buses() -> void:
	for n in ["Music", "Effects", "Crowd"]:
		if AudioServer.get_bus_index(n) == -1:
			var i := AudioServer.bus_count
			AudioServer.add_bus(i)
			AudioServer.set_bus_name(i, n)
			AudioServer.set_bus_send(i, "Master")


static func apply_audio() -> void:
	for pair in [["Music", music], ["Effects", effects], ["Crowd", crowd]]:
		var i := AudioServer.get_bus_index(pair[0])
		if i == -1:
			continue
		var v: int = pair[1]
		AudioServer.set_bus_mute(i, v <= 0)
		AudioServer.set_bus_volume_db(i, linear_to_db(maxf(v, 1) / 100.0))


static func half_seconds() -> float:
	return half_minutes * 60.0


static func camera_mult() -> float:
	return lerpf(0.5, 1.5, camera_speed / 100.0)
