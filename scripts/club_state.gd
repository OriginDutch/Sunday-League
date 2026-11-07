class_name ClubState
extends RefCounted
const LeagueScript = preload("res://scripts/league.gd")
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
const SECTION_ITEMS := ["bleachers", "bleachers_rush", "rows", "rows_rush"]
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
var sections: Dictionary = {}       # section index (String) -> {"stage": "bleachers", "rows": n}
var builds: Array = []              # [{"sec", "stage", "rows", "finish" (absolute week), "start"}]


static func new_game() -> ClubState:
	var s := ClubState.new()
	for i in START_SQUAD:
		s.squad.append(Names.person())
	s.refill_candidates()
	s.league = LeagueScript.create(CLUB_NAME)
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
		if not is_building(int(k)):
			n += int(sections[k]["rows"]) * BLEACHER_SEATS_PER_ROW
	return n


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


## Section items: "bleachers" on a section without a stand; "rows" adds the next row step.
func can_build(item: String, sec: int) -> bool:
	if sec < 0 or is_building(sec):
		return false
	if item.begins_with("bleachers"):
		return bleacher_rows(sec) == 0
	if item.begins_with("rows"):
		var r := bleacher_rows(sec)
		return r > 0 and r < BLEACHER_ROWS[-1]
	return false


func build_cost(item: String, sec: int = -1) -> int:
	var places := BLEACHER_ROWS[0] * BLEACHER_SEATS_PER_ROW
	if item.begins_with("rows"):
		places = 2 * BLEACHER_SEATS_PER_ROW
		var r := bleacher_rows(sec) if sec >= 0 else 0
		var i := BLEACHER_ROWS.find(r)
		if i >= 0 and i + 1 < BLEACHER_ROWS.size():
			places = (BLEACHER_ROWS[i + 1] - r) * BLEACHER_SEATS_PER_ROW
	var cost := places * BLEACHER_PRICE_PER_PLACE
	return int(round(cost * (RUSH_COST if item.ends_with("_rush") else 1.0)))


func build_weeks(item: String, sec: int = -1) -> float:
	var w := BLEACHER_WEEKS if item.begins_with("bleachers") else ROW_UPGRADE_WEEKS
	if item.ends_with("_rush"):
		w *= RUSH_TIME
	if item.begins_with("bleachers") and sec >= 0 and _section_has_furniture(sec):
		w += DEMOLITION_WEEKS   # stage jump: one week demolition first (not rushed)
	return w


func start_build(item: String, sec: int) -> bool:
	if not can_build(item, sec) or money < build_cost(item, sec):
		return false
	money -= build_cost(item, sec)
	var rows := BLEACHER_ROWS[0]
	if item.begins_with("rows"):
		rows = BLEACHER_ROWS[BLEACHER_ROWS.find(bleacher_rows(sec)) + 1]
	var weeks := build_weeks(item, sec)
	# demolish the old furniture in this section
	for k in SPOTS_PER_SECTION:
		slots.erase(str(sec * SPOTS_PER_SECTION + k))
	builds.append({"sec": sec, "stage": "bleachers", "rows": rows, "start": now(), "finish": now() + weeks})
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
	if item in SECTION_ITEMS:
		return start_build(item, slot)
	var key := str(slot)
	if not can_place(item, slot) or money < price_of(item):
		return false
	money -= price_of(item)
	if item == "bench":
		slots[key] = "bench"
	else:
		slots[key] = "chairs:%d" % (chairs_in(key) + 1)
	return true


## Applies a finished match. Home: your fans come, seated ones pay. Away (block 2 placeholder until
## away grounds exist): no ticket income and no seating effect, only the result counts.
func apply_match(goals_for: int, goals_against: int, entertainment_events: int, home: bool = true) -> Dictionary:
	var attendance := fans if home else 0
	var seated := mini(attendance, seats())
	var standing := attendance - seated
	var revenue := seated * TICKET_PRICE
	money += revenue

	var result := "D"
	if goals_for > goals_against:
		result = "W"
	elif goals_for < goals_against:
		result = "L"
	record[result.to_lower()] += 1
	matches_played += 1

	# approval
	var d_app := APPROVAL_DRAW
	if result == "W":
		d_app = APPROVAL_WIN
	elif result == "L":
		d_app = APPROVAL_LOSS
	var ent := minf(entertainment_events * 0.6, APPROVAL_ENTERTAINMENT_MAX)
	var no_seat := APPROVAL_NO_SEAT_MAX * (float(standing) / maxf(attendance, 1.0)) if home else 0.0
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
		"home": home,
	}


# ------------------------------------------------------------------ save / load

func to_dict() -> Dictionary:
	return {
		"version": SAVE_VERSION, "money": money, "fans": fans, "approval": approval, "squad": squad,
		"candidates": candidates, "slots": slots, "record": record,
		"matches_played": matches_played, "fans_carry": fans_carry,
		"league": league.to_dict(), "sections": sections, "builds": builds,
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
	s.builds = d.get("builds", [])
	for b in s.builds:
		b["sec"] = int(b["sec"])
		b["rows"] = int(b["rows"])
	s.refill_candidates()
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
