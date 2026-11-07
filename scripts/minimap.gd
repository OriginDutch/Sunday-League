class_name Minimap
extends Control
const Kit = preload("res://scripts/ui_kit.gd")
## Radar of the whole pitch (bottom-right) + arrows at the screen edge for teammates out of view.

const MAP_W := 260.0
const MARGIN := 8.0

var main: Main
var arrows: Control


func setup(m: Main) -> void:
	main = m
	set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	var map_h := MAP_W * (Main.HALF_W / Main.HALF_L)
	offset_left = -MAP_W - 16.0
	offset_right = -16.0
	offset_top = -map_h - 50.0
	offset_bottom = -50.0
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	# separate full-screen layer for the edge arrows
	arrows = Control.new()
	arrows.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	arrows.mouse_filter = Control.MOUSE_FILTER_IGNORE
	arrows.draw.connect(_draw_arrows)


func _process(_delta: float) -> void:
	queue_redraw()
	arrows.queue_redraw()


func _to_map(p: Vector3) -> Vector2:
	var w := size.x
	var h := size.y
	return Vector2((p.x / Main.HALF_L * 0.5 + 0.5) * w, (p.z / Main.HALF_W * 0.5 + 0.5) * h)


func _draw() -> void:
	if main == null or main.mode != "match":
		return
	var r := Rect2(Vector2.ZERO, size)
	# noticeboard index card (GDD §10e)
	draw_style_box(Kit.box(Kit.c("card"), 3), r.grow(MARGIN + 4.0))
	var pen := Kit.c("pen")
	var line := Color(pen.r, pen.g, pen.b, 0.5)
	draw_rect(r, pen, false, 2.0)
	draw_line(Vector2(size.x * 0.5, 0), Vector2(size.x * 0.5, size.y), line, 1.0)
	draw_arc(size * 0.5, 9.15 / Main.HALF_L * 0.5 * size.x, 0, TAU, 24, line, 1.0)
	for s in [-1.0, 1.0]:
		var sx: float = s
		var a := _to_map(Vector3(sx * Main.HALF_L, 0, -Main.BOX_HALF_W))
		var b := _to_map(Vector3(sx * (Main.HALF_L - Main.BOX_DEPTH), 0, Main.BOX_HALF_W))
		draw_rect(Rect2(Vector2(minf(a.x, b.x), a.y), Vector2(absf(b.x - a.x), b.y - a.y)), line, false, 1.0)
	for p in main.players:
		var c := Kit.c("primary") if p.team == 0 else Kit.c("ink")
		var mp := _to_map(p.position)
		draw_circle(mp, 4.0, c)
		if p == main.controlled:
			draw_arc(mp, 7.0, 0, TAU, 16, Kit.c("pen"), 2.0)
	var bp := _to_map(main.ball.position)
	draw_circle(bp, 4.0, Kit.c("ink"))
	draw_circle(bp, 2.6, Color.WHITE)


func _draw_arrows() -> void:
	if main == null or main.mode != "match" or main.autoplay:
		return
	var cam := main.camera
	var vp := arrows.size
	var pad := 52.0
	var center := vp * 0.5
	for p in main.home:
		if p.role == "GK" or p == main.controlled:
			continue
		var wp := p.position + Vector3(0, 1.0, 0)
		var behind := cam.is_position_behind(wp)
		var sp := cam.unproject_position(wp)
		var on_screen := not behind and sp.x > 0 and sp.y > 0 and sp.x < vp.x and sp.y < vp.y
		if on_screen:
			continue
		var dir := (sp - center)
		if behind:
			dir = -dir
		if dir.length() < 0.01:
			continue
		dir = dir.normalized()
		# push to the screen edge
		var tx := (vp.x * 0.5 - pad) / maxf(absf(dir.x), 0.0001)
		var ty := (vp.y * 0.5 - pad) / maxf(absf(dir.y), 0.0001)
		var pos := center + dir * minf(tx, ty)
		var perp := Vector2(-dir.y, dir.x)
		var pts := PackedVector2Array([pos + dir * 12.0, pos - dir * 8.0 + perp * 8.0, pos - dir * 8.0 - perp * 8.0])
		arrows.draw_colored_polygon(pts, Color(Main.HOME_SHIRT, 0.9))
		arrows.draw_polyline(PackedVector2Array([pts[0], pts[1], pts[2], pts[0]]), Color(1, 1, 1, 0.9), 1.5)
