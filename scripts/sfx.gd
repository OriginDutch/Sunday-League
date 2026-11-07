class_name Sfx
extends Node
## Procedurally generated sounds (no audio files): kick, whistle, (crowd sounds removed, see GDD §10h).

const RATE := 22050

var _kick: AudioStreamWAV
var _whistle: AudioStreamWAV
var _whistle_long: AudioStreamWAV
var _pool: Array[AudioStreamPlayer] = []
var crowd_level := 0.1     # 0..1, scales crowd sounds with attendance


func _ready() -> void:
	_kick = _make_kick()
	_whistle = _make_whistle(0.32)
	_whistle_long = _make_whistle(0.9)
	for i in 8:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_pool.append(p)


func _play(stream: AudioStream, volume_db: float, pitch: float = 1.0) -> void:
	for p in _pool:
		if not p.playing:
			p.stream = stream
			p.volume_db = volume_db
			p.pitch_scale = pitch
			p.play()
			return


func kick(speed: float) -> void:
	_play(_kick, linear_to_db(clampf(speed / 25.0, 0.15, 1.0)) - 2.0, randf_range(0.9, 1.1))


func whistle(long: bool = false) -> void:
	_play(_whistle_long if long else _whistle, -6.0)


func whistle_times(n: int) -> void:
	for i in n:
		get_tree().create_timer(i * 0.55).timeout.connect(func() -> void: whistle(i == n - 1))


func crowd(_kind: String) -> void:
	# procedural crowd sounds removed (GDD §10h); real recordings go here later
	pass


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
