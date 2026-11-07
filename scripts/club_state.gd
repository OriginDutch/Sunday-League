class_name ClubState
extends RefCounted
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
const SAVE_VERSION := 2             # v2 = sections; older saves start a new game

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


static func new_game() -> ClubState:
	var s := ClubState.new()
	for i in START_SQUAD:
		s.squad.append(Names.person())
	s.refill_candidates()
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
	return n


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
	var key := str(slot)
	if item == "bench":
		return not slots.has(key)
	return not slots.has(key) or (chairs_in(key) > 0 and chairs_in(key) < MAX_CHAIRS_PER_SLOT)


func price_of(item: String) -> int:
	return BENCH_PRICE if item == "bench" else CHAIR_PRICE


func place(item: String, slot: int) -> bool:
	var key := str(slot)
	if not can_place(item, slot) or money < price_of(item):
		return false
	money -= price_of(item)
	if item == "bench":
		slots[key] = "bench"
	else:
		slots[key] = "chairs:%d" % (chairs_in(key) + 1)
	return true


## Applies a finished friendly. Returns a summary dictionary for the post-match screen.
func apply_match(goals_for: int, goals_against: int, entertainment_events: int) -> Dictionary:
	var attendance := fans
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
	var no_seat := APPROVAL_NO_SEAT_MAX * (float(standing) / maxf(attendance, 1.0))
	var approval_before := approval
	approval = clampf(approval + d_app + ent + no_seat, 0.0, 100.0)

	# fan growth: results + facilities, scaled by approval (low approval -> slightly negative)
	var base := GROWTH_DRAW
	if result == "W":
		base = GROWTH_WIN
	elif result == "L":
		base = GROWTH_LOSS
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
	}


# ------------------------------------------------------------------ save / load

func to_dict() -> Dictionary:
	return {
		"version": SAVE_VERSION, "money": money, "fans": fans, "approval": approval, "squad": squad,
		"candidates": candidates, "slots": slots, "record": record,
		"matches_played": matches_played, "fans_carry": fans_carry,
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
