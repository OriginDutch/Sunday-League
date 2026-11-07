class_name Hub
extends CanvasLayer
## Between-match screen: shop, "Who can play for you", squad, play a friendly, post-match summary.

const POSITIONS := ["GK", "LB", "CB", "CB", "RB", "CM", "CDM", "CM", "LW", "ST", "RW"]
const GOAL_SUPPORTERS := 100   # v0.1 done-criterion

var main: Main
var club: ClubState
var root: Control
var top_label: Label
var list_box: VBoxContainer
var play_btn: Button
var hint_label: Label
var wipe_btn: Button
var summary_panel: PanelContainer
var summary_label: Label
var wipe_armed := false
var last_seated := 0


func build(m: Main) -> void:
	main = m
	root = Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	# top bar
	var top_bg := PanelContainer.new()
	top_bg.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	top_bg.offset_bottom = 52
	root.add_child(top_bg)
	top_label = Label.new()
	top_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	top_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	top_label.label_settings = _font(22)
	top_bg.add_child(top_label)

	# left panel (scrolls)
	var panel := PanelContainer.new()
	panel.set_anchors_and_offsets_preset(Control.PRESET_LEFT_WIDE)
	panel.offset_top = 60
	panel.offset_right = 430
	panel.offset_bottom = -10
	panel.offset_left = 10
	root.add_child(panel)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel.add_child(scroll)
	list_box = VBoxContainer.new()
	list_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list_box.add_theme_constant_override("separation", 6)
	scroll.add_child(list_box)

	# play button
	play_btn = Button.new()
	play_btn.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	play_btn.offset_left = -420
	play_btn.offset_top = -90
	play_btn.offset_right = -20
	play_btn.offset_bottom = -20
	play_btn.add_theme_font_size_override("font_size", 22)
	play_btn.pressed.connect(func() -> void: main.start_friendly())
	root.add_child(play_btn)

	# placement / help hint
	hint_label = Label.new()
	hint_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	hint_label.offset_left = -300
	hint_label.offset_right = 300
	hint_label.offset_top = -140
	hint_label.offset_bottom = -100
	hint_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint_label.label_settings = _font(22)
	root.add_child(hint_label)

	# dev: wipe save
	wipe_btn = Button.new()
	wipe_btn.text = "New game"
	wipe_btn.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	wipe_btn.offset_left = -560
	wipe_btn.offset_right = -440
	wipe_btn.offset_top = -60
	wipe_btn.offset_bottom = -20
	wipe_btn.pressed.connect(_on_wipe)
	root.add_child(wipe_btn)

	# post-match summary
	summary_panel = PanelContainer.new()
	summary_panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	summary_panel.offset_left = -300
	summary_panel.offset_right = 300
	summary_panel.offset_top = -230
	summary_panel.offset_bottom = 230
	summary_panel.visible = false
	add_child(summary_panel)
	var sv := VBoxContainer.new()
	sv.add_theme_constant_override("separation", 14)
	summary_panel.add_child(sv)
	summary_label = Label.new()
	summary_label.label_settings = _font(20)
	summary_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	summary_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sv.add_child(summary_label)
	var cont := Button.new()
	cont.text = "Continue"
	cont.add_theme_font_size_override("font_size", 22)
	cont.pressed.connect(func() -> void: main.back_to_hub())
	sv.add_child(cont)


func set_club(c: ClubState) -> void:
	club = c
	refresh()


func refresh() -> void:
	if club == null:
		return
	top_label.text = "£%d   ·   Fans %d   ·   Approval %d%%   ·   Seats %d   ·   Squad %d/%d   ·   W%d D%d L%d   ·   Goal: %d/%d paying supporters" % [
		club.money, club.fans, int(round(club.approval)), club.seats(), club.squad.size(), ClubState.SQUAD_SIZE,
		club.record["w"], club.record["d"], club.record["l"], last_seated, GOAL_SUPPORTERS]

	for c in list_box.get_children():
		c.queue_free()

	_header("SHOP")
	_shop_button("chair", "Chair — £%d  (1 seat)" % ClubState.CHAIR_PRICE)
	_shop_button("bench", "Bench — £%d  (%d seats)" % [ClubState.BENCH_PRICE, ClubState.BENCH_SEATS])
	_small("Fans only pay (£%d) if they have a seat. Everyone else watches for free." % ClubState.TICKET_PRICE)

	_header("WHO CAN PLAY FOR YOU")
	var full := club.squad.size() >= ClubState.SQUAD_SIZE
	for i in club.candidates.size():
		var p: Dictionary = club.candidates[i]
		var row := HBoxContainer.new()
		var l := Label.new()
		l.text = "%s\n  %s" % [p["name"], p["origin"]]
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(l)
		var b := Button.new()
		b.text = "Recruit"
		b.disabled = full
		var idx := i
		b.pressed.connect(func() -> void:
			if club.recruit(idx):
				refresh())
		row.add_child(b)
		list_box.add_child(row)

	_header("SQUAD")
	for i in ClubState.SQUAD_SIZE:
		var l := Label.new()
		if i < club.squad.size():
			var p: Dictionary = club.squad[i]
			l.text = "%-4s %s" % [POSITIONS[i], p["name"]]
		else:
			l.text = "%-4s —" % POSITIONS[i]
			l.modulate = Color(1, 1, 1, 0.45)
		list_box.add_child(l)

	if full:
		play_btn.disabled = false
		play_btn.text = "PLAY FRIENDLY  ▶"
	else:
		play_btn.disabled = true
		play_btn.text = "Need %d players (%d/%d)" % [ClubState.SQUAD_SIZE, club.squad.size(), ClubState.SQUAD_SIZE]
	_update_hint()


func _update_hint() -> void:
	if main.placing_item != "":
		hint_label.text = "Click a free spot for your %s  ·  right-click / Esc to cancel" % main.placing_item
	else:
		hint_label.text = "WASD to look around · mouse wheel to zoom"


func _shop_button(item: String, text: String) -> void:
	var b := Button.new()
	b.text = text
	b.disabled = club.money < club.price_of(item)
	b.pressed.connect(func() -> void:
		main.begin_placing(item)
		_update_hint())
	list_box.add_child(b)


func _header(text: String) -> void:
	var l := Label.new()
	l.text = text
	l.label_settings = _font(20)
	list_box.add_child(l)


func _small(text: String) -> void:
	var l := Label.new()
	l.text = text
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(380, 0)
	l.modulate = Color(1, 1, 1, 0.7)
	list_box.add_child(l)


func _on_wipe() -> void:
	if not wipe_armed:
		wipe_armed = true
		wipe_btn.text = "Sure? Click again"
		return
	wipe_armed = false
	wipe_btn.text = "New game"
	main.new_game()


func show_hub(on: bool) -> void:
	root.visible = on
	if on:
		refresh()


func show_summary(s: Dictionary, opponent: String) -> void:
	last_seated = s["seated"]
	var res := {"W": "WIN", "D": "DRAW", "L": "LOSS"}
	var parts: Dictionary = s["approval_parts"]
	summary_label.text = "%s   %d - %d   vs %s\n\nAttendance: %d\n   %d seated (paid £%d each)\n   %d standing (free)\nTicket income: £%d\n\nFans: %d → %d\nApproval: %d%% → %d%%\n   result %+.1f · entertainment %+.1f · seating %+.1f" % [
		res[s["result"]], s["goals_for"], s["goals_against"], opponent,
		s["attendance"], s["seated"], ClubState.TICKET_PRICE, s["standing"], s["revenue"],
		s["fans_before"], s["fans_after"], int(round(s["approval_before"])), int(round(s["approval_after"])),
		parts["result"], parts["entertainment"], parts["seating"]]
	if s["seated"] >= GOAL_SUPPORTERS:
		summary_label.text += "\n\n★ v0.1 GOAL REACHED: %d paying supporters! ★" % s["seated"]
	summary_panel.visible = true


func hide_summary() -> void:
	summary_panel.visible = false


func _font(size: int) -> LabelSettings:
	var ls := LabelSettings.new()
	ls.font_size = size
	ls.outline_size = maxi(3, size / 7)
	ls.outline_color = Color(0, 0, 0, 0.8)
	return ls
