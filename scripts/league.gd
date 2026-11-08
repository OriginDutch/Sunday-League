extends RefCounted
## (No class_name on purpose: load by path, so a fresh pull runs before the editor rescans.)
## One division: 20 teams, a 38-round season (19 home, 19 away) spread over 42 weeks,
## simulated results for every match you don't play, and the table. GDD §10a/§10b calendar.
## Team 0 is you. Saved inside the club save.

const TEAMS := 20
const SEASON_WEEKS := 42            # tunable (GDD: 42 weeks season + 10 weeks off-season)
const OFFSEASON_WEEKS := 10
const DOUBLE_WEEKS := 3             # weeks with two league rounds (fixture spacing)
# simulation (tunable): expected goals scale with strength ratio
const SIM_HOME_GOALS := 1.5
const SIM_AWAY_GOALS := 1.15
const SIM_STRENGTH_POWER := 4.0
const STRENGTH_MIN := 0.92          # same range the friendlies used for opponent speed
const STRENGTH_MAX := 1.08

var teams: Array = []               # [{name, str}] ; index 0 = you
var rounds: Array = []              # [{week, matches: [[home, away], ...], results: [[hg, ag] or null, ...]}]
var round_idx := 0                  # next round to play
var season := 1
var last_finish := 0                # your position last season (0 = none yet)
var extra_week := 0                 # play-off round you're in after the season (weeks 43–45)


## Your division from the pyramid: you + the 19 other clubs (shared dicts with the pyramid).
static func create_with(club_name: String, others: Array) -> RefCounted:
	var l = load("res://scripts/league.gd").new()
	l.teams.append({"name": club_name, "str": 1.0})
	for t in others.slice(0, TEAMS - 1):
		l.teams.append(t)
	l.make_fixtures()
	return l


static func create(club_name: String) -> RefCounted:
	var l = load("res://scripts/league.gd").new()
	l.teams.append({"name": club_name, "str": 1.0})
	var used := {}
	while l.teams.size() < TEAMS:
		var n: String = Names.opponent_unique(used)
		l.teams.append({"name": n, "str": snappedf(randf_range(STRENGTH_MIN, STRENGTH_MAX), 0.001)})
	l.make_fixtures()
	return l


## Double round robin. First half: everyone meets once (circle method), venues balanced so each
## team gets 9–10 home matches. Second half: the same pairs with venues swapped, in a new order.
func make_fixtures() -> void:
	rounds.clear()
	round_idx = 0
	var first: Array = []
	for attempt in 500:
		first = _first_half()
		if not first.is_empty():
			break
	first.shuffle()
	var second: Array = []
	for matches in first:
		var sw: Array = []
		for m in matches:
			sw.append([m[1], m[0]])
		second.append(sw)
	# new order for the returns; never the same pair in the last round of the first half and the first of the second
	for attempt in 50:
		second.shuffle()
		if not _same_pairs(first[-1], second[0]):
			break
	var all: Array = first + second
	# weeks: 3 double weeks (two rounds in one week), the rest spread over 42 weeks with a few empty weeks
	var n := all.size()
	var doubles := {}
	while doubles.size() < DOUBLE_WEEKS:
		var r := randi_range(4, n - 4)
		if not doubles.has(r) and not doubles.has(r - 1) and not doubles.has(r + 1):
			doubles[r] = true
	var weeks_used := n - DOUBLE_WEEKS
	var blanks := SEASON_WEEKS - weeks_used
	var gap_after := {}
	while gap_after.size() < blanks:
		var r := randi_range(1, n - 2)
		if not doubles.has(r + 1) and not gap_after.has(r):
			gap_after[r] = true
	var week := 1
	for r in n:
		if r > 0:
			if doubles.has(r):
				pass        # same week as the previous round (midweek)
			else:
				week += 2 if gap_after.has(r - 1) else 1
		var res: Array = []
		res.resize(all[r].size())
		rounds.append({"week": week, "matches": all[r], "results": res})


## One round robin with venues balanced to 9–10 home matches per team. Empty array = unlucky, try again.
func _first_half() -> Array:
	var order: Array = range(TEAMS)
	order.shuffle()
	var home_count := {}
	for t in TEAMS:
		home_count[t] = 0
	var first: Array = []
	for r in TEAMS - 1:
		var matches: Array = []
		for i in TEAMS / 2:
			var a: int = order[i]
			var b: int = order[TEAMS - 1 - i]
			var a_home: bool
			if home_count[a] != home_count[b]:
				a_home = home_count[a] < home_count[b]
			else:
				a_home = randf() < 0.5
			var m := [a, b] if a_home else [b, a]
			home_count[m[0]] += 1
			matches.append(m)
		first.append(matches)
		# rotate everything but the first slot
		var last: int = order.pop_back()
		order.insert(1, last)
	for t in TEAMS:
		if home_count[t] < (TEAMS - 1) / 2 or home_count[t] > (TEAMS - 1) / 2 + 1:
			return []
	return first


func _same_pairs(a: Array, b: Array) -> bool:
	for m in a:
		for k in b:
			if (m[0] == k[0] and m[1] == k[1]) or (m[0] == k[1] and m[1] == k[0]):
				if m[0] == 0 or m[1] == 0:
					return true
	return false


func season_over() -> bool:
	return round_idx >= rounds.size()


func current_week() -> int:
	if season_over():
		return SEASON_WEEKS + extra_week
	return int(rounds[round_idx]["week"])


## Your next match: {opponent (index), home (bool), week, round}. Empty when the season is over.
func next_fixture() -> Dictionary:
	if season_over():
		return {}
	for m in rounds[round_idx]["matches"]:
		if m[0] == 0:
			return {"opponent": m[1], "home": true, "week": current_week(), "round": round_idx + 1}
		if m[1] == 0:
			return {"opponent": m[0], "home": false, "week": current_week(), "round": round_idx + 1}
	return {}


## Store your result, simulate the rest of the round, move on. Returns the round's results as text lines.
func play_round(your_goals: int, their_goals: int) -> Array:
	var lines: Array = []
	var rd: Dictionary = rounds[round_idx]
	for i in rd["matches"].size():
		var m: Array = rd["matches"][i]
		var r: Array
		if m[0] == 0:
			r = [your_goals, their_goals]
		elif m[1] == 0:
			r = [their_goals, your_goals]
		else:
			r = _simulate(m[0], m[1])
		rd["results"][i] = r
		lines.append("%s %d - %d %s" % [teams[m[0]]["name"], r[0], r[1], teams[m[1]]["name"]])
	round_idx += 1
	return lines


func _simulate(h: int, a: int) -> Array:
	var ratio: float = float(teams[h]["str"]) / float(teams[a]["str"])
	var lh := SIM_HOME_GOALS * pow(ratio, SIM_STRENGTH_POWER)
	var la := SIM_AWAY_GOALS * pow(1.0 / ratio, SIM_STRENGTH_POWER)
	return [_poisson(lh), _poisson(la)]


static func _poisson(lam: float) -> int:
	var l := exp(-lam)
	var k := 0
	var p := 1.0
	while true:
		p *= randf()
		if p <= l:
			return k
		k += 1
	return k


## Sorted table rows: {team, name, p, w, d, l, gf, ga, gd, pts}
func table() -> Array:
	var rows := {}
	for t in teams.size():
		rows[t] = {"team": t, "name": teams[t]["name"], "p": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "gd": 0, "pts": 0}
	for rd in rounds:
		for i in rd["matches"].size():
			var r = rd["results"][i]
			if r == null:
				continue
			var m: Array = rd["matches"][i]
			_add(rows[m[0]], r[0], r[1])
			_add(rows[m[1]], r[1], r[0])
	var out: Array = rows.values()
	out.sort_custom(func(x, y):
		if x["pts"] != y["pts"]:
			return x["pts"] > y["pts"]
		if x["gd"] != y["gd"]:
			return x["gd"] > y["gd"]
		if x["gf"] != y["gf"]:
			return x["gf"] > y["gf"]
		return x["name"] < y["name"])
	return out


func _add(row: Dictionary, f: int, a: int) -> void:
	row["p"] += 1
	row["gf"] += f
	row["ga"] += a
	row["gd"] = row["gf"] - row["ga"]
	if f > a:
		row["w"] += 1
		row["pts"] += 3
	elif f == a:
		row["d"] += 1
		row["pts"] += 1
	else:
		row["l"] += 1


func position_of(team: int) -> int:
	var t := table()
	for i in t.size():
		if t[i]["team"] == team:
			return i + 1
	return 0


## After the last round: the 10-week off-season is skipped and a new season starts (same division for now).
func start_new_season() -> void:
	last_finish = position_of(0)
	season += 1
	make_fixtures()


func to_dict() -> Dictionary:
	return {"teams": teams, "rounds": rounds, "round_idx": round_idx, "season": season, "last_finish": last_finish, "extra_week": extra_week}


static func from_dict(d: Dictionary) -> RefCounted:
	var l = load("res://scripts/league.gd").new()
	l.teams = d.get("teams", [])
	l.rounds = d.get("rounds", [])
	l.round_idx = int(d.get("round_idx", 0))
	l.season = int(d.get("season", 1))
	l.last_finish = int(d.get("last_finish", 0))
	l.extra_week = int(d.get("extra_week", 0))
	# JSON turns ints into floats: normalise what we index with
	for rd in l.rounds:
		rd["week"] = int(rd["week"])
		for m in rd["matches"]:
			m[0] = int(m[0])
			m[1] = int(m[1])
		for i in rd["results"].size():
			if rd["results"][i] != null:
				rd["results"][i] = [int(rd["results"][i][0]), int(rd["results"][i][1])]
	if l.teams.size() != TEAMS or l.rounds.is_empty():
		return create("Your club")
	return l
