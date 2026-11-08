class_name Hub
extends CanvasLayer
const LeagueScript = preload("res://scripts/league.gd")
const PyramidScript = preload("res://scripts/pyramid.gd")
const Kit = preload("res://scripts/ui_kit.gd")
const SettingsScript = preload("res://scripts/settings.gd")
## Between-match screens in the Clubhouse Noticeboard style (GDD §10e, design/ui-noticeboard/):
## top bar, bottom strip (ticker + Club / Stadium / Recruitment / Squad / Finances), and per tab:
## Club = Our Goal + Next Match (with mini table), Stadium = build catalogue, Recruitment, Squad.
## Full league table as a pinned sheet. Laid out in design pixels (1920×1080) on a board that is
## scaled to the window.

const POSITIONS := ["GK", "LB", "CB", "CB", "RB", "CM", "CDM", "CM", "LW", "ST", "RW"]
const GOAL_SUPPORTERS := 100   # v0.1 done-criterion
const NAV := [["Club", "club"], ["Stadium", "stadium"], ["Recruitment", "recruit"], ["Squad", "squad"], ["Finances", "finances"]]
const TICKER := ["Rumour has it the chairman is eyeing a second-hand scoreboard. Fancy.",
	"The tea urn is fixed. Morale is up.", "Someone left a shin pad in the dugout. Again.",
	"The groundsman says the grass is 'coming along'.", "Raffle prize this week: a slightly used corner flag."]

var main: Main
var club: ClubState
var root: Control                 # full-window layer (main toggles its visibility)
var board: Control                # 1920×1080 design space, scaled to the window
var screen := "hub"               # "hub" | "menu" (main menu)
var settings_open := false
var menu_new_armed := false
var overlay: Control              # build preview card (kept across refreshes)
var _prev_key := ""
var tab := "Club"
var stand_cat := "Seating"        # Stadium catalogue tab
var rush := false                 # Stands: build the next one as a rush job (+50% cost, 75% of the time)
var table_open := false
var cheats_open := false          # dev cheats (F1 in the hub)
var away_viewing := ""            # dev cheat: away ground on show in the hub
var last_seated := 0
var wipe_armed := false
var _ticker_i := 0



func build(m: Main) -> void:
	main = m
	root = Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	board = Control.new()
	board.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(board)
	overlay = Control.new()
	overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(overlay)
	get_viewport().size_changed.connect(_fit)
	_fit()
	_build_summary()


func _fit() -> void:
	var vp := get_viewport().get_visible_rect().size
	var s := minf(vp.x / Kit.DESIGN.x, vp.y / Kit.DESIGN.y)
	board.scale = Vector2(s, s)
	board.position = Vector2.ZERO
	board.size = vp / s
	overlay.scale = Vector2(s, s)
	overlay.size = vp / s


func set_club(c: ClubState) -> void:
	club = c
	refresh()


func show_hub(on: bool) -> void:
	root.visible = on
	if on:
		refresh()


# ================================================================== layout

func refresh() -> void:
	if club == null or board == null:
		return
	for ch in board.get_children():
		ch.queue_free()
	if screen == "menu":
		_menu()
		if settings_open:
			_settings()
		return
	_top_bar()
	match tab:
		"Club":
			_club_tab()
		"Stadium":
			_stadium_tab()
		"Recruitment":
			_recruitment_tab()
		"Squad":
			_squad_tab()
		"Finances":
			_finances_tab()
	if cheats_open:
		_cheats()
	_strip()
	_hint()
	if table_open:
		_full_table()
	if settings_open:
		_settings()


func go(t: String) -> void:
	if t != "Stadium" and main.placing_item != "":
		main.placing_item = ""
		main.grounds.show_markers(false)
	tab = t
	refresh()


## Put a free control at (x, y) from the top-left, or from the top-right when right = true.
func _at(ctrl: Control, x: float, y: float, w: float, right := false) -> void:
	board.add_child(ctrl)
	if right:
		ctrl.anchor_left = 1.0
		ctrl.anchor_right = 1.0
		ctrl.offset_left = -x - w
		ctrl.offset_right = -x
		ctrl.offset_top = y
	else:
		ctrl.position = Vector2(x, y)


func _hbox(gap := 8) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", gap)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return h


func _vbox(gap := 8) -> VBoxContainer:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", gap)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return v


func _spread(left: Control, right: Control) -> HBoxContainer:
	var h := _hbox(12)
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(left)
	h.add_child(right)
	return h


# ------------------------------------------------------------------ top bar

func _top_bar() -> void:
	var lg: LeagueScript = club.league
	var bar := PanelContainer.new()
	var sb := Kit.box(Kit.c("paper"), 3)
	sb.content_margin_left = 20
	sb.content_margin_right = 16
	bar.add_theme_stylebox_override("panel", sb)
	var holder := Control.new()      # tape/pins can't live inside a container
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	board.add_child(holder)
	holder.anchor_right = 1.0
	holder.offset_left = 32
	holder.offset_right = -32
	holder.offset_top = 24
	holder.offset_bottom = 24 + 84
	holder.add_child(bar)
	bar.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var row := _hbox(14)
	row.alignment = BoxContainer.ALIGNMENT_BEGIN
	bar.add_child(row)
	var crest := Kit.icon("crest_home", 44, Kit.c("pen"))
	crest.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(crest)
	var name_col := _vbox(-4)
	name_col.alignment = BoxContainer.ALIGNMENT_CENTER
	name_col.add_child(Kit.label(ClubState.CLUB_NAME, true, 30, 700, Kit.c("ink")))
	name_col.add_child(Kit.label("The changing rooms are technically a shed.", true, 16, 400, Kit.c("muted")))
	row.add_child(name_col)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(spacer)
	var tags := _hbox(10)
	tags.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var short := club.squad.size() < ClubState.SQUAD_SIZE
	var stats := [
		["fans", str(club.fans), "Fans", null],
		["approval", "%d%%" % int(round(club.approval)), "Fan approval", null],
		["cash", "£%s" % _money(club.money), "Cash", null],
		["seat", str(club.seats()), "Seats", null],
		["shirt", "%d / %d" % [club.squad.size(), ClubState.SQUAD_SIZE], "Squad", Kit.c("danger") if short else null],
		["record", _ordinal(lg.position_of(0)), club.division_name(), null],
		["clock", "Wk %d" % lg.current_week(), "Season %d" % lg.season, null],
	]
	var rots := [-1.0, 0.8, -0.4, 1.0, -0.8, 0.5, -0.6]
	for i in stats.size():
		var s: Array = stats[i]
		tags.add_child(Kit.stat_tag(s[0], s[1], s[2], rots[i], s[3]))
	row.add_child(tags)
	var div := ColorRect.new()
	div.color = Kit.c("div")
	div.custom_minimum_size = Vector2(1, 44)
	div.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(div)
	var set_b := Kit.icon_button("settings", "Settings")
	set_b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	set_b.pressed.connect(func() -> void:
		settings_open = true
		refresh())
	row.add_child(set_b)
	var quit_b := Kit.icon_button("quit", "Quit to menu")
	quit_b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	quit_b.pressed.connect(func() -> void:
		if main.placing_item != "":
			main.placing_item = ""
			main.grounds.show_markers(false)
		club.save()
		screen = "menu"
		refresh())
	row.add_child(quit_b)
	Kit.tape(holder, Vector2(40, -12), -4)
	var rt := Kit.tape(holder, Vector2.ZERO, 3)
	rt.anchor_left = 1.0
	rt.anchor_right = 1.0
	rt.offset_left = -60 - 96
	rt.offset_right = -60
	rt.offset_top = -12
	rt.offset_bottom = 16


# ------------------------------------------------------------------ bottom strip

func _strip() -> void:
	var st := PanelContainer.new()
	var sb := Kit.box(Kit.c("paper"), 3)
	sb.content_margin_left = 22
	sb.content_margin_right = 10
	st.add_theme_stylebox_override("panel", sb)
	var holder := Control.new()
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	board.add_child(holder)
	holder.anchor_left = 0.5
	holder.anchor_right = 0.5
	holder.anchor_top = 1.0
	holder.anchor_bottom = 1.0
	holder.offset_left = -670
	holder.offset_right = 670
	holder.offset_top = -24 - 72
	holder.offset_bottom = -24
	holder.add_child(st)
	st.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var row := _hbox(16)
	st.add_child(row)
	var news := Kit.icon("news", 22, Kit.c("pin"))
	news.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(news)
	var tick := Kit.label(_ticker_text(), true, 20, 700, Kit.c("ink"))
	tick.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tick.clip_text = true
	tick.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	tick.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(tick)
	var div := ColorRect.new()
	div.color = Kit.c("div")
	div.custom_minimum_size = Vector2(1, 40)
	div.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(div)
	var nav := _hbox(4)
	nav.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	for n in NAV:
		var b := Kit.nav_item(n[0], n[1], n[0] == tab)
		var t: String = n[0]
		b.pressed.connect(func() -> void: go(t))
		nav.add_child(b)
	row.add_child(nav)
	Kit.tape(holder, Vector2(-20, -14), -8)


func _ticker_text() -> String:
	var lg: LeagueScript = club.league
	if lg.season_over():
		if not club.playoff_done():
			return "Play-offs! The chairman has ironed his lucky tie."
		return "Season %d is over — we finished %s. The chairman wants a word about next year." % [lg.season, _ordinal(lg.position_of(0))]
	if club.squad.size() < ClubState.SQUAD_SIZE:
		return "We need %d more players before the ref will start the game." % (ClubState.SQUAD_SIZE - club.squad.size())
	if not club.builds.is_empty():
		return "Builders on site. They've had four teas already."
	return TICKER[(club.matches_played + _ticker_i) % TICKER.size()]


# ------------------------------------------------------------------ hints / camera tag

func _hint() -> void:
	var p := PanelContainer.new()
	var sb := Kit.box(Kit.c("paper"), 3)
	sb.content_margin_left = 16
	sb.content_margin_right = 8
	sb.content_margin_top = 8
	sb.content_margin_bottom = 8
	p.add_theme_stylebox_override("panel", sb)
	var row := _hbox(10)
	var txt := "WASD move · wheel zoom · Q/E rotate · R/F tilt · hold right mouse to look · F1 cheats"
	if main.placing_item != "":
		txt = ("Click sections to switch hard core on / off" if main.placing_item == "hardcore" else ("Click a section to build" if main.placing_item in ClubState.SECTION_ITEMS else "Click a free spot")) + " · right click or Esc to cancel"
	var l := Kit.label(txt, false, 15, 500, Kit.c("muted"))
	l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(l)
	var rb := Kit.icon_button("rotate", "Reset camera (C)")
	rb.pressed.connect(func() -> void: main.reset_hub_camera())
	row.add_child(rb)
	p.add_child(row)
	board.add_child(p)
	p.anchor_left = 1.0
	p.anchor_right = 1.0
	p.anchor_top = 1.0
	p.anchor_bottom = 1.0
	p.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	p.grow_vertical = Control.GROW_DIRECTION_BEGIN
	p.offset_right = -32
	p.offset_bottom = -120


# ------------------------------------------------------------------ Club tab

func _club_tab() -> void:
	# Our Goal (sticky note)
	var g := Kit.sheet("note", 410, -1.4, Vector4(26, 28, 26, 24), 12)
	var b: VBoxContainer = g["body"]
	b.add_child(Kit.heading("Our Goal", 38, Kit.c("note_ink")))
	b.add_child(Kit.label("Reach %d paying supporters" % GOAL_SUPPORTERS, false, 20, 600, Kit.c("note_ink"), true))
	b.add_child(_spread(Kit.label("Paying supporters", false, 16, 500, Kit.c("note_muted")),
		Kit.label("%d / %d" % [last_seated, GOAL_SUPPORTERS], false, 18, 700, Kit.c("note_ink"))))
	b.add_child(Kit.progress(100.0 * last_seated / GOAL_SUPPORTERS))
	var left := GOAL_SUPPORTERS - last_seated
	var line := "%d to go!! Ask your nan. And her mates. — Chairman" % left if left > 0 else "Done! The chairman is buying a round. — Chairman"
	b.add_child(Kit.label(line, true, 19, 400, Kit.c("note_muted"), true))
	var bs := Kit.link("Build seats", "stadium", true)
	bs.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	bs.pressed.connect(func() -> void: go("Stadium"))
	b.add_child(bs)
	Kit.tape(g["root"], Vector2(156, -14), 2)
	_at(g["root"], 40, 146, 410)

	# Next Match (index card)
	var lg: LeagueScript = club.league
	var m := Kit.sheet("card", 440, 0.9, Vector4(24, 24, 24, 18), 14)
	var mb: VBoxContainer = m["body"]
	var pf: Dictionary = club.playoff_fixture() if lg.season_over() else {}
	if not pf.is_empty():
		# your next play-off leg (GDD §6)
		var staying := int(club.playoff["div"]) < club.division()
		mb.add_child(_spread(Kit.heading(ClubState.round_name(pf["round"], pf["tie"]).replace("Play-off ", "Play-off\n"), 36),
			Kit.caps(club.division_name(int(club.playoff["div"])))))
		var sub := "Week %d · %s leg · %s" % [lg.current_week(), "1st" if int(pf["leg"]) == 0 else "2nd", "home" if pf["home"] else "away"]
		mb.add_child(Kit.label(sub, false, 15, 500, Kit.c("muted")))
		var opp_name: String = pf["opponent"]["name"]
		var us_name := ClubState.CLUB_NAME
		var teams_pf := GridContainer.new()
		teams_pf.columns = 3
		teams_pf.mouse_filter = Control.MOUSE_FILTER_IGNORE
		teams_pf.add_child(_team(us_name if pf["home"] else opp_name, "crest_home" if pf["home"] else "crest_away", pf["home"]))
		var vs_pf := Kit.label("vs", true, 32, 700, Kit.c("pen"))
		vs_pf.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		vs_pf.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		vs_pf.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		teams_pf.add_child(vs_pf)
		teams_pf.add_child(_team(opp_name if pf["home"] else us_name, "crest_away" if pf["home"] else "crest_home", not pf["home"]))
		mb.add_child(teams_pf)
		if pf.has("first_leg"):
			mb.add_child(Kit.label("First leg: %d–%d to %s. Level after this one: extra time, then penalties." % [
				maxi(pf["first_leg"][0], pf["first_leg"][1]), mini(pf["first_leg"][0], pf["first_leg"][1]),
				"us" if pf["first_leg"][0] > pf["first_leg"][1] else ("them" if pf["first_leg"][0] < pf["first_leg"][1] else "nobody")],
				true, 18, 400, Kit.c("muted"), true))
		else:
			mb.add_child(Kit.label("Win and we stay up. Lose and we go down." if staying else "Two legs. The winner of the final goes up.",
				true, 18, 400, Kit.c("muted"), true))
		var pp := Kit.primary("Play %s" % ("1st leg" if int(pf["leg"]) == 0 else "2nd leg"), "play")
		pp.disabled = club.squad.size() < ClubState.SQUAD_SIZE
		pp.pressed.connect(_on_play)
		mb.add_child(pp)
	elif lg.season_over():
		mb.add_child(_spread(Kit.heading("Season %d over" % lg.season, 36), Kit.caps(club.division_name())))
		mb.add_child(Kit.label("We finished %s." % _ordinal(lg.position_of(0)), false, 20, 600, Kit.c("ink")))
		var eo := club.expected_outcome()
		var po_line := club._playoff_summary()
		if po_line != "":
			mb.add_child(Kit.label(po_line + ".", false, 18, 600, Kit.c("ink")))
		match eo["outcome"]:
			"promoted":
				mb.add_child(Kit.label("Promoted to %s!" % club.division_name(eo["to"]), true, 26, 700, Kit.c("ok")))
			"relegated":
				mb.add_child(Kit.label("Relegated to %s." % club.division_name(eo["to"]), true, 24, 700, Kit.c("danger")))
			_:
				if eo["denied"]:
					mb.add_child(Kit.label("Not enough seats: %s needs %d, we have %d. Our place goes to the next club." % [
						club.division_name(club.division() + 1), club.seats_needed_up(), club.seats()], true, 19, 600, Kit.c("danger"), true))
				else:
					mb.add_child(Kit.label("Another year in %s." % club.division_name(), true, 19, 400, Kit.c("muted"), true))
		var ns := Kit.primary("Start season %d" % (lg.season + 1), "play")
		ns.pressed.connect(_on_play)
		mb.add_child(ns)
		mb.add_child(Kit.label("Skips the %d-week off-season" % LeagueScript.OFFSEASON_WEEKS, false, 14, 500, Kit.c("muted")))
	else:
		var fx: Dictionary = lg.next_fixture()
		mb.add_child(_spread(Kit.heading("Next Match"), Kit.caps(club.division_name())))
		var rp: Dictionary = club.last_report
		if not rp.is_empty() and int(rp["season"]) == lg.season - 1 and lg.round_idx == 0:
			var rtxt := "Welcome to %s." % club.division_name()
			if rp["outcome"] == "promoted":
				rtxt = "Promoted! Welcome to %s." % club.division_name()
			elif rp["outcome"] == "relegated":
				rtxt = "Relegated. %s it is." % club.division_name()
			elif rp.get("denied", false):
				rtxt = "No promotion: not enough seats. Still %s." % club.division_name()
			else:
				rtxt = "Another season in %s." % club.division_name()
			mb.add_child(Kit.label(rtxt, true, 20, 700, Kit.c("pen"), true))
		mb.add_child(Kit.label("Week %d · round %d of %d · %s" % [fx["week"], fx["round"], lg.rounds.size(), "home" if fx["home"] else "away"],
			false, 15, 500, Kit.c("muted")))
		var opp: String = lg.teams[fx["opponent"]]["name"]
		var us := ClubState.CLUB_NAME
		var home_name := us if fx["home"] else opp
		var away_name := opp if fx["home"] else us
		var teams := GridContainer.new()
		teams.columns = 3
		teams.mouse_filter = Control.MOUSE_FILTER_IGNORE
		teams.add_child(_team(home_name, "crest_home" if fx["home"] else "crest_away", fx["home"]))
		var vs := Kit.label("vs", true, 32, 700, Kit.c("pen"))
		vs.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		vs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		vs.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		teams.add_child(vs)
		teams.add_child(_team(away_name, "crest_away" if fx["home"] else "crest_home", not fx["home"]))
		mb.add_child(teams)
		var play := Kit.primary("Play Match", "play")
		var short := ClubState.SQUAD_SIZE - club.squad.size()
		play.disabled = short > 0
		play.pressed.connect(_on_play)
		mb.add_child(play)
		if short > 0:
			mb.add_child(_warning("You need %d players. You have %d." % [ClubState.SQUAD_SIZE, club.squad.size()],
				"The ref won't start with %d. We asked." % club.squad.size(), "Recruit %d more" % short, "Recruitment"))
		elif not fx["home"]:
			mb.add_child(Kit.label("Away: no ticket income, %d%% of our fans travel along." % int(Main.AWAY_TRAVEL_SHARE * 100),
				false, 14, 500, Kit.c("muted"), true))
	mb.add_child(_mini_table())
	Kit.pin(m["root"], 220)
	_at(m["root"], 40, 132, 440, true)


func _team(n: String, crest: String, ours: bool) -> Control:
	var v := _vbox(6)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var cr := Kit.icon(crest, 56, Kit.c("pen") if ours else Kit.c("ink"))
	cr.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(cr)
	var l := Kit.label(n, false, 17, 700, Kit.c("ink"), true)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.custom_minimum_size = Vector2(120, 0)
	v.add_child(l)
	return v


func _warning(text: String, flavour: String, action: String, to_tab: String) -> Control:
	var p := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0)
	sb.set_border_width_all(2)
	sb.border_color = Kit.c("danger")
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 14
	sb.content_margin_right = 14
	sb.content_margin_top = 12
	sb.content_margin_bottom = 12
	p.add_theme_stylebox_override("panel", sb)
	var row := _hbox(10)
	var ic := Kit.icon("warn", 20, Kit.c("danger"))
	ic.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	row.add_child(ic)
	var col := _vbox(8)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.add_child(Kit.label(text, false, 16, 600, Kit.c("ink"), true))
	col.add_child(Kit.label(flavour, true, 18, 400, Kit.c("muted"), true))
	var b := Kit.link(action, "recruit")
	b.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	b.pressed.connect(func() -> void: go(to_tab))
	col.add_child(b)
	row.add_child(col)
	p.add_child(row)
	return p


func _mini_table() -> Control:
	var lg: LeagueScript = club.league
	var t: Array = lg.table()
	var me := 0
	for i in t.size():
		if t[i]["team"] == 0:
			me = i
	var from := clampi(me - 2, 0, t.size() - 5)
	var v := _vbox(2)
	v.add_child(Kit.rule())
	v.add_child(_row(["Pos", "Team", "P", "Pts"], [36, 0, 32, 40], 13, 700, Kit.c("muted"), false, true))
	for i in range(from, from + 5):
		var r: Dictionary = t[i]
		var ours: bool = r["team"] == 0
		v.add_child(_row([str(i + 1), r["name"], str(r["p"]), str(r["pts"])], [36, 0, 32, 40], 15, 700 if ours else 500,
			Kit.c("ink"), ours))
	var full := LinkButton.new()
	full.text = "Full table →"
	full.underline = LinkButton.UNDERLINE_MODE_ALWAYS
	full.add_theme_font_override("font", Kit.font(true, 700))
	full.add_theme_font_size_override("font_size", 19)
	for k in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		full.add_theme_color_override(k, Kit.c("pen"))
	full.size_flags_horizontal = Control.SIZE_SHRINK_END
	full.focus_mode = Control.FOCUS_NONE
	full.pressed.connect(func() -> void:
		table_open = true
		refresh())
	v.add_child(full)
	return v


## A table row: cells with fixed widths (0 = expand); numbers right-aligned; optional highlighter.
func _row(cells: Array, widths: Array, size: int, weight: int, col: Color, highlight := false, caps := false) -> Control:
	var wrap := Control.new()
	wrap.custom_minimum_size = Vector2(0, 30 if size <= 15 else 34)
	wrap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if highlight:
		var hl := Kit.highlighter()
		hl.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		hl.offset_left = -6
		hl.offset_right = 4
		hl.offset_top = 3
		hl.offset_bottom = -3
		hl.rotation_degrees = -0.6
		wrap.add_child(hl)
	var h := _hbox(8)
	h.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	h.offset_left = 6
	h.offset_right = -6
	for i in cells.size():
		var l := Kit.label(str(cells[i]).to_upper() if caps else str(cells[i]), false, size, weight, col)
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		l.size_flags_vertical = Control.SIZE_FILL
		var w: int = widths[i]
		if w == 0:
			l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			l.clip_text = true
			l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		else:
			l.custom_minimum_size = Vector2(w, 0)
			if i > 1 or (i == 0 and false):
				l.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		h.add_child(l)
	wrap.add_child(h)
	return wrap


func _on_play() -> void:
	if away_viewing != "":
		away_viewing = ""
		main.cheat_view_home()
	if club.league.season_over() and club.playoff_done():
		main.next_season()
	else:
		main.start_friendly()


# ------------------------------------------------------------------ full table (pinned A4 sheet)

func _full_table() -> void:
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.35)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.gui_input.connect(func(e: InputEvent) -> void:
		if e is InputEventMouseButton and (e as InputEventMouseButton).pressed:
			table_open = false
			refresh())
	board.add_child(dim)
	var lg: LeagueScript = club.league
	var s := Kit.sheet("card", 720, 0.4, Vector4(34, 22, 30, 18), 2)
	var b: VBoxContainer = s["body"]
	var close := Kit.icon_button("close", "Close")
	close.pressed.connect(func() -> void:
		table_open = false
		refresh())
	b.add_child(_spread(Kit.heading("%s — Season %d" % [club.division_name(), lg.season], 36), close))
	b.add_child(Kit.label("Week %d of %d" % [lg.current_week(), LeagueScript.SEASON_WEEKS], false, 15, 500, Kit.c("muted")))
	var W := [40, 0, 40, 40, 40, 40, 52, 52]
	b.add_child(Kit.rule())
	b.add_child(_row(["#", "Team", "P", "W", "D", "L", "GD", "Pts"], W, 13, 700, Kit.c("muted"), false, true))
	var t: Array = lg.table()
	for i in t.size():
		var r: Dictionary = t[i]
		var ours: bool = r["team"] == 0
		var gd: int = r["gd"]
		b.add_child(_row([str(i + 1), r["name"], str(r["p"]), str(r["w"]), str(r["d"]), str(r["l"]),
			("+%d" % gd) if gd > 0 else ("−%d" % -gd if gd < 0 else "0"), str(r["pts"])], W, 15, 700 if ours else 500,
			Kit.c("ink"), ours))
		# zone lines (GDD §6): the bottom division has no relegation, the top one no promotion
		var dv := club.division()
		if i == 1 and PyramidScript.has_promotion(dv):
			b.add_child(_zone_line("Promotion ↑  (needs %d seats)" % club.seats_needed_up()))
		elif i == 6 and PyramidScript.has_promotion(dv):
			b.add_child(_zone_line("Play-offs ↑ (3rd–7th + 18th of the division above)"))
		elif i == 16 and PyramidScript.has_relegation(dv):
			b.add_child(_zone_line("18th: play-offs against the division below"))
		elif i == 17 and PyramidScript.has_relegation(dv):
			b.add_child(_zone_line("Relegation ↓"))
	Kit.pin(s["root"], 360)
	board.add_child(s["root"])
	s["root"].anchor_left = 0.5
	s["root"].anchor_right = 0.5
	s["root"].offset_left = -360
	s["root"].offset_right = 360
	s["root"].offset_top = 92


func _zone_line(text: String) -> Control:
	var v := _hbox(8)
	var line := ColorRect.new()
	line.color = Kit.c("pen")
	line.custom_minimum_size = Vector2(0, 2)
	line.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	line.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	v.add_child(line)
	v.add_child(Kit.label(text, true, 17, 700, Kit.c("pen")))
	return v


# ------------------------------------------------------------------ Stadium tab (build catalogue)

func _stadium_tab() -> void:
	var s := Kit.sheet("plain_card", 444, -0.5, Vector4(18, 22, 18, 18), 14)
	var b: VBoxContainer = s["body"]
	b.add_child(_spread(Kit.heading("Build", 34), Kit.label("Esc to stop building", false, 14, 500, Kit.c("muted"))))
	var tabs := _hbox(4)
	for cat in [["Seating", "seat"], ["Stands", "stadium"], ["Fans", "fans"]]:
		var tb := Kit.nav_item(cat[0], cat[1], cat[0] == stand_cat)
		tb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var cname: String = cat[0]
		tb.pressed.connect(func() -> void:
			stand_cat = cname
			refresh())
		tabs.add_child(tb)
	b.add_child(tabs)
	b.add_child(Kit.rule())
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 14)
	grid.add_theme_constant_override("v_separation", 14)
	if stand_cat == "Fans":
		grid.add_child(_shop_card("hardcore", "Hard core", "fans", "%d section%s" % [club.hardcore.size(), "" if club.hardcore.size() == 1 else "s"],
			"Free · click sections on / off", "Flags, scarves, songs. Standing, mostly."))
	elif stand_cat == "Seating":
		grid.add_child(_shop_card("chair", "Chair", "seat", "+1 seat", "Instant · up to %d per spot" % ClubState.MAX_CHAIRS_PER_SLOT, "Folding. Mostly."))
		grid.add_child(_shop_card("bench", "Bench", "seat", "+%d seats" % ClubState.BENCH_SEATS, "Instant", "Seats four. Five if you're friendly."))
	else:
		# rush is one switch for every stand card (8 cards didn't fit)
		var rb := CheckButton.new()
		rb.text = "Rush build: +50% cost, 75% of the time"
		rb.button_pressed = rush
		rb.focus_mode = Control.FOCUS_NONE
		rb.add_theme_font_override("font", Kit.font(false, 600))
		rb.add_theme_font_size_override("font_size", 16)
		rb.add_theme_color_override("font_color", Kit.c("ink"))
		rb.add_theme_color_override("font_pressed_color", Kit.c("ink"))
		rb.add_theme_color_override("font_hover_color", Kit.c("ink"))
		rb.toggled.connect(func(on: bool) -> void:
			rush = on
			if main.placing_item != "" and main.placing_item in ClubState.SECTION_ITEMS:
				main.placing_item = ClubState.item_stage(main.placing_item) + ("_rush" if on else "")
			refresh())
		b.add_child(rb)
		var sfx := "_rush" if rush else ""
		var flav := {"bleachers": "Cold in January.", "shed": "A roof! Ticket +25%.",
			"main": "Columns. Ticket +50%.", "rows": "Up we go."}
		var icons := {"bleachers": "stadium", "shed": "stadium", "main": "stadium", "rows": "plus"}
		for st in ClubState.STAGE_ORDER:
			var info_st: Dictionary = ClubState.STAGES[st]
			var steps: Array = info_st["rows"]
			# short texts: a long "adds" line made the card wider than its slot (Marcel 2026-11-09)
			grid.add_child(_shop_card(st + sfx, info_st["name"], icons[st], "+%d seats" % (int(steps[0]) * ClubState.BLEACHER_SEATS_PER_ROW),
				"%s wk · rows %s · +%d wk to demolish" % [_wk(club.build_weeks(st + sfx)), "/".join(steps.map(func(x): return str(x))), int(ClubState.DEMOLITION_WEEKS)], flav[st]))
		grid.add_child(_shop_card("rows" + sfx, "More rows", icons["rows"], "next step",
			"on any stand · its price per place", flav["rows"]))
	b.add_child(grid)
	var info := _hbox(8)
	info.add_child(Kit.icon("info", 18, Kit.c("pen")))
	var it := Kit.label("Pick an item, then click a free spot or section in the ground. A section is closed while it's being built.",
		false, 15, 500, Kit.c("muted"), true)
	it.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.add_child(it)
	b.add_child(info)
	if not club.builds.is_empty():
		b.add_child(Kit.caps("Under construction", Kit.c("muted")))
		for bd in club.builds:
			b.add_child(Kit.label("Section %d · %s, %d rows · ready %s" % [int(bd["sec"]) + 1, ClubState.STAGES[bd.get("stage", "bleachers")]["name"], int(bd["rows"]), club.ready_label(bd)],
				false, 15, 600, Kit.c("ink"), true))
	Kit.pin(s["root"], 222)
	_at(s["root"], 40, 140, 444)


func _shop_card(item: String, title: String, ic: String, adds: String, note: String, flavour: String) -> Control:
	var price := club.build_cost(item) if item in ClubState.SECTION_ITEMS else club.price_of(item)
	var afford := club.money >= price
	var selected := main.placing_item == item
	var btn := Button.new()
	btn.custom_minimum_size = Vector2(196, 168)
	btn.focus_mode = Control.FOCUS_NONE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Kit.c("card")
	sb.set_border_width_all(1)
	sb.border_color = Kit.c("tag_border")
	sb.border_width_top = 6
	sb.set_corner_radius_all(3)
	sb.shadow_color = Color(0, 0, 0, 0.18)
	sb.shadow_size = 4
	sb.shadow_offset = Vector2(0, 2)
	var normal := sb.duplicate()
	normal.border_color = Kit.c("tag_border")
	var hover := sb.duplicate()
	hover.shadow_color = Color(0, 0, 0, 0.3)
	hover.shadow_size = 9
	hover.shadow_offset = Vector2(0, 7)
	var sel := hover.duplicate()
	sel.border_color = Kit.c("highlight")
	for k in ["normal", "hover", "pressed", "disabled"]:
		btn.add_theme_stylebox_override(k, sel if selected else (hover if k == "hover" else normal))
	btn.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	btn.disabled = not afford
	var v := _vbox(6)
	v.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	v.offset_left = 16
	v.offset_right = -14
	v.offset_top = 14
	v.offset_bottom = -12
	var tc := Kit.c("ink") if afford else Kit.c("muted")
	var head := _hbox(10)
	head.add_child(Kit.icon(ic, 24, tc))
	var tl := Kit.label(title, false, 18, 700, tc)
	tl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(tl)
	v.add_child(head)
	v.add_child(Kit.label(flavour, true, 17, 400, Kit.c("pen") if afford else Kit.c("muted"), true))
	var pr := Kit.label("£%s" % _money(price), false, 20, 700, Kit.c("ink") if afford else Kit.c("danger"))
	var ad := Kit.label(adds, false, 15, 600, Kit.c("ok") if afford else Kit.c("muted"))
	ad.size_flags_vertical = Control.SIZE_SHRINK_END
	v.add_child(_spread(pr, ad))
	if afford:
		v.add_child(Kit.label(note, false, 13, 500, Kit.c("muted"), true))
	else:
		var f := _hbox(6)
		f.add_child(Kit.icon("lock", 16, Kit.c("danger")))
		f.add_child(Kit.label("£%s short" % _money(price - club.money), false, 14, 600, Kit.c("danger")))
		v.add_child(f)
	btn.add_child(v)
	if selected:
		Kit.pin(btn, 98)
	btn.pressed.connect(func() -> void:
		main.begin_placing(item)
		refresh())
	return btn


# ------------------------------------------------------------------ Recruitment tab

func _recruitment_tab() -> void:
	var n := Kit.sheet("note", 380, -1.2, Vector4(26, 28, 26, 24), 12)
	var b: VBoxContainer = n["body"]
	b.add_child(Kit.heading("Who can play for you", 36, Kit.c("note_ink")))
	b.add_child(Kit.label("Recruiting is free. You need %d players to play a match." % ClubState.SQUAD_SIZE, false, 16, 500, Kit.c("note_ink"), true))
	b.add_child(_spread(Kit.label("Squad", false, 16, 500, Kit.c("note_muted")),
		Kit.label("%d / %d" % [club.squad.size(), ClubState.SQUAD_SIZE], false, 18, 700, Kit.c("note_ink"))))
	b.add_child(Kit.progress(100.0 * club.squad.size() / ClubState.SQUAD_SIZE))
	var left := ClubState.SQUAD_SIZE - club.squad.size()
	b.add_child(Kit.label("%d more. Someone always knows a lad." % left if left > 0 else "Full squad. The kit bag is officially heavy.",
		true, 19, 400, Kit.c("note_muted"), true))
	Kit.tape(n["root"], Vector2(140, -14), -2)
	_at(n["root"], 40, 150, 380)

	var full := club.squad.size() >= ClubState.SQUAD_SIZE
	var rots := [-1.2, 0.8, -0.5, 1.1, 0.6, -0.9, 1.0, -0.6]
	var cw := 333.0
	for i in club.candidates.size():
		var p: Dictionary = club.candidates[i]
		var c := Kit.sheet("plain_card", cw, rots[i % rots.size()], Vector4(20, 22, 20, 18), 10)
		var cb: VBoxContainer = c["body"]
		var head := _hbox(12)
		var ring := PanelContainer.new()
		var rs := StyleBoxFlat.new()
		rs.bg_color = Color(0, 0, 0, 0)
		rs.set_border_width_all(2)
		rs.border_color = Kit.c("ink")
		rs.set_corner_radius_all(22)
		ring.add_theme_stylebox_override("panel", rs)
		ring.custom_minimum_size = Vector2(44, 44)
		var ri := Kit.icon("recruit", 22, Kit.c("ink"))
		ring.add_child(ri)
		head.add_child(ring)
		var nl := Kit.label(p["name"], false, 20, 700, Kit.c("ink"))
		nl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		head.add_child(nl)
		cb.add_child(head)
		var ol := Kit.label(p["origin"], true, 20, 400, Kit.c("pen"), true)
		ol.custom_minimum_size = Vector2(0, 52)
		cb.add_child(ol)
		var rb := Kit.primary("Recruit", "plus", 44, 16)
		rb.disabled = full
		var idx := i
		rb.pressed.connect(func() -> void:
			if club.recruit(idx):
				club.save()
				refresh())
		cb.add_child(_spread(Kit.label("Free", false, 14, 500, Kit.c("muted")), rb))
		Kit.pin(c["root"], cw * 0.5)
		var col := i % 4
		var rowi := i / 4
		_at(c["root"], 470 + col * (cw + 26), 150 + rowi * 230, cw)


# ------------------------------------------------------------------ Squad tab

func _squad_tab() -> void:
	var s := Kit.sheet("plain_card", 920, 0.3, Vector4(24, 20, 24, 16), 10)
	var b: VBoxContainer = s["body"]
	var n := club.squad.size()
	var ready := n >= ClubState.SQUAD_SIZE
	b.add_child(_spread(Kit.heading("Squad"), Kit.label("%d / %d · %s" % [n, ClubState.SQUAD_SIZE, "ready to play" if ready else "not enough players"],
		false, 18, 700, Kit.c("ok") if ready else Kit.c("danger"))))
	var W := [40, 70, 260, 0, 110]
	b.add_child(Kit.rule())
	b.add_child(_squad_row(["#", "Pos", "Name", "Where from", "Status"], W, true))
	for i in ClubState.SQUAD_SIZE:
		if i < n:
			var p: Dictionary = club.squad[i]
			b.add_child(_squad_row([str(i + 1), POSITIONS[i], p["name"], p["origin"], "Available"], W))
		else:
			b.add_child(_squad_row([str(i + 1), POSITIONS[i], "—", "", ""], W))
	Kit.pin(s["root"], 276)
	Kit.pin(s["root"], 644)
	_at(s["root"], 500, 132, 920)
	_formation_card()


# ------------------------------------------------------------------ Finances tab (Marcel, 2026-11-08; mock-up S_Finances)

const LEDGER_ROWS := 6


func _finances_tab() -> void:
	var lg: LeagueScript = club.league
	var season := lg.season
	var tot: Dictionary = club.season_totals(season)
	var notes := {"Sponsor": ClubState.SPONSOR_NAME, "Prize money": "end of season", "League fee": "week 1"}
	# --- this season, per category
	var s := Kit.sheet("card", 430, -0.6, Vector4(26, 22, 26, 18), 2)
	var b: VBoxContainer = s["body"]
	b.add_child(_spread(Kit.heading("This season", 36), Kit.caps("Week %d / %d" % [mini(lg.current_week(), LeagueScript.SEASON_WEEKS), LeagueScript.SEASON_WEEKS])))
	b.add_child(Kit.caps("Money in", Kit.c("muted")))
	var ti := 0.0
	for k in tot["in"]:
		var v: float = tot["in"][k]
		ti += v
		b.add_child(_fin_row(k, notes.get(k, ""), _pounds(v), Kit.c("ok") if v > 0.0 else Kit.c("muted")))
	b.add_child(Kit.rule(Kit.c("div"), 1))
	b.add_child(Kit.caps("Money out", Kit.c("muted")))
	var to := 0.0
	for k in tot["out"]:
		var v: float = tot["out"][k]
		to += v
		b.add_child(_fin_row(k, notes.get(k, ""), _pounds(v), Kit.c("danger") if v < 0.0 else Kit.c("muted")))
	b.add_child(Kit.rule())
	var net := ti + to
	b.add_child(_fin_row("In − out", "", _pounds(net, true), Kit.c("ok") if net >= 0.0 else Kit.c("danger"), true))
	b.add_child(Kit.label("Up on the season. The tea hut is carrying us." if net >= 0.0 else "Down on the season. Nan's doing a bake sale.",
		true, 19, 400, Kit.c("pen"), true))
	Kit.pin(s["root"], 222)
	_at(s["root"], 40, 140, 430)
	_ledger_card(season)
	_cash_card(season)
	_coming_up()


func _fin_row(lab: String, note: String, val: String, col: Color, bold := false) -> Control:
	var h := _hbox(8)
	h.custom_minimum_size = Vector2(0, 32)
	var l := Kit.label(lab, false, 19 if bold else 16, 700 if bold else 500, Kit.c("ink") if bold else Kit.c("muted"))
	l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(l)
	if note != "":
		var n := Kit.label(note, true, 17, 400, Kit.c("muted"))
		n.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(n)
	var sp := Control.new()
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(sp)
	var v := Kit.label(val, false, 19 if bold else 17, 700 if bold else 600, col)
	v.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(v)
	return h


## Match by match (newest first). Every match is stored with all its lines, so a row can open a
## breakdown later (Marcel: not clickable yet, maybe later); opponent crests go in the crest column.
func _ledger_card(season: int) -> void:
	var s := Kit.sheet("plain_card", 820, 0.3, Vector4(24, 22, 24, 16), 8)
	var b: VBoxContainer = s["body"]
	b.add_child(_spread(Kit.heading("Match by match", 36), Kit.label("Season %d" % season, false, 15, 500, Kit.c("muted"))))
	b.add_child(Kit.rule())
	var W := [62, 26, 0, 40, 64, 84, 84, 92]
	b.add_child(_ledger_row(["Week", "", "Opponent", "", "Result", "In", "Out", "Net"], W, true))
	var matches := []
	for e in club.ledger:
		if e["kind"] == "match" and int(e["season"]) == season:
			matches.append(e)
	matches.reverse()
	if matches.is_empty():
		b.add_child(Kit.label("No matches yet this season.", true, 20, 400, Kit.c("muted")))
	for i in mini(LEDGER_ROWS, matches.size()):
		var e: Dictionary = matches[i]
		var ein := ClubState.entry_in(e)
		var eout := ClubState.entry_out(e)
		b.add_child(_ledger_row(["Wk %d" % int(e["week"]), "crest", e["title"], "H" if e.get("home", true) else "A",
			"%s %s" % [e.get("result", ""), e.get("score", "")], _pounds(ein), _pounds(eout), _pounds(ein + eout, true)], W))
	if matches.size() > LEDGER_ROWS:
		b.add_child(Kit.label("+ %d earlier" % (matches.size() - LEDGER_ROWS), false, 14, 500, Kit.c("muted")))
	b.add_child(Kit.label("Away days cost a fiver. Home days pay the bills.", true, 19, 400, Kit.c("pen")))
	Kit.pin(s["root"], 246)
	Kit.pin(s["root"], 574)
	_at(s["root"], 500, 140, 820)


func _ledger_row(cells: Array, widths: Array, head := false) -> Control:
	var wrap := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0)
	sb.border_width_bottom = 1
	sb.border_color = Kit.c("tag_border")
	sb.content_margin_left = 12
	sb.content_margin_right = 12
	wrap.add_theme_stylebox_override("panel", sb)
	wrap.custom_minimum_size = Vector2(0, 30 if head else 40)
	var h := _hbox(10)
	for i in cells.size():
		var c: Control
		var txt: String = cells[i]
		if head:
			c = Kit.caps(txt, Kit.c("muted"))
		elif i == 1:
			c = Kit.icon("crest_away", 22, Kit.c("ink"))       # opponent crest (real logos later)
		elif i == 3:
			c = Kit.label(txt, false, 13, 700, Kit.c("ink"))
		elif i == 4:
			var col := Kit.c("ok") if txt.begins_with("W") else (Kit.c("danger") if txt.begins_with("L") else Kit.c("muted"))
			c = Kit.label(txt, false, 15, 700, col)
		elif i >= 5:
			var col2 := Kit.c("ok") if i == 5 else (Kit.c("danger") if i == 6 else (Kit.c("danger") if txt.begins_with("-") else Kit.c("ok")))
			c = Kit.label(txt, false, 16, 700 if i == 7 else 600, col2)
		elif i == 2:
			c = Kit.label(txt, false, 16, 600, Kit.c("ink"))
		else:
			c = Kit.label(txt, false, 15, 600, Kit.c("muted"))
		if c is Label:
			(c as Label).vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			if i >= 5:
				(c as Label).horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
			(c as Label).clip_text = true
		c.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		var w: int = widths[i]
		if w == 0:
			c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		else:
			c.custom_minimum_size = Vector2(w, c.custom_minimum_size.y)
		h.add_child(c)
	wrap.add_child(h)
	return wrap


func _cash_card(season: int) -> void:
	var s := Kit.sheet("plain_card", 820, -0.4, Vector4(24, 16, 24, 10), 4)
	var b: VBoxContainer = s["body"]
	b.add_child(_spread(Kit.heading("Cash", 34), Kit.caps("This season, per week")))
	var chart := CashChart.new()
	chart.custom_minimum_size = Vector2(770, 160)
	var pts := []
	var start_cash := -1
	for c in club.cash_log:
		if int(c["season"]) == season:
			pts.append(Vector2(float(c["week"]), float(c["cash"])))
		elif int(c["season"]) < season:
			start_cash = int(c["cash"])
	if start_cash >= 0 and (pts.is_empty() or pts[0].x > 0.0):
		pts.push_front(Vector2(0, start_cash))
	# one dot per week you built something: "4× chair, bench"
	var per_week := {}
	for e in club.ledger:
		if e["kind"] == "build" and int(e["season"]) == season:
			var wk := int(e["week"])
			if not per_week.has(wk):
				per_week[wk] = {}
			var t := String(e["title"]).to_lower()
			per_week[wk][t] = int(per_week[wk].get(t, 0)) + 1
	var marks := []
	for wk in per_week:
		var parts := []
		for t in per_week[wk]:
			var n: int = per_week[wk][t]
			parts.append(t if n == 1 else "%d× %s" % [n, t])
		marks.append([float(wk), ", ".join(parts)])
	chart.points = pts
	chart.marks = marks
	chart.weeks = LeagueScript.SEASON_WEEKS
	for p in pts:
		chart.weeks = maxi(chart.weeks, int(p.x))   # play-off weeks 43–45
	b.add_child(chart)
	Kit.tape(s["root"], Vector2(360, -14), 2)
	_at(s["root"], 500, 652, 820)


func _coming_up() -> void:
	var n := Kit.sheet("note", 360, 1.4, Vector4(24, 26, 24, 22), 14)
	var b: VBoxContainer = n["body"]
	b.add_child(Kit.heading("Coming up", 34, Kit.c("note_ink")))
	for bd in club.builds:
		b.add_child(_coming("clock", "Section %d bleachers" % (int(bd["sec"]) + 1), "paid · ready %s" % club.ready_label(bd), Kit.c("note_ink")))
	var lg: LeagueScript = club.league
	var fx: Dictionary = lg.next_fixture()
	if not fx.is_empty():
		var opp: String = lg.teams[fx["opponent"]]["name"]
		var subs := club.squad.size() * ClubState.SUBS_PER_PLAYER
		if fx["home"]:
			var cost := club.cost(ClubState.PITCH_HIRE) + club.cost(ClubState.REFEREE_FEE) + club.cost(ClubState.KIT_WASHING)
			var est := mini(club.fans, club.seats()) * club.ticket_price() + club.fans * club.econ("spend") + subs - cost
			b.add_child(_coming("stadium", "Next: %s (home)" % opp, "about %s (pitch, ref, kit −£%d)" % [_pounds(est, true), cost], Kit.c("ok")))
		else:
			var cost2 := club.cost(ClubState.KIT_WASHING) + club.cost(ClubState.TRAVEL)
			b.add_child(_coming("stadium", "Next: %s (away)" % opp, "about %s (subs in, kit and travel −£%d)" % [_pounds(subs - cost2, true), cost2], Kit.c("ok")))
	var pfc: Dictionary = club.playoff_fixture() if lg.season_over() else {}
	if not pfc.is_empty():
		b.add_child(_coming("stadium", "%s, %s leg: %s (%s)" % [ClubState.round_name(pfc["round"], pfc["tie"]),
			"1st" if int(pfc["leg"]) == 0 else "2nd", pfc["opponent"]["name"], "home" if pfc["home"] else "away"], "week %d" % lg.current_week(), Kit.c("ok")))
	if PyramidScript.has_promotion(club.division()):
		var need := club.seats_needed_up()
		var ok := club.seats() >= need
		b.add_child(_coming("seat" if ok else "warn", "Promotion needs %d seats" % need,
			"we have %d%s" % [club.seats(), "" if ok else " — we can't go up yet"], Kit.c("ok") if ok else Kit.c("danger")))
	if club.prize_paid_season < lg.season:
		b.add_child(_coming("cash", "Prize money", "%s at the end of the season" % _pounds(club.econ("prize"), true), Kit.c("ok")))
	b.add_child(_coming("warn", "Next season, week 1", "League fee −%s · sponsor +%s" % [_pounds(club.cost(ClubState.LEAGUE_FEE)), _pounds(club.econ("sponsor"))], Kit.c("danger")))
	b.add_child(Kit.label("Nan says the urn needs replacing. Not yet, Nan.", true, 19, 400, Kit.c("note_muted"), true))
	Kit.tape(n["root"], Vector2(130, -14), -3)
	_at(n["root"], 44, 160, 360, true)


func _coming(ic: String, title: String, sub: String, col: Color) -> Control:
	var h := _hbox(12)
	var i := Kit.icon(ic, 20, col)
	i.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	h.add_child(i)
	var v := _vbox(0)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_child(Kit.label(title, false, 16, 600, Kit.c("note_ink"), true))
	v.add_child(Kit.label(sub, false, 15, 500, Kit.c("note_muted"), true))
	h.add_child(v)
	return h


## Cash per week this season: a pen line with dots where you built something.
class CashChart extends Control:
	var points: Array = []      # [Vector2(week, cash)]
	var marks: Array = []       # [[week, label]]
	var weeks := 42

	func _draw() -> void:
		var pad := Vector2(30, 24)
		var w := size.x - pad.x * 2.0
		var h := size.y - pad.y * 2.0
		var ink := Kit.c("ink")
		var hi := 10.0
		var lo := 0.0
		for p in points:
			hi = maxf(hi, p.y)
			lo = minf(lo, p.y)
		hi *= 1.15
		var to_px := func(p: Vector2) -> Vector2:
			return Vector2(pad.x + w * p.x / weeks, pad.y + h * (1.0 - (p.y - lo) / maxf(1.0, hi - lo)))
		for g in [0.25, 0.5, 0.75]:
			var y: float = pad.y + h * (1.0 - g)
			draw_line(Vector2(pad.x, y), Vector2(pad.x + w, y), Kit.c("lines"), 1.0)
		draw_line(Vector2(pad.x, pad.y + h), Vector2(pad.x + w, pad.y + h), ink, 2.0, true)
		var f := Kit.font(false, 500)
		for wk in [1, 10, 20, 30, weeks]:
			var x: float = pad.x + w * wk / weeks
			draw_string(f, Vector2(x - 8, size.y - 2), str(wk), HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Kit.c("muted"))
		if points.is_empty():
			return
		# a step line: cash holds until the next booking
		var line := PackedVector2Array()
		var prev: Vector2 = points[0]
		line.append(to_px.call(prev))
		for i in range(1, points.size()):
			var p: Vector2 = points[i]
			line.append(to_px.call(Vector2(p.x, prev.y)))
			line.append(to_px.call(p))
			prev = p
		draw_polyline(line, Kit.c("primary"), 3.5, true)
		var hand := Kit.font(true, 400)
		for m in marks:
			var cash_at := 0.0
			for p in points:
				if p.x <= m[0]:
					cash_at = p.y
			var q: Vector2 = to_px.call(Vector2(m[0], cash_at))
			draw_circle(q, 5.0, Kit.c("danger"))
			draw_string(hand, q + Vector2(8, 20), m[1], HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Kit.c("pen"))
		var last: Vector2 = to_px.call(points[-1])
		draw_circle(last, 7.0, Kit.c("primary"))
		draw_dashed_line(last, Vector2(pad.x + w, last.y), Kit.c("muted"), 2.0, 6.0)
		draw_string(Kit.font(false, 700), last + Vector2(12, -8), Hub._pounds(points[-1].y), HORIZONTAL_ALIGNMENT_LEFT, -1, 18, ink)


func _squad_row(cells: Array, widths: Array, head := false) -> Control:
	var wrap := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0)
	sb.border_width_bottom = 1
	sb.border_color = Kit.c("tag_border")
	sb.content_margin_left = 16
	sb.content_margin_right = 16
	wrap.add_theme_stylebox_override("panel", sb)
	wrap.custom_minimum_size = Vector2(0, 34 if head else 42)
	var h := _hbox(14)
	for i in cells.size():
		var l: Label
		if head:
			l = Kit.caps(cells[i], Kit.c("muted"))
		elif i == 3:
			l = Kit.label(cells[i], true, 19, 400, Kit.c("pen"))
		elif i == 4:
			l = Kit.label(cells[i], false, 15, 600, Kit.c("ok"))
		elif i == 1:
			l = Kit.label(cells[i], false, 14, 700, Kit.c("ink"))
		else:
			l = Kit.label(cells[i], false, 17 if i == 2 else 15, 600, Kit.c("ink") if i == 2 and cells[i] != "—" else Kit.c("muted"))
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		var w: int = widths[i]
		if w == 0:
			l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			l.clip_text = true
		else:
			l.custom_minimum_size = Vector2(w, 0)
		h.add_child(l)
	wrap.add_child(h)
	return wrap


# ------------------------------------------------------------------ dev cheats (F1)

func _cheats() -> void:
	var s := Kit.sheet("plain_card", 360, 0.6, Vector4(20, 22, 20, 18), 8)
	var b: VBoxContainer = s["body"]
	b.add_child(_spread(Kit.heading("Dev cheats", 30), Kit.label("F1 to hide", false, 14, 500, Kit.c("muted"))))
	_cheat(b, "+ £10,000", func() -> void: club.money += 10000)
	_cheat(b, "+ 100 fans", func() -> void: club.fans += 100)
	_cheat(b, "Finish all construction now", func() -> void:
		for bd in club.builds:
			bd["finish"] = club.now()
		club.complete_builds()
		main.grounds.rebuild_furniture())
	_cheat(b, "Construction +1 week", func() -> void:
		for bd in club.builds:
			bd["finish"] = float(bd["finish"]) - 1.0
		club.complete_builds()
		main.grounds.rebuild_furniture())
	var cr := _hbox(6)
	_cheat(cr, "Weather: %s" % club.temperature, func() -> void:
		club.temperature = {"mild": "cold", "cold": "sunny", "sunny": "mild"}[club.temperature])
	_cheat(cr, "Max stadium", func() -> void:
		main.cheat_max_stadium())
	_cheat(cr, "Sell out", func() -> void:
		club.fans = club.seats() + 1200)
	b.add_child(cr)
	_cheat(b, "Squad full (11)", func() -> void:
		while club.squad.size() < ClubState.SQUAD_SIZE:
			club.recruit(0))
	var ap := _hbox(6)
	_cheat(ap, "Approval 100%", func() -> void: club.approval = 100.0)
	_cheat(ap, "Approval 0%", func() -> void: club.approval = 0.0)
	b.add_child(ap)
	if not club.league.season_over():
		var row := _hbox(6)
		for r in [["Win 3-0", 3, 0], ["Draw 1-1", 1, 1], ["Lose 0-3", 0, 3]]:
			var gf: int = r[1]
			var ga: int = r[2]
			var cb := Kit.link(r[0], "", false, 40)
			cb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			cb.pressed.connect(func() -> void: main.cheat_result(gf, ga))
			row.add_child(cb)
		b.add_child(row)
	var row2 := _hbox(6)
	var va := Kit.link("View next away ground" if away_viewing == "" else "Next (%s)" % away_viewing, "", false, 40)
	va.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	va.clip_text = true
	va.pressed.connect(func() -> void:
		away_viewing = main.cheat_view_away()
		refresh())
	row2.add_child(va)
	if away_viewing != "":
		var vh := Kit.link("My ground", "", false, 40)
		vh.pressed.connect(func() -> void:
			away_viewing = ""
			main.cheat_view_home()
			refresh())
		row2.add_child(vh)
	b.add_child(row2)
	var wipe := Kit.link("Sure? Click again" if wipe_armed else "New game (wipes the save)", "demolish", false, 40)
	wipe.pressed.connect(_on_wipe)
	b.add_child(wipe)
	b.add_child(Kit.label("In a match: F2 ends it now, F3 goal for you, F4 goal for them, F5 free camera. Anywhere: ` (key left of 1) fps counter, Shift+` vsync on/off.", false, 13, 500, Kit.c("muted"), true))
	Kit.tape(s["root"], Vector2(130, -14), 3, 96, true)
	_at(s["root"], 500, 146, 360)


func _cheat(parent: Control, text: String, f: Callable) -> void:
	var b := Kit.link(text, "", false, 40)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.pressed.connect(func() -> void:
		f.call()
		club.save()
		refresh())
	parent.add_child(b)


func _on_wipe() -> void:
	if not wipe_armed:
		wipe_armed = true
		refresh()
		return
	wipe_armed = false
	main.new_game()
	club.save()


# ------------------------------------------------------------------ helpers

static func _wk(w: float) -> String:
	if is_equal_approx(w, round(w)):
		return str(int(w))
	if is_equal_approx(w * 2.0, round(w * 2.0)):
		return "%.1f" % w
	return "%.2f" % w


static func _ordinal(n: int) -> String:
	if n <= 0:
		return "—"
	var suf := "th"
	if n % 100 < 11 or n % 100 > 13:
		suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
	return "%d%s" % [n, suf]


static func _money(v: int) -> String:
	if absi(v) >= 1000000:     # Marcel: shorten around a million
		return ("-" if v < 0 else "") + ("%.1fm" % (absi(v) / 1000000.0)).replace(".0m", "m")
	var s := str(absi(v))
	var out := ""
	while s.length() > 3:
		out = "," + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return ("-" if v < 0 else "") + s + out



## "£1,234", "-£15", "+£1.70", "£1.2m" — sign shown for money out, and for money in when `plus`.
static func _pounds(v: float, plus := false) -> String:
	var a := absf(v)
	var body := ""
	if a >= 1000000.0:
		body = _money(int(round(a)))
	elif absf(a - round(a)) > 0.004:
		body = "%.2f" % a
	else:
		body = _money(int(round(a)))
	return ("-" if v < -0.004 else ("+" if plus and v > 0.004 else "")) + "£" + body


# ================================================================== main menu

func _menu() -> void:
	var title := Kit.sheet("paper", 840, -0.8, Vector4(40, 34, 40, 30), 6)
	var tb: VBoxContainer = title["body"]
	var h := Kit.label("Sunday League", true, 104, 700, Kit.c("ink"))
	h.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tb.add_child(h)
	var sub := Kit.label("From a field and some chairs to the very top.", true, 26, 400, Kit.c("pen"))
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tb.add_child(sub)
	Kit.tape(title["root"], Vector2(80, -14), -6, 120)
	Kit.tape(title["root"], Vector2(640, -14), 5, 120)
	board.add_child(title["root"])
	title["root"].anchor_left = 0.5
	title["root"].anchor_right = 0.5
	title["root"].offset_left = -420
	title["root"].offset_right = 420
	title["root"].offset_top = 150

	var m := Kit.sheet("plain_card", 560, 0.6, Vector4(30, 30, 30, 28), 14)
	var mb: VBoxContainer = m["body"]
	var has_save := FileAccess.file_exists(ClubState.SAVE_PATH)
	if has_save:
		var lg: LeagueScript = club.league
		var cont := Kit.primary("Continue", "play", 72, 22)
		cont.alignment = HORIZONTAL_ALIGNMENT_LEFT
		cont.text = "Continue\n%s · Season %d · Week %d · %d seats" % [ClubState.CLUB_NAME, lg.season, lg.current_week(), club.seats()]
		cont.pressed.connect(func() -> void:
			screen = "hub"
			refresh())
		mb.add_child(cont)
	var nw := Kit.link("Sure? This wipes your club — click again" if menu_new_armed else "Start a new club", "plus", false, 56)
	nw.alignment = HORIZONTAL_ALIGNMENT_LEFT
	nw.add_theme_font_size_override("font_size", 19)
	nw.pressed.connect(func() -> void:
		if has_save and not menu_new_armed:
			menu_new_armed = true
			refresh()
			return
		menu_new_armed = false
		main.new_game()
		club.save()
		screen = "hub"
		tab = "Club"
		refresh())
	mb.add_child(nw)
	var st := Kit.link("Settings", "settings", false, 56)
	st.alignment = HORIZONTAL_ALIGNMENT_LEFT
	st.add_theme_font_size_override("font_size", 19)
	st.pressed.connect(func() -> void:
		settings_open = true
		refresh())
	mb.add_child(st)
	var q := Kit.link("Quit", "quit", false, 56)
	q.alignment = HORIZONTAL_ALIGNMENT_LEFT
	q.add_theme_font_size_override("font_size", 19)
	q.pressed.connect(func() -> void:
		club.save()
		main.get_tree().quit())
	mb.add_child(q)
	Kit.pin(m["root"], 280)
	board.add_child(m["root"])
	m["root"].anchor_left = 0.5
	m["root"].anchor_right = 0.5
	m["root"].offset_left = -280
	m["root"].offset_right = 280
	m["root"].offset_top = 430

	var n := Kit.sheet("note", 320, 2.5, Vector4(22, 26, 22, 22), 6)
	(n["body"] as VBoxContainer).add_child(Kit.caps("Club news", Kit.c("note_muted")))
	(n["body"] as VBoxContainer).add_child(Kit.label("The kettle's fixed. Training resumes Weds 7pm.", true, 21, 400, Kit.c("note_ink"), true))
	Kit.tape(n["root"], Vector2(110, -14), -4)
	_at(n["root"], 200, 470, 320, true)

	var v := PanelContainer.new()
	var vs := Kit.box(Kit.c("paper"), 3, false)
	vs.content_margin_left = 10
	vs.content_margin_right = 10
	vs.content_margin_top = 6
	vs.content_margin_bottom = 6
	v.add_theme_stylebox_override("panel", vs)
	v.add_child(Kit.label("v0.1", false, 14, 500, Kit.c("muted")))
	board.add_child(v)
	v.anchor_top = 1.0
	v.anchor_bottom = 1.0
	v.grow_vertical = Control.GROW_DIRECTION_BEGIN
	v.offset_left = 32
	v.offset_bottom = -24


# ================================================================== settings (modal)

func _settings() -> void:
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.45)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	board.add_child(dim)
	var s := Kit.sheet("plain_card", 760, 0.0, Vector4(34, 28, 34, 28), 18)
	var b: VBoxContainer = s["body"]
	var close := Kit.icon_button("close", "Close settings")
	close.pressed.connect(_close_settings)
	b.add_child(_spread(Kit.heading("Settings", 42), close))
	b.add_child(Kit.caps("Sound"))
	var sound := _hbox(24)
	sound.add_child(_slider_box("Music", SettingsScript.music, func(v: float) -> void:
		SettingsScript.music = int(v)
		SettingsScript.apply_audio()))
	sound.add_child(_slider_box("Effects", SettingsScript.effects, func(v: float) -> void:
		SettingsScript.effects = int(v)
		SettingsScript.apply_audio()))
	sound.add_child(_slider_box("Crowd", SettingsScript.crowd, func(v: float) -> void:
		SettingsScript.crowd = int(v)
		SettingsScript.apply_audio()))
	b.add_child(sound)
	b.add_child(Kit.rule(Kit.c("tag_border"), 1))
	b.add_child(Kit.caps("Match"))
	var step := _hbox(10)
	var minus := Kit.icon_button("minus", "Shorter")
	var val := Kit.label("%d min per half" % SettingsScript.half_minutes, false, 18, 700, Kit.c("ink"))
	val.custom_minimum_size = Vector2(150, 0)
	val.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	val.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var plus := Kit.icon_button("plus", "Longer")
	minus.pressed.connect(func() -> void:
		SettingsScript.half_minutes = maxi(1, SettingsScript.half_minutes - 1)
		val.text = "%d min per half" % SettingsScript.half_minutes)
	plus.pressed.connect(func() -> void:
		SettingsScript.half_minutes = mini(10, SettingsScript.half_minutes + 1)
		val.text = "%d min per half" % SettingsScript.half_minutes)
	step.add_child(minus)
	step.add_child(val)
	step.add_child(plus)
	b.add_child(_spread(Kit.label("Match length", false, 16, 600, Kit.c("ink")), step))
	b.add_child(Kit.rule(Kit.c("tag_border"), 1))
	b.add_child(Kit.caps("Camera & look"))
	b.add_child(_slider_box("Camera speed", SettingsScript.camera_speed, func(v: float) -> void:
		SettingsScript.camera_speed = int(v)))
	var seg := Kit.segmented(["Light", "Dark"], "Dark" if SettingsScript.dark else "Light", func(o: String) -> void:
		SettingsScript.dark = o == "Dark"
		Kit.dark = SettingsScript.dark
		SettingsScript.save()
		main.rebuild_hud()
		refresh())
	seg.custom_minimum_size = Vector2(320, 0)
	b.add_child(_spread(Kit.label("Appearance", false, 16, 600, Kit.c("ink")), seg))
	var done := Kit.primary("Done", "check")
	done.size_flags_horizontal = Control.SIZE_SHRINK_END
	done.custom_minimum_size = Vector2(180, 56)
	done.pressed.connect(_close_settings)
	b.add_child(done)
	Kit.pin(s["root"], 380)
	board.add_child(s["root"])
	s["root"].anchor_left = 0.5
	s["root"].anchor_right = 0.5
	s["root"].offset_left = -380
	s["root"].offset_right = 380
	s["root"].offset_top = 120
	var n := Kit.sheet("note", 300, 3.0, Vector4(20, 24, 20, 20), 4)
	(n["body"] as VBoxContainer).add_child(Kit.label("Turning the crowd down won't make them any nicer.", true, 20, 400, Kit.c("note_ink"), true))
	Kit.tape(n["root"], Vector2(100, -14), -5)
	board.add_child(n["root"])
	n["root"].anchor_left = 0.5
	n["root"].anchor_right = 0.5
	n["root"].offset_left = 400
	n["root"].offset_right = 700
	n["root"].offset_top = 640


func _slider_box(lab: String, value: int, on_change: Callable) -> VBoxContainer:
	var v := _vbox(6)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var num := Kit.label("%d%%" % value, false, 16, 700, Kit.c("ink"))
	v.add_child(_spread(Kit.label(lab, false, 16, 600, Kit.c("ink")), num))
	var sl := Kit.slider(value)
	sl.value_changed.connect(func(x: float) -> void:
		num.text = "%d%%" % int(x)
		on_change.call(x))
	v.add_child(sl)
	return v


func _close_settings() -> void:
	settings_open = false
	SettingsScript.save()
	refresh()


# ================================================================== build preview (beside the hovered spot)

static func _side_name(sec: int) -> String:
	var L := ClubState.SECTIONS_LONG
	var S := ClubState.SECTIONS_SHORT
	# Marcel (2026-11-08): the camera side is the main side, "West"; opposite "East"; the ends North and South
	if sec < L:
		return "East side · Section %d" % (sec + 1)
	if sec < 2 * L:
		return "West side · Section %d" % (sec - L + 1)
	if sec < 2 * L + S:
		return "North end · Section %d" % (sec - 2 * L + 1)
	return "South end · Section %d" % (sec - 2 * L - S + 1)


## Called by main every hub frame while placing. idx = hovered spot/section (-1 = none).
func update_preview(item: String, idx: int, screen_pos: Vector2) -> void:
	if item == "" or idx < 0 or screen != "hub":
		_prev_key = ""
		for ch in overlay.get_children():
			ch.queue_free()
		return
	var key := "%s:%d:%d" % [item, idx, club.money]
	if key != _prev_key:
		_prev_key = key
		for ch in overlay.get_children():
			ch.queue_free()
		overlay.add_child(_preview_card(item, idx))
	if overlay.get_child_count() > 0:
		var card: Control = overlay.get_child(overlay.get_child_count() - 1)
		var p := screen_pos / overlay.scale.x + Vector2(60, -120)
		p.x = clampf(p.x, 500.0, overlay.size.x - 440.0)
		p.y = clampf(p.y, 130.0, overlay.size.y - 560.0)
		card.position = p


func _preview_card(item: String, idx: int) -> Control:
	if item == "hardcore":
		return _hardcore_card(idx)
	var sec_item := item in ClubState.SECTION_ITEMS
	var names := {"chair": "Chair", "bench": "Bench"}
	if sec_item:
		var st0 := ClubState.item_stage(item)
		var nm := "More rows" if st0 == "rows" else String(ClubState.STAGES[st0]["name"])
		if st0 == "rows" and club.stage_of(idx) != "":
			nm = "%s to %d rows" % [ClubState.STAGES[club.stage_of(idx)]["name"], club.next_rows(item, idx)]
		names[item] = nm + (" (rush)" if item.ends_with("_rush") else "")
	var s := Kit.sheet("plain_card", 400, 0.6, Vector4(24, 24, 24, 20), 12)
	var b: VBoxContainer = s["body"]
	b.add_child(Kit.heading(names.get(item, item), 34))
	var where := _side_name(idx) if sec_item else "%s · Spot %d" % [_side_name(idx / ClubState.SPOTS_PER_SECTION), idx % ClubState.SPOTS_PER_SECTION + 1]
	b.add_child(Kit.label(where, false, 16, 500, Kit.c("muted")))
	var price := club.build_cost(item, idx) if sec_item else club.price_of(item)
	b.add_child(Kit.caps("Cost", Kit.c("muted")))
	b.add_child(_line("Price", "£%s" % _money(price)))
	b.add_child(Kit.rule())
	b.add_child(_line("You pay", "£%s" % _money(price), null, true))
	var after := club.money - price
	b.add_child(_line("Cash after", ("-£%s" % _money(-after)) if after < 0 else "£%s" % _money(after), Kit.c("danger") if after < 0 else null))
	b.add_child(Kit.caps("Adds", Kit.c("muted")))
	var add_seats := 1
	var mult := 1.0
	var lost := 0
	if item == "bench":
		add_seats = ClubState.BENCH_SEATS
	elif sec_item:
		var st1 := ClubState.item_stage(item)
		var stage := club.stage_of(idx) if st1 == "rows" else st1
		if stage == "":
			stage = "bleachers"
		lost = club.section_seats(idx)
		for k in ClubState.SPOTS_PER_SECTION:
			lost += club.seats_in(str(idx * ClubState.SPOTS_PER_SECTION + k)) if st1 != "rows" else 0
		add_seats = ClubState.stand_seats(stage, club.next_rows(item, idx), idx) - lost
		mult = float(ClubState.STAGES[stage]["ticket"])
	var after_seats := club.seats() + add_seats
	b.add_child(_adds("seat", "%+d seat%s (%d → %d)" % [add_seats, "" if absi(add_seats) == 1 else "s", club.seats(), after_seats]))
	b.add_child(_adds("cash", "%s per home match when filled%s" % [_pounds((add_seats + lost) * club.ticket_price() * mult, true),
		"" if mult == 1.0 else " (covered: +%d%%)" % int(round((mult - 1.0) * 100))]))
	if sec_item and ClubState.item_stage(item) == "main" and idx == ClubState.TUNNEL_SECTION:
		b.add_child(_adds("info", "Players' tunnel here: the first %d rows make way for it" % ClubState.TUNNEL_ROWS, Kit.c("ink")))
	if sec_item:
		var w := club.build_weeks(item, idx)
		var ready := club.ready_label({"finish": club.now() + w})
		b.add_child(_adds("clock", "Ready in %s wk · %s" % [_wk(w), ready], Kit.c("ink")))
		if ClubState.item_stage(item) != "rows" and (club._section_has_furniture(idx) or club.stage_of(idx) != ""):
			var what := "the chairs/benches" if club.stage_of(idx) == "" else "the " + String(ClubState.STAGES[club.stage_of(idx)]["name"]).to_lower()
			b.add_child(_adds("demolish", "Demolishes %s here (+%d wk)" % [what, int(ClubState.DEMOLITION_WEEKS)], Kit.c("danger")))
		b.add_child(Kit.label("The section is closed while it's being built.", true, 19, 400, Kit.c("pen"), true))
	else:
		b.add_child(_adds("clock", "Ready instantly", Kit.c("ink")))
		b.add_child(Kit.label("Stack up to 4 per spot. They don't match. Nobody minds." if item == "chair" else "Seats four. Five if you're friendly.",
			true, 19, 400, Kit.c("pen"), true))
	b.add_child(Kit.label("Left click to build · right click or Esc to cancel", false, 14, 500, Kit.c("muted")))
	Kit.pin(s["root"], 200)
	return s["root"]


func _hardcore_card(idx: int) -> Control:
	var on := club.is_hardcore(idx)
	var s := Kit.sheet("plain_card", 400, 0.6, Vector4(24, 24, 24, 20), 12)
	var b: VBoxContainer = s["body"]
	b.add_child(Kit.heading("Hard core", 34))
	b.add_child(Kit.label(_side_name(idx), false, 16, 500, Kit.c("muted")))
	b.add_child(_line("Now", "Hard core" if on else "Regular", Kit.c("ok") if on else null))
	b.add_child(_adds("fans", "Click to make it %s" % ("a regular section" if on else "hard core"), Kit.c("ink")))
	b.add_child(Kit.label("More club colours, scarves and flags; a lot of them stand. Free, and you can switch it back any time.",
		true, 19, 400, Kit.c("pen"), true))
	b.add_child(Kit.label("Left click to switch · right click or Esc to stop", false, 14, 500, Kit.c("muted")))
	Kit.pin(s["root"], 200)
	return s["root"]


func _line(lab: String, val: String, col = null, big := false) -> Control:
	return _spread(Kit.label(lab, false, 16, 500, Kit.c("muted")),
		Kit.label(val, false, 22 if big else 17, 700 if big else 600, Kit.c("ink") if col == null else col))


func _adds(ic: String, text: String, col = null) -> Control:
	var h := _hbox(10)
	var c: Color = Kit.c("ok") if col == null else col
	h.add_child(Kit.icon(ic, 20, c))
	var l := Kit.label(text, false, 16, 600, c, true)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(l)
	return h


# ================================================================== formation sketch (Squad tab)

class Formation extends Control:
	const SPOTS := [["GK", 50, 90], ["LB", 14, 70], ["CB", 37, 74], ["CB", 63, 74], ["RB", 86, 70], ["CM", 28, 48],
		["CDM", 50, 56], ["CM", 72, 48], ["LW", 16, 22], ["ST", 50, 15], ["RW", 84, 22]]
	var pen := Color.BLACK
	var ink := Color.BLACK
	var card := Color.WHITE
	var font: Font
	var filled := 11

	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		var faint := Color(pen.r, pen.g, pen.b, 0.6)
		draw_rect(r, pen, false, 2.0)
		draw_line(Vector2(0, size.y * 0.5), Vector2(size.x, size.y * 0.5), faint, 2.0)
		draw_arc(size * 0.5, 45.0, 0, TAU, 40, faint, 2.0)
		draw_rect(Rect2(size.x * 0.25, size.y - 70, size.x * 0.5, 70), faint, false, 2.0)
		draw_rect(Rect2(size.x * 0.25, 0, size.x * 0.5, 70), faint, false, 2.0)
		for i in SPOTS.size():
			var sp: Array = SPOTS[i]
			var c := Vector2(size.x * sp[1] / 100.0, size.y * sp[2] / 100.0)
			draw_circle(c, 20.0, card if i < filled else Color(card.r, card.g, card.b, 0.5))
			draw_arc(c, 20.0, 0, TAU, 32, ink if i < filled else Color(ink.r, ink.g, ink.b, 0.35), 2.0)
			var t: String = sp[0]
			var w := font.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, 13).x
			draw_string(font, c + Vector2(-w * 0.5, 5), t, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, ink)


func _formation_card() -> void:
	var s := Kit.sheet("plain_card", 420, -0.8, Vector4(22, 24, 22, 22), 14)
	var b: VBoxContainer = s["body"]
	b.add_child(_spread(Kit.heading("Formation", 34), Kit.caps("4-3-3")))
	var f := Formation.new()
	f.pen = Kit.c("pen")
	f.ink = Kit.c("ink")
	f.card = Kit.c("card")
	f.font = Kit.font(false, 700)
	f.filled = club.squad.size()
	f.custom_minimum_size = Vector2(0, 470)
	f.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(f)
	b.add_child(Kit.label("Drawn by the gaffer on a beer mat. Copied out neatly.", true, 19, 400, Kit.c("muted"), true))
	Kit.tape(s["root"], Vector2(160, -14), 3)
	_at(s["root"], 40, 150, 420)


# ================================================================== post-match summary

var summary_root: Control         # own scaled layer over everything


func _build_summary() -> void:
	summary_root = Control.new()
	summary_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	summary_root.visible = false
	add_child(summary_root)
	get_viewport().size_changed.connect(_fit_summary)
	_fit_summary()


func _fit_summary() -> void:
	var vp := get_viewport().get_visible_rect().size
	var sc := minf(vp.x / Kit.DESIGN.x, vp.y / Kit.DESIGN.y)
	summary_root.scale = Vector2(sc, sc)
	summary_root.size = vp / sc


func show_summary(s: Dictionary, opponent: String) -> void:
	last_seated = s["seated"]
	_ticker_i += 1
	for ch in summary_root.get_children():
		ch.queue_free()
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.35)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	summary_root.add_child(dim)
	var home: bool = s.get("home", true)
	var gf: int = s["goals_for"]
	var ga: int = s["goals_against"]
	var us := ClubState.CLUB_NAME

	var card := Kit.sheet("card", 1120, 0.4, Vector4(36, 30, 36, 30), 22)
	var b: VBoxContainer = card["body"]
	var res := {"W": "Full time — a win!", "D": "Full time — a draw", "L": "Full time — a loss"}
	var tag := "League · now %s" % _ordinal(int(s["position"])) if s.has("position") else "Friendly"
	if s.get("season_over", false) and not s.has("playoff"):
		tag += " · season over"
	var po: Dictionary = s.get("playoff", {})
	if not po.is_empty():
		tag = "%s · %s leg" % [po["title"], "1st" if int(po["leg"]) == 1 else "2nd"]
	b.add_child(_spread(Kit.heading(res[s["result"]], 44), Kit.caps(tag)))
	# score line: home team on the left
	var line := _hbox(28)
	line.alignment = BoxContainer.ALIGNMENT_CENTER
	var l_name := us if home else opponent
	var r_name := opponent if home else us
	var lh := _hbox(16)
	lh.alignment = BoxContainer.ALIGNMENT_END
	lh.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var ln := Kit.label(l_name, false, 24, 700, Kit.c("ink"))
	ln.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	lh.add_child(ln)
	lh.add_child(Kit.icon("crest_home" if home else "crest_away", 60, Kit.c("pen") if home else Kit.c("ink")))
	line.add_child(lh)
	line.add_child(Kit.label("%d – %d" % [gf if home else ga, ga if home else gf], false, 64, 700, Kit.c("ink")))
	var rh := _hbox(16)
	rh.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rh.add_child(Kit.icon("crest_away" if home else "crest_home", 60, Kit.c("ink") if home else Kit.c("pen")))
	var rn := Kit.label(r_name, false, 24, 700, Kit.c("ink"))
	rn.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	rh.add_child(rn)
	line.add_child(rh)
	b.add_child(line)
	if not po.is_empty():
		var pl := Kit.label(po["line"], true, 26, 700, Kit.c("pen") if po.get("won", true) else Kit.c("danger"), true)
		pl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		b.add_child(pl)
	b.add_child(Kit.rule())

	var cols := _hbox(40)
	# attendance
	var att := _sum_col("Attendance", "fans")
	if home:
		att.add_child(_sum_row("Seated (paying)", str(s["seated"])))
		att.add_child(_sum_row("Standing (free)", str(s["standing"])))
		att.add_child(_sum_row("Total", str(s["attendance"]), null, true))
		var pct: float = 100.0 * s["seated"] / maxf(1.0, s["attendance"])
		att.add_child(Kit.progress(pct, false))
		att.add_child(Kit.label("Every seat was taken." if s["standing"] > 0 and s["seated"] > 0 else
			("Nobody had a seat." if s["seated"] == 0 else "Room to spare."), false, 14, 500, Kit.c("muted")))
	else:
		att.add_child(_sum_row("Our travelling fans", str(int(round(club.fans * Main.AWAY_TRAVEL_SHARE)))))
		att.add_child(Kit.label("Away match: their ground, their turnstiles.", false, 14, 500, Kit.c("muted"), true))
	cols.add_child(att)
	# money
	var mon := _sum_col("Money", "cash")
	var lines: Dictionary = s.get("lines", {})
	var costs := 0.0
	var cost_names := []
	for k in lines:
		var v := float(lines[k])
		if v >= 0.0:
			var lab: String = k
			if k == "Tickets":
				lab = "Tickets (%d × %s)" % [s["seated"], _pounds(float(lines[k]) / int(s["seated"]) if int(s["seated"]) > 0 else club.ticket_price())]
			mon.add_child(_sum_row(lab, _pounds(v, true), Kit.c("ok")))
		else:
			costs += v
			cost_names.append(String(k).to_lower())
	if costs < 0.0:
		mon.add_child(_sum_row("Costs (%s)" % ", ".join(cost_names), _pounds(costs), Kit.c("danger")))
	var net := float(s.get("money_in", 0.0)) + float(s.get("money_out", 0.0))
	mon.add_child(_sum_row("This match", _pounds(net, true), Kit.c("ok") if net >= 0.0 else Kit.c("danger")))
	mon.add_child(_sum_row("Cash now", "£%s" % _money(club.money), null, true))
	cols.add_child(mon)
	# fans & approval
	var fa := _sum_col("Fans", "approval")
	var dfans: int = s["fans_after"] - s["fans_before"]
	fa.add_child(_sum_row("Fans", "%d → %d  (%+d)" % [s["fans_before"], s["fans_after"], dfans], Kit.c("ok") if dfans >= 0 else Kit.c("danger")))
	var a0 := int(round(s["approval_before"]))
	var a1 := int(round(s["approval_after"]))
	fa.add_child(_sum_row("Fan approval", "%d%% → %d%%  (%+d)" % [a0, a1, a1 - a0], Kit.c("ok") if a1 >= a0 else Kit.c("danger"), true))
	var parts: Dictionary = s["approval_parts"]
	var rname: String = {"W": "win", "D": "draw", "L": "loss"}[s["result"]]
	for p in [["· Result (%s)" % rname, parts["result"]], ["· Entertainment", parts["entertainment"]], ["· Seating", parts["seating"]]]:
		var v: float = snappedf(p[1], 0.1)
		if is_zero_approx(v):
			v = 0.0
		if p[0] == "· Seating" and not home:
			continue
		fa.add_child(_sum_row(p[0], "%+.1f" % v, Kit.c("ok") if v >= 0.0 else Kit.c("danger")))
	cols.add_child(fa)
	b.add_child(cols)
	if s["seated"] >= GOAL_SUPPORTERS:
		b.add_child(Kit.label("★ Goal reached: %d paying supporters! ★" % s["seated"], true, 26, 700, Kit.c("pen")))
	var back := Kit.primary("Back to the club", "club")
	back.size_flags_horizontal = Control.SIZE_SHRINK_END
	back.custom_minimum_size = Vector2(280, 56)
	back.pressed.connect(func() -> void: main.back_to_hub())
	b.add_child(back)
	Kit.pin(card["root"], 224)
	Kit.pin(card["root"], 896)
	summary_root.add_child(card["root"])
	card["root"].anchor_left = 0.5
	card["root"].anchor_right = 0.5
	card["root"].offset_left = -560
	card["root"].offset_right = 560
	card["root"].offset_top = 132

	# elsewhere in the league (sticky note)
	var others: Array = s.get("round_results", [])
	if not others.is_empty():
		var n := Kit.sheet("note", 320, -2.5, Vector4(20, 24, 20, 20), 2)
		var nb: VBoxContainer = n["body"]
		nb.add_child(Kit.caps("Elsewhere today", Kit.c("note_muted")))
		for r in others:
			if str(r).contains(us):
				continue
			nb.add_child(Kit.label(r, true, 16, 400, Kit.c("note_ink"), true))
		Kit.tape(n["root"], Vector2(132, -14), 4)
		summary_root.add_child(n["root"])
		n["root"].position = Vector2(26, 150)
	summary_root.visible = true


func _sum_col(head: String, ic: String) -> VBoxContainer:
	var v := _vbox(6)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var h := _hbox(8)
	h.add_child(Kit.icon(ic, 20, Kit.c("pen")))
	var cl := Kit.caps(head)
	cl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(cl)
	v.add_child(h)
	return v


func _sum_row(lab: String, val: String, col = null, bold := false) -> Control:
	var p := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0)
	sb.border_width_bottom = 1
	sb.border_color = Kit.c("tag_border")
	sb.content_margin_top = 6
	sb.content_margin_bottom = 6
	p.add_theme_stylebox_override("panel", sb)
	p.add_child(_spread(Kit.label(lab, false, 16, 500, Kit.c("muted")),
		Kit.label(val, false, 20 if bold else 17, 700 if bold else 600, Kit.c("ink") if col == null else col)))
	return p


func hide_summary() -> void:
	if summary_root != null:
		summary_root.visible = false
