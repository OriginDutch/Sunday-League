class_name Sfx
extends Node
## Sounds: recorded kicks + goal cheers (assets/audio, GDD §10h), procedural whistle.

const RATE := 22050

var _kick: AudioStreamWAV
var _whistle: AudioStreamWAV
var _whistle_long: AudioStreamWAV
var _pool: Array[AudioStreamPlayer] = []
var crowd_level := 0.1     # 0..1, scales crowd sounds with attendance
var _kicks: Array[AudioStream] = []
var _kicks_big: Array[AudioStream] = []
var _cheers: Array[AudioStream] = []
var _cheer_player: AudioStreamPlayer
var _cheer_tween: Tween

const BIG_KICK_SPEED := 20.0    # m/s; harder kicks use the heavier "goalie kick" sounds (tunable)
const CHEER_HOLD := 8.0         # seconds at full volume before the goal cheer fades (tunable)
const CHEER_FADE := 4.0


func _ready() -> void:
	_kick = _make_kick()
	# licensed recordings are not in git (GDD §10h); missing files are skipped
	_kicks = _load_all("res://assets/audio/kicks/kick_%d.ogg", 7)
	_kicks_big = _load_all("res://assets/audio/kicks/kick_big_%d.ogg", 4)
	_cheers = _load_all("res://assets/audio/crowd/cheer_%d.ogg", 6)
	if _kicks.is_empty():
		_kicks.append(_kick)
	if _kicks_big.is_empty():
		_kicks_big = _kicks
	_cheer_player = AudioStreamPlayer.new()
	add_child(_cheer_player)
	_whistle = _make_whistle(0.32)
	_whistle_long = _make_whistle(0.9)
	for i in 8:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_pool.append(p)


func _load_all(pattern: String, count: int) -> Array[AudioStream]:
	var out: Array[AudioStream] = []
	for i in range(1, count + 1):
		var path := pattern % i
		if ResourceLoader.exists(path):
			out.append(load(path))
	return out


func _play(stream: AudioStream, volume_db: float, pitch: float = 1.0) -> void:
	for p in _pool:
		if not p.playing:
			p.stream = stream
			p.volume_db = volume_db
			p.pitch_scale = pitch
			p.play()
			return


func kick(speed: float) -> void:
	var set := _kicks_big if speed >= BIG_KICK_SPEED else _kicks
	_play(set.pick_random(), linear_to_db(clampf(speed / 25.0, 0.2, 1.0)) - 3.0, randf_range(0.95, 1.05))


func whistle(long: bool = false) -> void:
	_play(_whistle_long if long else _whistle, -6.0)


func whistle_times(n: int) -> void:
	for i in n:
		get_tree().create_timer(i * 0.55).timeout.connect(func() -> void: whistle(i == n - 1))


func crowd(kind: String) -> void:
	# only home goals have a recording so far; other reactions stay silent (GDD §10h)
	if kind != "goal_for" or _cheers.is_empty():
		return
	if _cheer_tween:
		_cheer_tween.kill()
	_cheer_player.stream = _cheers.pick_random()
	var vol := linear_to_db(clampf(crowd_level, 0.05, 1.0)) - 2.0
	_cheer_player.volume_db = vol
	_cheer_player.play()
	_cheer_tween = create_tween()
	_cheer_tween.tween_interval(CHEER_HOLD)
	_cheer_tween.tween_property(_cheer_player, "volume_db", -60.0, CHEER_FADE)
	_cheer_tween.tween_callback(_cheer_player.stop)


func set_murmur(_on: bool) -> void:
	# crowd murmur removed (sounded like wind, GDD §10h); comes back with real recordings
	pass


# ------------------------------------------------------------------ synthesis

func _to_wav(samples: PackedFloat32Array, loop: bool = false, loop_end: int = -1) -> AudioStreamWAV:
	var bytes := PackedByteArray()
	bytes.resize(samples.size() * 2)
	for i in samples.size():
		bytes.encode_s16(i * 2, int(clampf(samples[i], -1.0, 1.0) * 32000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = RATE
	w.stereo = false
	w.data = bytes
	if loop:
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_begin = 0
		w.loop_end = loop_end if loop_end > 0 else samples.size()
	return w


func _make_kick() -> AudioStreamWAV:
	var n := int(RATE * 0.14)
	var out := PackedFloat32Array()
	out.resize(n)
	var phase := 0.0
	for i in n:
		var t := float(i) / RATE
		var f := lerpf(110.0, 45.0, t / 0.14)
		phase += TAU * f / RATE
		var body := sin(phase) * exp(-t * 28.0)
		var click := randf_range(-1.0, 1.0) * exp(-t * 180.0) * 0.5
		out[i] = (body + click) * 0.9
	return _to_wav(out)


func _make_whistle(length: float) -> AudioStreamWAV:
	var n := int(RATE * length)
	var out := PackedFloat32Array()
	out.resize(n)
	var phase := 0.0
	for i in n:
		var t := float(i) / RATE
		var trill := 1.0 + 0.04 * sin(TAU * 32.0 * t)   # the pea rattling
		phase += TAU * 2900.0 * trill / RATE
		var env := minf(t / 0.02, 1.0) * minf((length - t) / 0.05, 1.0)
		out[i] = (sin(phase) * 0.6 + randf_range(-1.0, 1.0) * 0.08) * env * 0.5
	return _to_wav(out)
