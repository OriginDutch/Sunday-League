extends RefCounted
## Clubhouse Noticeboard UI kit (GDD §10e; tokens: design/ui-noticeboard/sunday_league_ui_tokens_v2.json).
## Paper, sticky note, index card, tape, pins, buttons, stat tags, nav items. Sizes are design pixels
## at 1920×1080 — the hub scales its board to the window. Loaded by path (no class_name on purpose).

const DESIGN := Vector2(1920, 1080)
const ICON_DIR := "res://assets/ui/icons/"

static var dark := false                              # light is the default (GDD); dark is an option
static var club_primary := Color(0.12, 0.62, 0.28)    # = Main.HOME_SHIRT until club colours are a thing
static var club_secondary := Color(1, 1, 1)
static var _fonts := {}
static var _icons := {}

const LIGHT := {
	"ink": "#24313A", "muted": "#5E6A72", "paper": "#F3EFE6", "card": "#FBF8F1", "tag": "#FFFFFF",
	"tag_border": "#D9D3C3", "btn_border": "#C9C2B0", "ok": "#1F7A3E", "danger": "#B8322A", "div": "#D9D3C3",
}
const DARK := {
	"ink": "#F1ECDF", "muted": "#B4B8B4", "paper": "#25292D", "card": "#2C3135", "tag": "#33383D",
	"tag_border": "#4A5056", "btn_border": "#5A6168", "ok": "#7FD39A", "danger": "#FF8A7A", "div": "#4A5056",
}
const FIXED := {"note": "#FFE58A", "note_ink": "#24313A", "note_muted": "#4A4A3A", "bar_track": "#FFF6C9"}


# ------------------------------------------------------------------ colours

static func c(key: String) -> Color:
	if FIXED.has(key):
		return Color(FIXED[key])
	match key:
		"primary":
			return club_primary
		"pen":
			return _pen()
		"highlight":
			return _highlight()
		"highlight_text":
			return _on(_highlight())
		"button_text":
			return _on(club_primary)
		"button_shadow":
			return club_primary.darkened(0.32)
		"tape":
			var h := _highlight()
			return Color(h.r, h.g, h.b, 0.78)
		"pin":
			return club_primary
		"lines":
			var p := _pen() if not dark else Color(1, 1, 1)
			return Color(p.r, p.g, p.b, 0.10 if not dark else 0.06)
	return Color((DARK if dark else LIGHT)[key])


static func _lum(col: Color) -> float:
	var f := func(v: float) -> float: return v / 12.92 if v <= 0.03928 else pow((v + 0.055) / 1.055, 2.4)
	return 0.2126 * f.call(col.r) + 0.7152 * f.call(col.g) + 0.0722 * f.call(col.b)


static func contrast(a: Color, b: Color) -> float:
	var la := _lum(a)
	var lb := _lum(b)
	return (maxf(la, lb) + 0.05) / (minf(la, lb) + 0.05)


## Text accents: primary darkened (light) or lightened (dark) until 4.5:1 on the card colour.
static func _pen() -> Color:
	var bg := Color(DARK["card"]) if dark else Color(LIGHT["card"])
	var p := club_primary
	for i in 20:
		if contrast(p, bg) >= 4.5:
			break
		p = p.lightened(0.08) if dark else p.darkened(0.08)
	return p


## Tape, selected tab, card stripe: the secondary colour if it shows on paper, else the primary.
static func _highlight() -> Color:
	return club_secondary if contrast(club_secondary, Color(LIGHT["paper"])) >= 1.5 else club_primary


static func _on(bg: Color) -> Color:
	var ink := Color(LIGHT["ink"])
	return Color(1, 1, 1) if contrast(Color(1, 1, 1), bg) >= contrast(ink, bg) else ink


# ------------------------------------------------------------------ fonts & text

## hand = Kalam (headings, club name, notes, ticker, flavour); otherwise Work Sans (everything functional).
static func font(hand: bool, weight: int = 500) -> Font:
	var key := "%s%d" % ["h" if hand else "s", weight]
	if _fonts.has(key):
		return _fonts[key]
	var f: Font
	if hand:
		f = load("res://assets/fonts/Kalam-Bold.ttf" if weight >= 700 else "res://assets/fonts/Kalam-Regular.ttf")
	else:
		var v := FontVariation.new()
		v.base_font = load("res://assets/fonts/WorkSans-Variable.ttf")
		v.variation_opentype = {"wght": weight}
		f = v
	_fonts[key] = f
	return f


static func label(text: String, hand: bool, size: int, weight: int, col: Color, wrap := false) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", font(hand, weight))
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", col)
	if wrap:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


static func heading(text: String, size := 38, col = null) -> Label:
	return label(text, true, size, 700, c("ink") if col == null else col)


static func caps(text: String, col = null) -> Label:
	return label(text.to_upper(), false, 14, 700, c("pen") if col == null else col)


# ------------------------------------------------------------------ icons

static func icon_tex(name: String) -> Texture2D:
	if not _icons.has(name):
		_icons[name] = load(ICON_DIR + name + ".svg")
	return _icons[name]


static func icon(name: String, size: int, col: Color) -> TextureRect:
	var t := TextureRect.new()
	t.texture = icon_tex(name)
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	t.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	t.custom_minimum_size = Vector2(size, size)
	t.modulate = col
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return t


# ------------------------------------------------------------------ surfaces

static func box(bg: Color, radius: int, shadow := true) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.set_corner_radius_all(radius)
	if shadow:
		s.shadow_color = Color(0, 0, 0, 0.45 if dark else 0.28)
		s.shadow_size = 16 if not dark else 18
		s.shadow_offset = Vector2(0, 8)
	s.anti_aliasing = true
	return s


## A sheet: an outer free Control (rotates around its centre, carries tape/pins) with a PanelContainer
## inside that sizes itself to its content. Returns {"root", "body" (VBoxContainer), "panel"}.
## kind: "paper" | "note" | "card" (ruled index card with a club stripe) | "plain_card" (no stripe).
static func sheet(kind: String, width: float, rot_deg := 0.0, pad := Vector4(26, 26, 26, 24), gap := 12) -> Dictionary:
	var root := Control.new()
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var panel := PanelContainer.new()
	var bg: Color = c("paper")
	var radius := 3
	match kind:
		"note":
			bg = c("note")
			radius = 2
		"card", "plain_card":
			bg = c("card")
	var sb := box(bg, radius)
	sb.content_margin_left = pad.x
	sb.content_margin_top = pad.y
	sb.content_margin_right = pad.z
	sb.content_margin_bottom = pad.w
	if kind == "card":
		sb.border_width_top = 6
		sb.border_color = c("highlight")
	panel.add_theme_stylebox_override("panel", sb)
	panel.custom_minimum_size = Vector2(width, 0)
	panel.size = Vector2(width, 0)
	root.add_child(panel)
	var body := VBoxContainer.new()
	body.add_theme_constant_override("separation", gap)
	panel.add_child(body)
	if kind == "card":
		var lines := RuledLines.new()
		lines.col = c("lines")
		lines.top = 56.0
		lines.pad = pad.x
		lines.set_anchors_preset(Control.PRESET_FULL_RECT)
		lines.mouse_filter = Control.MOUSE_FILTER_IGNORE
		lines.show_behind_parent = false
		panel.add_child(lines)
		panel.move_child(lines, 0)
	root.rotation_degrees = rot_deg
	var sync := func() -> void:
		root.size = panel.size
		root.custom_minimum_size = panel.size
		root.pivot_offset = panel.size * 0.5
	panel.resized.connect(sync)
	sync.call()
	return {"root": root, "body": body, "panel": panel}


## Faint ruled lines on an index card (every 32 px from `top`).
class RuledLines extends Control:
	var col := Color(0, 0, 0, 0.1)
	var top := 56.0
	var pad := 24.0

	func _draw() -> void:
		var y := top
		while y < size.y - 4.0:
			draw_line(Vector2(-pad, y), Vector2(size.x + pad, y), col, 1.0)
			y += 32.0


static func tape(parent: Control, pos: Vector2, rot_deg: float, w := 96.0, neutral := false) -> ColorRect:
	var t := ColorRect.new()
	t.color = Color(Color("#F0E8C8"), 0.82) if neutral else c("tape")
	t.size = Vector2(w, 28)
	t.position = pos
	t.pivot_offset = t.size * 0.5
	t.rotation_degrees = rot_deg
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(t)
	return t


static func pin(parent: Control, x: float, y := -9.0) -> Panel:
	var p := Panel.new()
	var s := StyleBoxFlat.new()
	s.bg_color = c("pin")
	s.set_corner_radius_all(10)
	s.shadow_color = Color(0, 0, 0, 0.35)
	s.shadow_size = 3
	s.shadow_offset = Vector2(0, 3)
	s.anti_aliasing = true
	p.add_theme_stylebox_override("panel", s)
	p.size = Vector2(20, 20)
	p.position = Vector2(x - 10.0, y)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(p)
	# the little highlight that makes it read as a round pin head
	var hl := Panel.new()
	var hs := StyleBoxFlat.new()
	hs.bg_color = Color(1, 1, 1, 0.35)
	hs.set_corner_radius_all(3)
	hl.add_theme_stylebox_override("panel", hs)
	hl.size = Vector2(6, 6)
	hl.position = Vector2(5, 4)
	hl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.add_child(hl)
	return p


# ------------------------------------------------------------------ buttons

static func _btn_style(bg: Color, radius: int, border := 0, border_col := Color.TRANSPARENT, sh := Color.TRANSPARENT, sh_off := 0) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.set_corner_radius_all(radius)
	if border > 0:
		s.set_border_width_all(border)
		s.border_color = border_col
	if sh.a > 0.0:
		s.shadow_color = sh
		s.shadow_size = 1
		s.shadow_offset = Vector2(0, sh_off)
	s.content_margin_left = 18
	s.content_margin_right = 18
	s.anti_aliasing = true
	return s


static func _apply(b: Button, normal: StyleBoxFlat, hover: StyleBoxFlat, pressed: StyleBoxFlat, disabled: StyleBoxFlat,
		fg: Color, fg_disabled: Color, font_w: int, size: int) -> void:
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", hover)
	b.add_theme_stylebox_override("pressed", pressed)
	b.add_theme_stylebox_override("disabled", disabled)
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	for k in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color", "font_hover_pressed_color"]:
		b.add_theme_color_override(k, fg)
	for k in ["icon_normal_color", "icon_hover_color", "icon_pressed_color", "icon_focus_color", "icon_hover_pressed_color"]:
		b.add_theme_color_override(k, fg)
	b.add_theme_color_override("font_disabled_color", fg_disabled)
	b.add_theme_color_override("icon_disabled_color", fg_disabled)
	b.add_theme_font_override("font", font(false, font_w))
	b.add_theme_font_size_override("font_size", size)
	b.add_theme_constant_override("h_separation", 10)
	b.add_theme_constant_override("icon_max_width", 22)
	b.focus_mode = Control.FOCUS_NONE


## The big club-colour button (Play Match, Build it, Recruit).
static func primary(text: String, ic := "", h := 56, size := 20) -> Button:
	var b := Button.new()
	b.text = text
	if ic != "":
		b.icon = icon_tex(ic)
	b.custom_minimum_size = Vector2(0, h)
	var p := club_primary
	var sh := c("button_shadow")
	_apply(b, _btn_style(p, 8, 0, Color.TRANSPARENT, sh, 3), _btn_style(p.lightened(0.08), 8, 0, Color.TRANSPARENT, sh, 3),
		_btn_style(p.darkened(0.08), 8, 0, Color.TRANSPARENT, sh, 1), _btn_style(c("tag_border"), 8),
		c("button_text"), c("muted"), 700, size)
	return b


## Outlined pen-style button ("Build seats", "Full table", "Cancel").
static func link(text: String, ic := "", on_note := false, h := 44) -> Button:
	var b := Button.new()
	b.text = text
	if ic != "":
		b.icon = icon_tex(ic)
	b.custom_minimum_size = Vector2(0, h)
	var ink := c("note_ink") if on_note else c("ink")
	var bg := Color(1, 1, 1, 0.5) if not dark else Color(1, 1, 1, 0.06)
	_apply(b, _btn_style(bg, 6, 2, ink), _btn_style(Color(1, 1, 1, 0.8) if not dark else Color(1, 1, 1, 0.12), 6, 2, ink),
		_btn_style(bg, 6, 2, ink), _btn_style(bg, 6, 2, c("muted")), ink, c("muted"), 600, 16)
	return b


static func icon_button(ic: String, tip: String) -> Button:
	var b := Button.new()
	b.icon = icon_tex(ic)
	b.tooltip_text = tip
	b.custom_minimum_size = Vector2(44, 44)
	b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var n := _btn_style(c("tag"), 6, 1, c("btn_border"))
	n.content_margin_left = 0
	n.content_margin_right = 0
	var hv := n.duplicate()
	hv.border_color = c("ink")
	_apply(b, n, hv, hv, n, c("ink"), c("muted"), 600, 16)
	return b


## Bottom-strip navigation item. Selected = club highlight, lifted.
static func nav_item(text: String, ic: String, selected: bool) -> Button:
	var b := Button.new()
	b.text = text
	b.icon = icon_tex(ic)
	b.alignment = HORIZONTAL_ALIGNMENT_CENTER
	b.custom_minimum_size = Vector2(0, 52)
	var clear := _btn_style(Color(0, 0, 0, 0), 4)
	var hov := _btn_style(Color(0.14, 0.19, 0.23, 0.06), 4)
	var prs := _btn_style(Color(0.14, 0.19, 0.23, 0.10), 4)
	if selected:
		var sel := _btn_style(c("highlight"), 4)
		sel.shadow_color = Color(0, 0, 0, 0.2)
		sel.shadow_size = 3
		sel.shadow_offset = Vector2(0, 3)
		sel.expand_margin_top = 4
		sel.content_margin_bottom = 4
		_apply(b, sel, sel, sel, sel, c("highlight_text"), c("muted"), 600, 17)
	else:
		_apply(b, clear, hov, prs, clear, c("ink"), c("muted"), 600, 17)
	return b


## Small white tag in the top bar: icon + value + label, slightly rotated.
static func stat_tag(ic: String, value: String, lab: String, rot_deg: float, val_col = null) -> Control:
	var wrap := Control.new()
	wrap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var p := PanelContainer.new()
	var s := StyleBoxFlat.new()
	s.bg_color = c("tag")
	s.set_border_width_all(1)
	s.border_color = c("tag_border")
	s.set_corner_radius_all(3)
	s.shadow_color = Color(0, 0, 0, 0.15)
	s.shadow_size = 3
	s.shadow_offset = Vector2(0, 2)
	s.content_margin_left = 14
	s.content_margin_right = 14
	p.add_theme_stylebox_override("panel", s)
	p.custom_minimum_size = Vector2(0, 52)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	var ic_rect := icon(ic, 20, c("pen"))
	ic_rect.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(ic_rect)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", -2)
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	col.add_child(label(value, false, 20, 700, c("ink") if val_col == null else val_col))
	col.add_child(label(lab, false, 14, 500, c("muted")))
	row.add_child(col)
	p.add_child(row)
	wrap.add_child(p)
	wrap.rotation_degrees = rot_deg
	var sync := func() -> void:
		wrap.custom_minimum_size = p.size
		wrap.size = p.size
		wrap.pivot_offset = p.size * 0.5
	p.resized.connect(sync)
	sync.call()
	return wrap


static func progress(pct: float, on_note := true) -> ProgressBar:
	var b := ProgressBar.new()
	b.show_percentage = false
	b.min_value = 0
	b.max_value = 100
	b.value = clampf(pct, 0.0, 100.0)
	b.custom_minimum_size = Vector2(0, 14)
	var ink := c("note_ink") if on_note else c("ink")
	var bg := StyleBoxFlat.new()
	bg.bg_color = c("bar_track") if on_note else c("tag")
	bg.set_border_width_all(2)
	bg.border_color = ink
	bg.set_corner_radius_all(7)
	var fill := StyleBoxFlat.new()
	fill.bg_color = club_primary
	fill.set_corner_radius_all(5)
	fill.set_border_width_all(2)
	fill.border_color = Color(0, 0, 0, 0)
	b.add_theme_stylebox_override("background", bg)
	b.add_theme_stylebox_override("fill", fill)
	b.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return b


## A thin horizontal rule in ink (under headings, table heads).
static func rule(col = null, h := 2) -> ColorRect:
	var r := ColorRect.new()
	r.color = c("ink") if col == null else col
	r.custom_minimum_size = Vector2(0, h)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


## The club-colour highlighter stroke behind your row in a table.
static func highlighter() -> Panel:
	var p := Panel.new()
	var s := StyleBoxFlat.new()
	var h := club_primary
	s.bg_color = Color(h.r, h.g, h.b, 0.32 if dark else 0.26)
	s.corner_radius_top_left = 10
	s.corner_radius_bottom_right = 10
	s.corner_radius_top_right = 4
	s.corner_radius_bottom_left = 4
	p.add_theme_stylebox_override("panel", s)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return p


# ------------------------------------------------------------------ settings controls

static func _circle_tex(d: int, fill: Color, border: Color, bw: float) -> ImageTexture:
	var img := Image.create(d, d, false, Image.FORMAT_RGBA8)
	var r := d * 0.5
	for y in d:
		for x in d:
			var dist := Vector2(x + 0.5 - r, y + 0.5 - r).length()
			var a := clampf(r - dist, 0.0, 1.0)
			if a <= 0.0:
				img.set_pixel(x, y, Color(0, 0, 0, 0))
				continue
			var c := border if dist > r - bw else fill
			img.set_pixel(x, y, Color(c.r, c.g, c.b, c.a * a))
	return ImageTexture.create_from_image(img)


## Slider: ink-outlined track with a club-colour fill and a round knob.
static func slider(value: float, min_v := 0.0, max_v := 100.0) -> HSlider:
	var s := HSlider.new()
	s.min_value = min_v
	s.max_value = max_v
	s.value = value
	s.custom_minimum_size = Vector2(0, 44)
	s.focus_mode = Control.FOCUS_NONE
	var track := StyleBoxFlat.new()
	track.bg_color = c("tag")
	track.set_border_width_all(2)
	track.border_color = c("ink")
	track.set_corner_radius_all(4)
	track.content_margin_top = 4
	track.content_margin_bottom = 4
	var fill := StyleBoxFlat.new()
	fill.bg_color = club_primary
	fill.set_border_width_all(2)
	fill.border_color = c("ink")
	fill.set_corner_radius_all(4)
	fill.content_margin_top = 4
	fill.content_margin_bottom = 4
	s.add_theme_stylebox_override("slider", track)
	s.add_theme_stylebox_override("grabber_area", fill)
	s.add_theme_stylebox_override("grabber_area_highlight", fill)
	var knob := _circle_tex(24, c("tag"), c("ink"), 2.0)
	s.add_theme_icon_override("grabber", knob)
	s.add_theme_icon_override("grabber_highlight", knob)
	return s


## Segmented control (e.g. Light | Dark). Returns the container; callback gets the picked option.
static func segmented(options: Array, selected: String, on_pick: Callable) -> PanelContainer:
	var p := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = c("tag")
	sb.set_border_width_all(2)
	sb.border_color = c("ink")
	sb.set_corner_radius_all(6)
	sb.set_content_margin_all(4)
	p.add_theme_stylebox_override("panel", sb)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 4)
	for o in options:
		var b := nav_item(o, "check" if o == selected else "minus", o == selected)
		b.custom_minimum_size = Vector2(0, 44)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var opt: String = o
		b.pressed.connect(func() -> void: on_pick.call(opt))
		row.add_child(b)
	p.add_child(row)
	return p
