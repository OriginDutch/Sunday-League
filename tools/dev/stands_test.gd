extends SceneTree
## Headless check of the stand stages: godot --headless -s tools/dev/stands_test.gd

var fails := 0


func check(ok: bool, what: String) -> void:
	print(("  ok   " if ok else "  FAIL ") + what)
	if not ok:
		fails += 1


func finish_all(c: ClubState) -> void:
	for b in c.builds.duplicate():
		b["finish"] = c.now()
	c.complete_builds()


func _init() -> void:
	var c := ClubState.new_game()
	c.money = 1000000
	print("1) The Shed on an empty section")
	check(c.can_build("shed", 0), "can build")
	check(c.build_cost("shed", 0) == 5600, "costs £5,600 (%d)" % c.build_cost("shed", 0))
	check(is_equal_approx(c.build_weeks("shed", 0), 2.0), "2 weeks (%.2f)" % c.build_weeks("shed", 0))
	check(c.place("shed", 0), "placed")
	check(c.section_seats(0) == 0, "closed while building")
	finish_all(c)
	check(c.stage_of(0) == "shed" and c.section_seats(0) == 60, "finished: 3 rows, 60 seats")
	check(not c.can_build("shed", 0), "can't build the same stage again")
	print("2) more rows")
	check(c.next_rows("rows", 0) == 5 and c.build_cost("rows", 0) == 3733, "→ 5 rows for £3,733 (%d)" % c.build_cost("rows", 0))
	check(is_equal_approx(c.build_weeks("rows", 0), 1.0), "1 week")
	c.place("rows", 0)
	finish_all(c)
	c.place("rows", 0)
	finish_all(c)
	check(c.bleacher_rows(0) == 8 and c.section_seats(0) == 160, "8 rows, 160 seats")
	check(not c.can_build("rows", 0), "no more rows after 8")
	print("3) stage jump to the main stand (demolition)")
	check(c.build_cost("main", 0) == 50000, "£50,000 (%d)" % c.build_cost("main", 0))
	check(is_equal_approx(c.build_weeks("main", 0), 5.0), "4 weeks + 1 demolition (%.2f)" % c.build_weeks("main", 0))
	check(is_equal_approx(c.build_weeks("main_rush", 0), 4.0), "rush: 3 + 1 demolition (%.2f)" % c.build_weeks("main_rush", 0))
	check(c.build_cost("main_rush", 0) == 75000, "rush +50%")
	c.place("main", 0)
	check(c.section_seats(0) == 0 and not c.sections.has("0"), "old stand gone while building")
	finish_all(c)
	check(c.stage_of(0) == "main" and c.section_seats(0) == 200, "main stand 10 rows = 200 seats")
	print("4) tunnel section (West middle)")
	c.place("main", ClubState.TUNNEL_SECTION)
	finish_all(c)
	check(c.section_seats(ClubState.TUNNEL_SECTION) == 120, "10 rows minus 4 for the tunnel = 120 (%d)" % c.section_seats(ClubState.TUNNEL_SECTION))
	print("5) skipping stages, bleachers still fine")
	c.place("bleachers", 1)
	finish_all(c)
	check(c.stage_of(1) == "bleachers" and c.section_seats(1) == 60, "bleachers 60")
	check(c.build_cost("rows", 1) == 1200, "bleacher rows still £1,200")
	print("6) covered seats first, dearer tickets")
	var tiers := c.seat_tiers()
	check(tiers[0][0] == 1.5 and tiers[0][1] == 320, "main stand first: 320 seats at 1.5× (%s)" % str(tiers))
	c.fans = 400
	var before := c.money
	var s := c.apply_match(1, 0, 3, true, "Test")
	var tp := c.ticket_price()
	var expect := 320 * tp * 1.5 + 60 * tp
	check(is_equal_approx(float(s["lines"]["Tickets"]), expect), "tickets £%.2f (expected £%.2f)" % [float(s["lines"]["Tickets"]), expect])
	check(float(s["approval_parts"]["seating"]) > 0.0, "approval bonus from covered seats (%.2f)" % float(s["approval_parts"]["seating"]))
	print("7) save / load keeps stages")
	var c2 := ClubState.from_dict(JSON.parse_string(JSON.stringify(c.to_dict())))
	check(c2.stage_of(0) == "main" and c2.seats() == c.seats(), "same stages and seats after load")
	print("FAILS: %d" % fails)
	quit(1 if fails else 0)
