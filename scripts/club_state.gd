class_name ClubState
extends RefCounted
const LeagueScript = preload("res://scripts/league.gd")
const PyramidScript = preload("res://scripts/pyramid.gd")
## Everything about your club that persists between matches. Saved as JSON to user://save.json.

const SAVE_PATH := "user://save.json"

# ---- tunable starting values / economy (v0.1) --------------------------------
const START_MONEY := 60
const START_FANS := 5
const START_APPROVAL := 50.0
const START_SQUAD := 4              # you start with a few people and recruit the rest
const SQUAD_SIZE := 11
const CANDIDATES := 8               # size of the "Who can play for you" list
const TICKET_PRICE := 2             # £ per seated fan (fixed in v0.1)
# Bottom-tier money flows (Marcel, 2026-11-08 — tunable; GDD §10b "Finances tab + bottom-tier economy")
const TEA_PER_VISITOR := 1          # tea hut: £ per visitor (seated + standing)
const SUBS_PER_PLAYER := 1          # match subs: every player chips in, home and away
const SPONSOR_PER_SEASON := 50      # paid in week 1
const SPONSOR_NAME := "Dave's Plumbing"
const PRIZE_MONEY := 1.70           # end of the season (one beer)
const PITCH_HIRE := 8               # per home match
const REFEREE_FEE := 5              # per home match
const KIT_WASHING := 2              # per match
const TRAVEL := 3                   # per away match
const LEAGUE_FEE := 30              # per season, week 1
## Money per division (Marcel, 2026-11-08: from the economy model's game column). Per division:
## ticket £ per seated fan, spend £ per visitor (tea hut), sponsor + prize money per season, and a cost
## factor on the bottom-tier costs above (model: ground running + travel/match costs, scaled with income).
const DIV_ECON := [
	{"ticket": 2.0, "spend": 1.0, "sponsor": 50, "prize": 1.70, "costs": 1.0},
	{"ticket": 3.0, "spend": 1.5, "sponsor": 150, "prize": 10.0, "costs": 2.5},
	{"ticket": 3.5, "spend": 2.0, "sponsor": 350, "prize": 25.0, "costs": 4.1},
	{"ticket": 4.5, "spend": 2.5, "sponsor": 700, "prize": 50.0, "costs": 6.4},
	{"ticket": 6.0, "spend": 3.5, "sponsor": 1500, "prize": 100.0, "costs": 13.1},
	{"ticket": 8.0, "spend": 4.5, "sponsor": 3500, "prize": 250.0, "costs": 31.6},
	{"ticket": 11.0, "spend": 5.5, "sponsor": 9000, "prize": 700.0, "costs": 55.5},
	{"ticket": 14.0, "spend": 6.5, "sponsor": 22000, "prize": 2500.0, "costs": 122.5},
	{"ticket": 17.0, "spend": 7.5, "sponsor": 55000, "prize": 15000.0, "costs": 283.0},
	{"ticket": 20.0, "spend": 8.5, "sponsor": 150000, "prize": 60000.0, "costs": 634.6},
	{"ticket": 22.0, "spend": 9.5, "sponsor": 700000, "prize": 450000.0, "costs": 1510.6},
	{"ticket": 26.0, "spend": 11.0, "sponsor": 2000000, "prize": 1500000.0, "costs": 3355.0},
	{"ticket": 32.0, "spend": 13.0, "sponsor": 6000000, "prize": 5000000.0, "costs": 8515.9},
	{"ticket": 48.0, "spend": 16.0, "sponsor": 25000000, "prize": 30000000.0, "costs": 25401.0},
]
## Ledger categories, in display order. New sources/expenses = a new name here + where it's booked.
const INCOME_CATS := ["Tickets", "Tea hut", "Match subs", "Sponsor", "Prize money"]
const EXPENSE_CATS := ["Pitch hire", "Referee", "Kit washing", "Travel", "League fee", "Building"]
const CHAIR_PRICE := 12
const BENCH_PRICE := 40
const BENCH_SEATS := 4
const MAX_CHAIRS_PER_SLOT := 4     # chairs stack up one by one in a spot (a bench's width)
# ground layout (GDD §10a): sections of 11.5 m, 9 per long side, 5 per short side
const SECTION_W := 11.5
const SECTIONS_LONG := 9
const SECTIONS_SHORT := 5
const SPOTS_PER_SECTION := 5        # 5 bench-wide spots of 4 seats = 20 seats in a row
# ---- building (GDD block 4): stages per section, build time in weeks, rush build ------------
# Prices from design/economy (Stand prices tab): open bleachers ≈ £1,800 per 3-row section ≈ £30 a place.
const BLEACHER_ROWS := [3, 5, 7]          # rows per stage step (rows proposal)
const BLEACHER_SEATS_PER_ROW := 20
const BLEACHER_PRICE_PER_PLACE := 30
const BLEACHER_WEEKS := 1.0               # build time per section
const ROW_UPGRADE_WEEKS := 0.5            # extra rows within a stage: half the stage time
const DEMOLITION_WEEKS := 1.0             # stage jump: clear the old furniture first
const RUSH_COST := 1.5                    # rush build: +50% cost...
const RUSH_TIME := 0.75                   # ...for 75% of the build time
## Stand stages per section (GDD §10h2, Marcel 2026-11-08). Prices per place from the economy model;
## rows go up in steps; a covered stage raises the ticket price of its seats and pleases the fans.
const STAGES := {
	"bleachers": {"name": "Open bleachers", "rows": [3, 5, 7], "per_place": 30.0, "weeks": 1.0, "row_weeks": 0.5, "covered": false, "ticket": 1.0},
	"shed": {"name": "The Shed", "rows": [3, 5, 8], "per_place": 5600.0 / 60.0, "weeks": 2.0, "row_weeks": 1.0, "covered": true, "ticket": 1.25},
	"main": {"name": "Main stand", "rows": [10, 12, 15], "per_place": 250.0, "weeks": 4.0, "row_weeks": 2.0, "covered": true, "ticket": 1.5},
}
const STAGE_ORDER := ["bleachers", "shed", "main"]
const TUNNEL_SECTION := 13          # middle of the West side (camera side): players' tunnel when it's a main stand
const TUNNEL_ROWS := 4              # the tunnel section starts above the tunnel over its full width
const COVERED_APPROVAL := 0.5       # a fan under a roof counts 1.5× for the seating part of approval
const SECTION_ITEMS := ["bleachers", "bleachers_rush", "shed", "shed_rush", "main", "main_rush", "rows", "rows_rush", "hardcore"]   # hardcore: free toggle, no build
const SAVE_VERSION := 3             # v2 = sections, v3 = league; older saves start a new game
const CLUB_NAME := "Your club"     # placeholder until the player can name the club

# fan growth per match (multiplied by an approval factor)
const GROWTH_WIN := 6.0
const GROWTH_DRAW := 2.5
const GROWTH_LOSS := 0.5
const GROWTH_PER_SEAT := 0.05       # facilities attract people
# approval change per match
const APPROVAL_WIN := 6.0
const APPROVAL_DRAW := 1.0
const APPROVAL_LOSS := -5.0
const APPROVAL_ENTERTAINMENT_MAX := 6.0
const APPROVAL_NO_SEAT_MAX := -6.0  # if every fan had to stand

var money := START_MONEY
var fans := START_FANS
var approval := START_APPROVAL
var squad: Array = []               # [{name, origin}] in recruitment order
var candidates: Array = []          # "Who can play for you"
var slots: Dictionary = {}          # spot index (String) -> "bench" | "chairs:N"; spot = section * 5 + k
var record := {"w": 0, "d": 0, "l": 0}
var matches_played := 0
var fans_carry := 0.0               # fractional fan growth carried over
var league: LeagueScript                  # your division: fixtures, results, table
var pyramid                         # all 14 divisions (scripts/pyramid.gd); pyramid.you = your division
var season_end := {}                # set when the regular season ends: {season, tables: [rows per division], blocked}
var playoff := {}                   # your play-offs: {div, bracket} (empty when you're not in them)
var last_report := {}               # what happened at the last season change (promoted / relegated / ...)
var sections: Dictionary = {}       # section index (String) -> {"stage": "bleachers", "rows": n}
var builds: Array = []              # [{"sec", "stage", "rows", "finish" (absolute week), "start"}]
## Money ledger: every booking with its lines (category -> £, + in / - out), per match / season / build,
## so the Finances tab can total it any way (and a match can be opened in full later).
var ledger: Array = []              # [{season, week, kind: "match"|"season"|"build", title, lines: {cat: £}, ...}]
var cash_log: Array = []            # [{season, week, cash}] after every booking (cash chart)
var cash_pennies := 0.0             # sub-pound remainder (prize money is £1.70)
var finances_season := 0            # last season whose week-1 money (sponsor, league fee) is booked
var prize_paid_season := 0
## Hard-core sections (Marcel, 2026-11-08): free, as many as you like, purely visual for now —
## flags, scarves, club wear and a share always standing. Keys are section numbers as strings.
var hardcore := {}
## Crowd clothing until weather exists: "cold" / "mild" / "sunny" (dev cheat cycles it).
var temperature := "mild"


static func new_game() -> ClubState:
	var s := ClubState.new()
	for i in START_SQUAD:
		s.squad.append(Names.person())
	s.refill_candidates()
	s.pyramid = PyramidScript.create()
	s.league = LeagueScript.create_with(CLUB_NAME, s.pyramid.divisions[0])
	s.cash_log.append({"season": 1, "week": 0, "cash": s.money})
	s.start_season_money()
	return s


func refill_candidates() -> void:
	while candidates.size() < CANDIDATES:
		candidates.append(Names.person())


func recruit(index: int) -> bool:
	if squad.size() >= SQUAD_SIZE or index < 0 or index >= candidates.size():
		return false
	squad.append(candidates[index])
	candidates.remove_at(index)
	refill_candidates()
	return true


func seats() -> int:
	var n := 0
	for k in slots:
		n += seats_in(str(k))
	for k in sections:
		n += section_seats(int(k))
	return n


func stage_of(sec: int) -> String:
	var k := str(sec)
	return String(sections[k].get("stage", "bleachers")) if sections.has(k) else ""


## Seats in a finished stand section (0 while it's being built).
func section_seats(sec: int) -> int:
	var k := str(sec)
	if not sections.has(k) or is_building(sec):
		return 0
	return stand_seats(stage_of(sec), int(sections[k]["rows"]), sec)


static func stand_seats(stage: String, rows: int, sec: int) -> int:
	if stage == "main" and sec == TUNNEL_SECTION:
		rows -= TUNNEL_ROWS
	return rows * BLEACHER_SEATS_PER_ROW


## Seat capacity per ticket multiplier, best first: [[mult, seats, covered], ...] (covered fills first, Marcel).
func seat_tiers() -> Array:
	var by := {}
	for k in sections:
		var n := section_seats(int(k))
		if n > 0:
			var st: Dictionary = STAGES[stage_of(int(k))]
			var m: float = st["ticket"]
			by[m] = int(by.get(m, 0)) + n
	var plain := 0
	for k in slots:
		plain += seats_in(str(k))
	by[1.0] = int(by.get(1.0, 0)) + plain
	var out := []
	for m in by:
		out.append([float(m), int(by[m]), float(m) > 1.0])
	out.sort_custom(func(a, b): return a[0] > b[0])
	return out


# ------------------------------------------------------------------ time & building

## Absolute week since the start of the career: 52 per year (42 season + 10 off-season).
func now() -> float:
	return float((league.season - 1) * (LeagueScript.SEASON_WEEKS + LeagueScript.OFFSEASON_WEEKS) + league.current_week())


func is_building(sec: int) -> bool:
	for b in builds:
		if int(b["sec"]) == sec:
			return true
	return false


func build_of(sec: int) -> Dictionary:
	for b in builds:
		if int(b["sec"]) == sec:
			return b
	return {}


## Week number (in its season) a build is ready, for the UI.
func ready_label(b: Dictionary) -> String:
	var year := LeagueScript.SEASON_WEEKS + LeagueScript.OFFSEASON_WEEKS
	var f := ceili(float(b["finish"]) - 0.001)
	var season := (f - 1) / year + 1
	var week := (f - 1) % year + 1
	if week > LeagueScript.SEASON_WEEKS:
		return "season %d pre-season" % (season + 1)
	return "season %d week %d" % [season, week]


func _section_has_furniture(sec: int) -> bool:
	for k in SPOTS_PER_SECTION:
		if slots.has(str(sec * SPOTS_PER_SECTION + k)):
			return true
	return false


func bleacher_rows(sec: int) -> int:
	var k := str(sec)
	return int(sections[k]["rows"]) if sections.has(k) else 0


static func item_stage(item: String) -> String:
	return item.trim_suffix("_rush")


## The row count a build would give: a new stage starts at its first step, "rows" goes one step up.
func next_rows(item: String, sec: int) -> int:
	var st := item_stage(item)
	if st == "rows":
		var cur := stage_of(sec)
		if cur == "":
			return 0
		var steps: Array = STAGES[cur]["rows"]
		var i := steps.find(bleacher_rows(sec))
		return int(steps[i + 1]) if i >= 0 and i + 1 < steps.size() else 0
	return int(STAGES[st]["rows"][0]) if STAGES.has(st) else 0


## Section items: a stage ("bleachers", "shed", "main") on a section that has another stage or none
## (skipping stages is fine, Marcel); "rows" adds the next row step of the stage that's there.
func can_build(item: String, sec: int) -> bool:
	if item == "hardcore":
		return sec >= 0
	if sec < 0 or is_building(sec):
		return false
	var st := item_stage(item)
	if st == "rows":
		return next_rows(item, sec) > 0
	return STAGES.has(st) and stage_of(sec) != st


## Places a build adds (for the price) — a new stage is priced on all its places.
func build_places(item: String, sec: int = -1) -> int:
	var st := item_stage(item)
	if st == "rows":
		var nr := next_rows(item, sec) if sec >= 0 else 0
		return (nr - bleacher_rows(sec)) * BLEACHER_SEATS_PER_ROW if nr > 0 else 2 * BLEACHER_SEATS_PER_ROW
	return int(STAGES[st]["rows"][0]) * BLEACHER_SEATS_PER_ROW


func build_cost(item: String, sec: int = -1) -> int:
	if item == "hardcore":
		return 0
	var st := item_stage(item)
	if st == "rows":
		st = stage_of(sec) if sec >= 0 and stage_of(sec) != "" else "bleachers"
	var cost := build_places(item, sec) * float(STAGES[st]["per_place"])
	return int(round(cost * (RUSH_COST if item.ends_with("_rush") else 1.0)))


func build_weeks(item: String, sec: int = -1) -> float:
	if item == "hardcore":
		return 0.0
	var st := item_stage(item)
	var w: float
	if st == "rows":
		var cur := stage_of(sec) if sec >= 0 and stage_of(sec) != "" else "bleachers"
		w = float(STAGES[cur]["row_weeks"])
	else:
		w = float(STAGES[st]["weeks"])
	if item.ends_with("_rush"):
		w *= RUSH_TIME
	if st != "rows" and sec >= 0 and (_section_has_furniture(sec) or stage_of(sec) != ""):
		w += DEMOLITION_WEEKS   # stage jump: one week demolition first (not rushed)
	return w


func start_build(item: String, sec: int) -> bool:
	if not can_build(item, sec) or money < build_cost(item, sec):
		return false
	var st := item_stage(item)
	var stage := stage_of(sec) if st == "rows" else st
	var rows := next_rows(item, sec)
	book("build", "Section %d · %s" % [sec + 1, ("%s to %d rows" % [STAGES[stage]["name"], rows]) if st == "rows" else String(STAGES[stage]["name"])],
		{"Building": -build_cost(item, sec)}, {"note": "rush" if item.ends_with("_rush") else ""})
	var weeks := build_weeks(item, sec)
	# demolish the old furniture in this section
	for k in SPOTS_PER_SECTION:
		slots.erase(str(sec * SPOTS_PER_SECTION + k))
	if st != "rows":
		sections.erase(str(sec))   # demolished: the old stand is gone while the new one goes up
	builds.append({"sec": sec, "stage": stage, "rows": rows, "start": now(), "finish": now() + weeks})
	return true


## Finish every build whose time has come. Returns the finished builds (for a message).
func complete_builds() -> Array:
	var done: Array = []
	var t := now()
	for b in builds.duplicate():
		if float(b["finish"]) <= t + 0.001:
			sections[str(int(b["sec"]))] = {"stage": b["stage"], "rows": int(b["rows"])}
			builds.erase(b)
			done.append(b)
	return done


func seats_in(key: String) -> int:
	if not slots.has(key):
		return 0
	var v: String = slots[key]
	if v == "bench":
		return BENCH_SEATS
	return chairs_in(key)


func chairs_in(key: String) -> int:
	if not slots.has(key):
		return 0
	var v: String = slots[key]
	if v.begins_with("chairs:"):
		return int(v.substr(7))
	return 0


## Bench: only on an empty section. Chair: empty section, or one with fewer than 4 chairs.
func can_place(item: String, slot: int) -> bool:
	if item in SECTION_ITEMS:
		return can_build(item, slot)
	var sec := slot / SPOTS_PER_SECTION
	if bleacher_rows(sec) > 0 or is_building(sec):
		return false
	var key := str(slot)
	if item == "bench":
		return not slots.has(key)
	return not slots.has(key) or (chairs_in(key) > 0 and chairs_in(key) < MAX_CHAIRS_PER_SLOT)


func price_of(item: String) -> int:
	if item in SECTION_ITEMS:
		return build_cost(item)
	return BENCH_PRICE if item == "bench" else CHAIR_PRICE


func place(item: String, slot: int) -> bool:
	if item == "hardcore":
		toggle_hardcore(slot)
		return true
	if item in SECTION_ITEMS:
		return start_build(item, slot)
	var key := str(slot)
	if not can_place(item, slot) or money < price_of(item):
		return false
	book("build", "Bench" if item == "bench" else "Chair", {"Building": -price_of(item)})
	if item == "bench":
		slots[key] = "bench"
	else:
		slots[key] = "chairs:%d" % (chairs_in(key) + 1)
	return true


## Applies a finished match. Home: your fans come, seated ones pay. Away (block 2 placeholder until
## away grounds exist): no ticket income and no seating effect, only the result counts.
func apply_match(goals_for: int, goals_against: int, entertainment_events: int, home: bool = true, opponent: String = "") -> Dictionary:
	var attendance := fans if home else 0
	var seated := mini(attendance, seats())
	var standing := attendance - seated
	# covered seats fill first (Marcel) and cost more: Shed +25%, main stand +50%
	var revenue := 0.0
	var covered := 0
	var left := seated
	for tier in seat_tiers():
		var n := mini(left, int(tier[1]))
		revenue += n * ticket_price() * float(tier[0])
		if tier[2]:
			covered += n
		left -= n
	var lines := {}
	if home:
		lines = {"Tickets": revenue, "Tea hut": attendance * econ("spend"), "Match subs": squad.size() * SUBS_PER_PLAYER,
			"Pitch hire": -cost(PITCH_HIRE), "Referee": -cost(REFEREE_FEE), "Kit washing": -cost(KIT_WASHING)}
	else:
		lines = {"Match subs": squad.size() * SUBS_PER_PLAYER, "Kit washing": -cost(KIT_WASHING), "Travel": -cost(TRAVEL)}
	var cash_before := money

	var result := "D"
	if goals_for > goals_against:
		result = "W"
	elif goals_for < goals_against:
		result = "L"
	record[result.to_lower()] += 1
	matches_played += 1
	var entry := book("match", opponent if opponent != "" else "Friendly", lines,
		{"home": home, "result": result, "score": "%d-%d" % [goals_for, goals_against], "fans": attendance})

	# approval
	var d_app := APPROVAL_DRAW
	if result == "W":
		d_app = APPROVAL_WIN
	elif result == "L":
		d_app = APPROVAL_LOSS
	var ent := minf(entertainment_events * 0.6, APPROVAL_ENTERTAINMENT_MAX)
	var no_seat := APPROVAL_NO_SEAT_MAX * (float(standing) - COVERED_APPROVAL * covered) / maxf(attendance, 1.0) if home else 0.0
	var approval_before := approval
	approval = clampf(approval + d_app + ent + no_seat, 0.0, 100.0)

	# fan growth: results + facilities, scaled by approval (low approval -> slightly negative)
	var base := GROWTH_DRAW
	if result == "W":
		base = GROWTH_WIN
	elif result == "L":
		base = GROWTH_LOSS
	if home:
		base += seats() * GROWTH_PER_SEAT
	var factor := lerpf(-0.3, 1.5, approval / 100.0)
	fans_carry += base * factor
	var gained := int(floor(fans_carry))
	if fans_carry < 0.0:
		gained = int(ceil(fans_carry))
	fans_carry -= gained
	var fans_before := fans
	fans = maxi(1, fans + gained)

	# a couple of new faces on the list after each match
	if candidates.size() > 0:
		candidates.remove_at(0)
	refill_candidates()

	return {
		"result": result, "goals_for": goals_for, "goals_against": goals_against,
		"attendance": attendance, "seated": seated, "standing": standing, "revenue": revenue,
		"fans_before": fans_before, "fans_after": fans,
		"approval_before": approval_before, "approval_after": approval,
		"approval_parts": {"result": d_app, "entertainment": ent, "seating": no_seat},
		"home": home, "lines": lines, "money_in": entry_in(entry), "money_out": entry_out(entry),
		"cash_before": cash_before, "cash_after": money,
	}


# ------------------------------------------------------------------ money

func division() -> int:
	return pyramid.you if pyramid != null else 0


func econ(key: String) -> float:
	return float(DIV_ECON[clampi(division(), 0, DIV_ECON.size() - 1)][key])


## A bottom-tier cost scaled to this division.
func cost(base: int) -> int:
	return int(round(base * econ("costs")))


func ticket_price() -> float:
	return econ("ticket")


## Books money in (+) / out (-) per category and keeps the ledger + cash log.
func book(kind: String, title: String, lines: Dictionary, extra: Dictionary = {}) -> Dictionary:
	var e := {"season": league.season, "week": league.current_week(), "kind": kind, "title": title, "lines": lines}
	e.merge(extra)
	var total := 0.0
	for k in lines:
		total += float(lines[k])
	cash_pennies += total
	var whole := int(cash_pennies)          # towards zero; the pennies wait
	money += whole
	cash_pennies -= whole
	ledger.append(e)
	cash_log.append({"season": league.season, "week": league.current_week(), "cash": money})
	return e


## Week 1 of a season: sponsor in, league fee out (once per season).
func start_season_money() -> void:
	if finances_season >= league.season:
		return
	finances_season = league.season
	book("season", "Season %d starts" % league.season, {"Sponsor": econ("sponsor"), "League fee": -cost(LEAGUE_FEE)},
		{"note": SPONSOR_NAME})


## After the last match: prize money (once per season), and the final tables / play-offs are fixed.
func end_season_money() -> void:
	if prize_paid_season >= league.season or not league.season_over():
		return
	on_regular_season_end()
	prize_paid_season = league.season
	book("season", "Season %d prize money" % league.season, {"Prize money": econ("prize")})


## In/out per category for one season (all categories present, 0 when nothing happened).
func season_totals(season: int) -> Dictionary:
	var inc := {}
	var out := {}
	for c in INCOME_CATS:
		inc[c] = 0.0
	for c in EXPENSE_CATS:
		out[c] = 0.0
	for e in ledger:
		if int(e["season"]) != season:
			continue
		for k in e["lines"]:
			var v := float(e["lines"][k])
			if inc.has(k):
				inc[k] += v
			elif out.has(k):
				out[k] += v
			elif v >= 0.0:
				inc[k] = inc.get(k, 0.0) + v
			else:
				out[k] = out.get(k, 0.0) + v
	return {"in": inc, "out": out}


static func entry_in(e: Dictionary) -> float:
	var t := 0.0
	for k in e["lines"]:
		t += maxf(0.0, float(e["lines"][k]))
	return t


static func entry_out(e: Dictionary) -> float:
	var t := 0.0
	for k in e["lines"]:
		t += minf(0.0, float(e["lines"][k]))
	return t


# ------------------------------------------------------------------ promotion / relegation (GDD §6)

func me() -> Dictionary:
	return {"name": CLUB_NAME, "str": 1.0}


func seats_needed_up() -> int:
	var d := division()
	return PyramidScript.SEATS_TO_ENTER[d + 1] if d < PyramidScript.TOP else 0


func can_go_up() -> bool:
	return division() < PyramidScript.TOP and seats() >= seats_needed_up()


## Called once when your last league match is played: fixes every division's final table and sets up
## your play-offs (as 3rd–7th, or as the 18th fighting to stay up in the division below's play-offs).
func on_regular_season_end() -> void:
	if not league.season_over() or int(season_end.get("season", 0)) == league.season:
		return
	var d := division()
	var tables := []
	for dd in PyramidScript.NAMES.size():
		if dd == d:
			var rows := []
			for r in league.table():
				rows.append(me() if r["team"] == 0 else league.teams[r["team"]])
			tables.append(rows)
		else:
			tables.append(pyramid.simulate_table(dd))
	var blocked := [] if can_go_up() else [CLUB_NAME]
	season_end = {"season": league.season, "tables": tables, "blocked": blocked, "pos": league.position_of(0)}
	playoff = {}
	if d < PyramidScript.TOP:
		var above18 = tables[d + 1][17]
		var seeds := PyramidScript.playoff_seeds(tables[d], above18, blocked)
		for k in seeds:
			if seeds[k] != null and seeds[k]["name"] == CLUB_NAME:
				playoff = {"div": d, "bracket": PyramidScript.bracket(seeds)}
	if playoff.is_empty() and d > 0 and league.position_of(0) == 18:
		var seeds2 := PyramidScript.playoff_seeds(tables[d - 1], me(), [])
		playoff = {"div": d - 1, "bracket": PyramidScript.bracket(seeds2)}


func _your_tie(br: Dictionary, rnd: int) -> String:
	for k in PyramidScript.TIES:
		var t: Dictionary = br[k]
		if int(t["round"]) != rnd:
			continue
		for c in t["teams"]:
			if c != null and c["name"] == CLUB_NAME:
				return k
	return ""


## Your next play-off leg, or {} when your play-offs are over. AI ties are simulated as they come up.
## {tie, leg (0/1), home, opponent {name, str}, round, first_leg [us, them] (second leg only)}
func playoff_fixture() -> Dictionary:
	if playoff.is_empty():
		return {}
	var br: Dictionary = playoff["bracket"]
	for rnd in [1, 2, 3]:
		PyramidScript.advance(br)
		var mine := _your_tie(br, rnd)
		for k in PyramidScript.TIES:
			var t: Dictionary = br[k]
			if int(t["round"]) == rnd and k != mine and t["winner"] == null and t["teams"][0] != null and t["teams"][1] != null:
				PyramidScript.sim_tie(t)
		if mine != "" and br[mine]["winner"] == null and br[mine]["teams"][0] != null and br[mine]["teams"][1] != null:
			var t: Dictionary = br[mine]
			var leg: int = t["legs"].size()
			var us := 0 if t["teams"][0]["name"] == CLUB_NAME else 1
			league.extra_week = rnd
			var fx := {"tie": mine, "leg": leg, "home": leg == us, "opponent": t["teams"][1 - us], "round": rnd}
			if leg == 1:
				fx["first_leg"] = [int(t["legs"][0][us]), int(t["legs"][0][1 - us])]
			return fx
		PyramidScript.advance(br)
	return {}


func playoff_done() -> bool:
	return playoff.is_empty() or playoff_fixture().is_empty()


## Your leg is played. `won_after` = true/false when extra time/penalties decided a level tie, else null.
func record_playoff_leg(tie: String, us_goals: int, them_goals: int, won_after = null, how := "") -> void:
	var t: Dictionary = playoff["bracket"][tie]
	var us := 0 if t["teams"][0]["name"] == CLUB_NAME else 1
	var g := [0, 0]
	g[us] = us_goals
	g[1 - us] = them_goals
	t["legs"].append(g)
	if t["legs"].size() == 2:
		var a := int(t["legs"][0][us]) + int(t["legs"][1][us])
		var b := int(t["legs"][0][1 - us]) + int(t["legs"][1][1 - us])
		var we_win := a > b if a != b else bool(won_after)
		if how != "":
			t[how] = true
		t["winner"] = t["teams"][us] if we_win else t["teams"][1 - us]


func division_name(d := -1) -> String:
	return PyramidScript.NAMES[clampi(division() if d < 0 else d, 0, PyramidScript.NAMES.size() - 1)]


## Where you'll be next season, as far as it's known now (season over, play-offs done or not needed).
## {outcome promoted|relegated|stayed, denied (would have gone up but not enough seats), to}
func expected_outcome() -> Dictionary:
	var d := division()
	var pos := league.position_of(0)
	var blocked: Array = season_end.get("blocked", [])
	var out := "stayed"
	var denied := false
	if not playoff.is_empty() and playoff_done():
		var w = playoff["bracket"]["F"]["winner"]
		var won: bool = w != null and w["name"] == CLUB_NAME
		if int(playoff["div"]) == d:
			out = "promoted" if won else "stayed"
		else:
			out = "stayed" if won else "relegated"
	elif d < PyramidScript.TOP and pos <= 2:
		out = "promoted" if blocked.is_empty() else "stayed"
		denied = not blocked.is_empty()
	elif d < PyramidScript.TOP and pos <= 7 and not blocked.is_empty():
		denied = true
	elif d > 0 and pos >= 19:
		out = "relegated"
	var to := d + (1 if out == "promoted" else (-1 if out == "relegated" else 0))
	return {"outcome": out, "denied": denied, "to": to}


static func round_name(rnd: int, tie: String) -> String:
	if rnd == 3:
		return "Play-off final"
	if rnd == 2:
		return "Play-off semi-final"
	return "Play-off quarter-final"


## "Start season N+1": play-offs everywhere, everybody moves, you land in your new division.
func start_next_season() -> Dictionary:
	on_regular_season_end()
	var tables: Array = season_end["tables"]
	var blocked: Array = season_end["blocked"]
	var d := division()
	var po := []
	for dd in PyramidScript.NAMES.size():
		if dd >= PyramidScript.TOP:
			po.append(null)
		elif not playoff.is_empty() and int(playoff["div"]) == dd:
			PyramidScript.advance(playoff["bracket"])
			po.append(playoff["bracket"]["F"]["winner"])
		else:
			var seeds := PyramidScript.playoff_seeds(tables[dd], tables[dd + 1][17], blocked if dd == d else [])
			po.append(PyramidScript.sim_playoffs(seeds))
	pyramid.divisions[d] = league.teams.slice(1)
	var pos: int = season_end["pos"]
	pyramid.apply_moves(tables, po, blocked)
	var nd := d
	for dd in pyramid.divisions.size():
		for i in pyramid.divisions[dd].size():
			if pyramid.divisions[dd][i]["name"] == CLUB_NAME:
				nd = dd
				pyramid.divisions[dd].remove_at(i)
				break
	pyramid.you = nd
	var outcome := "stayed"
	if nd > d:
		outcome = "promoted"
	elif nd < d:
		outcome = "relegated"
	var would_go_up := d < PyramidScript.TOP and (pos <= 2 or (pos <= 7 and not blocked.is_empty()))
	last_report = {"season": league.season, "from": d, "to": nd, "pos": pos, "outcome": outcome,
		"denied": not blocked.is_empty() and would_go_up and outcome != "promoted", "seats_needed": seats_needed_up() if nd == d else 0,
		"playoff": _playoff_summary()}
	var old_season := league.season
	league = LeagueScript.create_with(CLUB_NAME, pyramid.divisions[nd])
	league.season = old_season + 1
	league.last_finish = pos
	season_end = {}
	playoff = {}
	start_season_money()
	return last_report


func _playoff_summary() -> String:
	if playoff.is_empty():
		return ""
	var br: Dictionary = playoff["bracket"]
	var last := ""
	for k in ["A", "B", "C", "D", "F"]:
		var t: Dictionary = br[k]
		for c in t["teams"]:
			if c != null and c["name"] == CLUB_NAME:
				last = k
	if last == "":
		return ""
	var t: Dictionary = br[last]
	if t["winner"] == null:
		return "In the %s" % round_name(int(t["round"]), last).to_lower()
	var won: bool = t["winner"]["name"] == CLUB_NAME
	var nm := round_name(int(t["round"]), last).replace("Play-off ", "")
	return ("Won the play-off final" if last == "F" else "Through the %s" % nm) if won else "Out in the play-off %s" % nm


func is_hardcore(sec: int) -> bool:
	return hardcore.has(str(sec))


func toggle_hardcore(sec: int) -> void:
	if hardcore.has(str(sec)):
		hardcore.erase(str(sec))
	else:
		hardcore[str(sec)] = true


# ------------------------------------------------------------------ save / load

func to_dict() -> Dictionary:
	return {
		"version": SAVE_VERSION, "money": money, "fans": fans, "approval": approval, "squad": squad,
		"candidates": candidates, "slots": slots, "record": record,
		"matches_played": matches_played, "fans_carry": fans_carry,
		"league": league.to_dict(), "sections": sections, "builds": builds,
		"hardcore": hardcore, "temperature": temperature,
		"ledger": ledger, "cash_log": cash_log, "cash_pennies": cash_pennies,
		"pyramid": pyramid.to_dict(), "season_end": season_end, "playoff": playoff, "last_report": last_report,
		"finances_season": finances_season, "prize_paid_season": prize_paid_season,
	}


static func from_dict(d: Dictionary) -> ClubState:
	if int(d.get("version", 1)) < SAVE_VERSION:
		return new_game()   # saves don't matter yet (Marcel, 2026-11-07): old layout -> fresh start
	var s := ClubState.new()
	s.money = int(d.get("money", START_MONEY))
	s.fans = int(d.get("fans", START_FANS))
	s.approval = float(d.get("approval", START_APPROVAL))
	s.squad = d.get("squad", [])
	s.candidates = d.get("candidates", [])
	s.slots = d.get("slots", {})
	var r: Dictionary = d.get("record", {"w": 0, "d": 0, "l": 0})
	s.record = {"w": int(r.get("w", 0)), "d": int(r.get("d", 0)), "l": int(r.get("l", 0))}
	s.matches_played = int(d.get("matches_played", 0))
	s.fans_carry = float(d.get("fans_carry", 0.0))
	s.league = LeagueScript.from_dict(d.get("league", {}))
	s.sections = d.get("sections", {})
	for k in s.sections:
		s.sections[k]["rows"] = int(s.sections[k]["rows"])
	s.pyramid = PyramidScript.from_dict(d.get("pyramid", {}))
	s.season_end = d.get("season_end", {})
	s.playoff = d.get("playoff", {})
	s.last_report = d.get("last_report", {})
	s.ledger = d.get("ledger", [])
	s.cash_log = d.get("cash_log", [])
	s.cash_pennies = float(d.get("cash_pennies", 0.0))
	s.finances_season = int(d.get("finances_season", 0))
	s.prize_paid_season = int(d.get("prize_paid_season", 0))
	s.hardcore = d.get("hardcore", {})
	s.temperature = String(d.get("temperature", "mild"))
	s.builds = d.get("builds", [])
	for b in s.builds:
		b["sec"] = int(b["sec"])
		b["rows"] = int(b["rows"])
	s.refill_candidates()
	s.start_season_money()
	return s


func save() -> void:
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f == null:
		push_warning("Could not save: %s" % error_string(FileAccess.get_open_error()))
		return
	f.store_string(JSON.stringify(to_dict(), "  "))


static func load_or_new() -> ClubState:
	if not FileAccess.file_exists(SAVE_PATH):
		return new_game()
	var f := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if f == null:
		return new_game()
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed is Dictionary:
		return from_dict(parsed)
	return new_game()


static func delete_save() -> void:
	if FileAccess.file_exists(SAVE_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE_PATH))
