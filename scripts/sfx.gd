class_name Sfx
extends Node
## Procedurally generated sounds (no audio files): kick, whistle, crowd cheer/groan/ooh, crowd murmur.

const RATE := 22050

var _kick: AudioStreamWAV
var _whistle: AudioStreamWAV
var _whistle_long: AudioStreamWAV
var _cheer: AudioStreamWAV
var _groan: AudioStreamWAV
var _ooh: AudioStreamWAV
var _murmur: AudioStreamWAV
var _pool: Array[AudioStreamPlayer] = []
var _murmur_player: AudioStreamPlayer
var crowd_level := 0.1     # 0..1, scales crowd sounds with attendance


func _ready() -> void:
	_kick = _make_kick()
	_whistle = _make_whistle(0.32)
	_whistle_long = _make_whistle(0.9)
	_cheer = _make_crowd(2.6, 0.35, 1.0, 0.25)
	_groan = _make_crowd(1.6, 0.12, 0.6, 0.9)
	_ooh = _make_crowd(0.9, 0.2, 0.7, 0.5)
	_murmur = _make_crowd(4.0, 0.08, 0.5, 0.5, true)
	for i in 8:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_pool.append(p)
	_murmur_player = AudioStreamPlayer.new()
	_murmur_player.stream = _murmur
	add_child(_murmur_player)


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


func crowd(kind: String) -> void:
	var vol := linear_to_db(clampf(crowd_level, 0.05, 1.0))
	match kind:
		"goal_for":
			_play(_cheer, vol, randf_range(0.95, 1.05))
		"goal_against":
			_play(_groan, vol - 3.0)
		"save", "chance":
			_play(_ooh, vol - 4.0, randf_range(0.9, 1.1))
		"tackle":
			_play(_cheer, vol - 12.0, 1.3)


func set_murmur(on: bool) -> void:
	if on:
		_murmur_player.volume_db = linear_to_db(clampf(crowd_level, 0.03, 1.0)) - 14.0
		if not _murmur_player.playing:
			_murmur_player.play()
	else:
		_murmur_player.stop()


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


## Crowd noise: filtered noise with a swell envelope. `bright` sets the filter (0..1),
## `fall` how much of the length is decay.
func _make_crowd(length: float, attack: float, bright: float, fall: float, loop: bool = false) -> AudioStreamWAV:
	var n := int(RATE * length)
	var out := PackedFloat32Array()
	out.resize(n)
	var lp := 0.0
	var lp2 := 0.0
	var a := lerpf(0.03, 0.25, bright)
	for i in n:
		var t := float(i) / RATE
		lp += (randf_range(-1.0, 1.0) - lp) * a
		lp2 += (lp - lp2) * a
		var env := 1.0
		if not loop:
			env = minf(t / maxf(attack, 0.01), 1.0)
			var decay_start := length * (1.0 - fall)
			if t > decay_start:
				env *= maxf(0.0, 1.0 - (t - decay_start) / (length - decay_start))
		# slow wobble so it sounds like many voices
		env *= 0.8 + 0.2 * sin(TAU * 2.3 * t + sin(TAU * 0.7 * t) * 2.0)
		out[i] = lp2 * env * 2.2
	if loop:
		# crossfade the ends so the loop doesn't click
		var fade := int(RATE * 0.2)
		for i in fade:
			var k := float(i) / fade
			out[i] = out[i] * k + out[n - fade + i] * (1.0 - k)
		return _to_wav(out, true, n - fade)   # loop jumps from n-fade back to 0, which now matches
	return _to_wav(out, loop)
