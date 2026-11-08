extends SceneTree
## Headless check of promotion/relegation: godot --headless -s tools/dev/pyramid_test.gd
## Plays whole seasons with fixed scorelines and prints where you end up.

const PyramidScript = preload("res://scripts/pyramid.gd")
var fails := 0


func check(ok: bool, what: String) -> void:
	print(("  ok   " if ok else "  FAIL ") + what)
	if not ok:
		fails += 1


func play_season(c: ClubState, gf: int, ga: int) -> void:
	while not c.league.season_over():
		c.league.play_round(gf, ga)
	c.end_season_money()
	c.on_regular_season_end()


func play_playoffs(c: ClubState, gf: int, ga: int) -> int:
	var legs := 0
	while true:
		var fx := c.playoff_fixture()
		if fx.is_empty():
			break
		c.record_playoff_leg(fx["tie"], gf, ga, gf >= ga)
		legs += 1
		if legs > 10:
			break
	return legs


func sizes_ok(c: ClubState) -> bool:
	for d in c.pyramid.divisions.size():
		var n: int = c.pyramid.divisions[d].size() + (1 if d == c.pyramid.you else 0)
		if n != 20:
			print("    division %d has %d clubs" % [d, n])
			return false
	return true


func _init() -> void:
	seed(7)
	print("1) win everything, 0 seats -> blocked from going up")
	var c := ClubState.new_game()
	check(c.division() == 0 and c.league.teams.size() == 20, "start in %s with 20 clubs" % PyramidScript.NAMES[0])
	play_season(c, 9, 0)
	check(c.league.position_of(0) == 1, "finished 1st")
	check(not c.can_go_up(), "not enough seats (%d < %d)" % [c.seats(), c.seats_needed_up()])
	var r := c.start_next_season()
	check(r["outcome"] == "stayed" and r["denied"], "stayed, denied: %s" % str(r))
	check(sizes_ok(c), "every division has 20 clubs")

	print("2) win everything with 10 seats -> promoted")
	c = ClubState.new_game()
	c.slots["test"] = "chairs:10"
	print("    seats = %d" % c.seats())
	play_season(c, 9, 0)
	check(c.can_go_up(), "enough seats")
	r = c.start_next_season()
	check(r["outcome"] == "promoted" and c.division() == 1, "promoted to %s" % PyramidScript.NAMES[c.division()])
	check(c.league.season == 2 and c.league.teams.size() == 20 and c.league.current_week() == 1, "season 2, week %d" % c.league.current_week())
	check(sizes_ok(c), "every division has 20 clubs")
	check(c.ticket_price() == 3.0, "ticket price now £3")

	print("3) 5th place -> play-offs, win them -> promoted")
	c = ClubState.new_game()
	c.slots["test"] = "chairs:10"
	# 5th-ish: alternate results until position is 3..7
	var w := 0
	while not c.league.season_over():
		var res: Vector2i = [Vector2i(3, 0), Vector2i(1, 1), Vector2i(0, 2), Vector2i(2, 1)][w % 4]
		c.league.play_round(res.x, res.y)
		w += 1
	c.on_regular_season_end()
	var pos := c.league.position_of(0)
	print("    finished %d" % pos)
	if pos >= 3 and pos <= 7:
		check(not c.playoff.is_empty(), "in the play-offs")
		var fx := c.playoff_fixture()
		check(c.league.current_week() >= 43, "play-off week %d" % c.league.current_week())
		print("    first leg: %s vs %s, home=%s" % [ClubState.round_name(fx["round"], fx["tie"]), fx["opponent"]["name"], fx["home"]])
		var legs := play_playoffs(c, 3, 0)
		check(legs >= 4, "played %d legs" % legs)
		r = c.start_next_season()
		check(r["outcome"] == "promoted", "promoted via play-offs: %s" % r["playoff"])
	else:
		print("    (not in 3..7, skipped)")

	print("4) lose everything in division 2 -> relegated")
	c = ClubState.new_game()
	# move you to division 2: one of its clubs takes your place in division 0
	c.pyramid.you = 2
	c.pyramid.divisions[0].append(c.pyramid.divisions[2].pop_front())
	c.league = load("res://scripts/league.gd").create_with(ClubState.CLUB_NAME, c.pyramid.divisions[2])
	check(sizes_ok(c), "setup ok")
	play_season(c, 0, 5)
	check(c.league.position_of(0) == 20, "finished 20th")
	r = c.start_next_season()
	check(r["outcome"] == "relegated" and c.division() == 1, "relegated to %s" % PyramidScript.NAMES[c.division()])
	check(sizes_ok(c), "every division has 20 clubs")

	print("5) save / load mid play-off")
	c = ClubState.new_game()
	c.slots["test"] = "chairs:10"
	play_season(c, 9, 0)
	var fx5 := c.playoff_fixture()
	var c2 := ClubState.from_dict(JSON.parse_string(JSON.stringify(c.to_dict())))
	check(c2.division() == c.division() and c2.playoff.size() == c.playoff.size(), "pyramid + play-off state survive a save")
	var fx6 := c2.playoff_fixture()
	check(fx5.get("tie", "") == fx6.get("tie", "") and fx5.get("leg", -1) == fx6.get("leg", -1), "same next leg after load")
	var r2 := c2.start_next_season()
	check(sizes_ok(c2), "transition after load ok (%s)" % r2["outcome"])

	print("6) 10 seasons in a row, sizes stay right")
	c = ClubState.new_game()
	c.slots["test"] = "chairs:10000"
	for i in 10:
		play_season(c, randi() % 4, randi() % 3)
		play_playoffs(c, 2, 1)
		r = c.start_next_season()
		print("    season %d: %s, finished %d -> %s" % [r["season"], r["outcome"], r["pos"], PyramidScript.NAMES[c.division()]])
		check(sizes_ok(c), "sizes ok")
	print("FAILS: %d" % fails)
	quit(1 if fails else 0)
