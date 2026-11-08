extends RefCounted
## The pyramid (GDD §6): 14 divisions of 20 clubs. Your own division is played in full (league.gd);
## the other 13 are simulated at the end of each season. Promotion / relegation (Marcel, 2026-11-07/08):
## 1st–2nd up, 19th–20th down; play-offs for one more spot between 3rd–7th and the 18th of the division
## above (bracket: A = 7v4, B = 6v5, C = A v B, D = 18 v 3, final C v D, two legs each, extra time + penalties).
## Promotion needs enough seats (SEATS_TO_ENTER); without them your place goes to the next club.
## Loaded by path (no class_name): `const PyramidScript := preload("res://scripts/pyramid.gd")`.

const NAMES := ["Non-League 3", "Non-League 2", "Non-League 1", "League 10", "League 9", "League 8", "League 7",
	"League 6", "League 5", "League 4", "League 3", "League 2", "League 1", "Premier Division"]
## Seats needed to play in a division (Marcel: "akkoord voor nu").
const SEATS_TO_ENTER := [0, 10, 20, 40, 60, 100, 150, 300, 600, 1000, 2000, 3000, 4000, 5000]
const TEAMS := 20
const TOP := 13

# Club names: pub teams in Non-League, town clubs from League 10 up (placeholders until naming is designed)
const TOWN_A := ["Ash", "Brad", "Carl", "Dun", "East", "Fair", "Green", "Hart", "Kings", "Lang", "Mid", "North",
	"Oak", "Port", "Rich", "Stan", "Thorn", "Wal", "West", "Whit", "Wold", "Bram", "Cross", "Elm", "Fen", "Hol",
	"Lyn", "Marl", "Pen", "Sal", "Tam", "Wen", "Ux", "Bex", "Chal", "Dor", "Ever", "Glen"]
const TOWN_B := ["ford", "ham", "ton", "bury", "field", "wick", "ley", "worth", "bridge", "mouth", "borough",
	"chester", "stone", "dale", "port", "sea", "minster", "well"]
const TOWN_C := ["Town", "United", "City", "Rovers", "Athletic", "Albion", "FC", "Wanderers", "County", "Borough"]

var divisions: Array = []       # [div] -> [{name, str}] (the other clubs; in your division the 19 others)
var you := 0                    # your division


static func create() -> RefCounted:
	var p = load("res://scripts/pyramid.gd").new()
	var used := {}
	for d in NAMES.size():
		var list := []
		var n := TEAMS - 1 if d == 0 else TEAMS
		while list.size() < n:
			var nm := _club_name(d, used)
			list.append({"name": nm, "str": snappedf(randf_range(0.92, 1.08), 0.001)})
		p.divisions.append(list)
	return p


static func _club_name(d: int, used: Dictionary) -> String:
	for i in 200:
		var nm: String
		if d <= 2:
			nm = Names.opponent()
		else:
			nm = "%s%s %s" % [TOWN_A.pick_random(), TOWN_B.pick_random(), TOWN_C.pick_random()]
		if not used.has(nm):
			used[nm] = true
			return nm
	return "Club %d" % used.size()


func name_of(d: int) -> String:
	return NAMES[clampi(d, 0, TOP)]


## Lines on a division's table (GDD §6): promotion/play-offs off at the top, relegation/18th off at the bottom.
static func has_promotion(d: int) -> bool:
	return d < TOP


static func has_relegation(d: int) -> bool:
	return d > 0


# ------------------------------------------------------------------ season end

## A simulated final table for another division: stronger clubs tend to finish higher.
func simulate_table(d: int) -> Array:
	var rows := []
	for t in divisions[d]:
		rows.append({"name": t["name"], "str": t["str"], "k": float(t["str"]) + randfn(0.0, 0.035)})
	rows.sort_custom(func(a, b): return a["k"] > b["k"])
	return rows


## Play-off seeds for division d from its final table (rows: [{name, str}], 1st first) and the
## division above's 18th. Clubs that can't go up (you without the seats) are skipped.
## Returns {"3".."7": club, "18": club or null}.
static func playoff_seeds(rows: Array, eighteenth, skip: Array) -> Dictionary:
	var eligible := rows.filter(func(r): return not (r["name"] in skip))
	var seeds := {}
	for i in 5:
		if 2 + i < eligible.size():
			seeds[str(3 + i)] = eligible[2 + i]
	seeds["18"] = eighteenth
	return seeds


const TIES := ["A", "B", "C", "D", "F"]


## The bracket for a seeding (Marcel's format). Ties: [first-leg home, second-leg home].
## The higher-placed club hosts the second leg (EFL / KNVB rule; Marcel 2026-11-08). The 18th of the
## division above counts as the highest (rank 0), then 3rd … 7th.
static func bracket(seeds: Dictionary) -> Dictionary:
	var rank := {}
	for k in seeds:
		if seeds[k] != null:
			rank[seeds[k]["name"]] = 0 if k == "18" else int(k)
	return {
		"A": {"teams": [seeds.get("7"), seeds.get("4")], "legs": [], "winner": null, "round": 1},
		"B": {"teams": [seeds.get("6"), seeds.get("5")], "legs": [], "winner": null, "round": 1},
		"C": {"teams": [null, null], "legs": [], "winner": null, "round": 2, "from": ["A", "B"]},
		"D": {"teams": [seeds.get("3"), seeds.get("18")], "legs": [], "winner": null, "round": 2},
		"F": {"teams": [null, null], "legs": [], "winner": null, "round": 3, "from": ["C", "D"]},
		"rank": rank,
	}


## Fill in later ties once their feeders are decided; byes when a seed is missing.
static func advance(br: Dictionary) -> void:
	for k in ["A", "B", "D"]:
		var t: Dictionary = br[k]
		if t["winner"] == null:
			if t["teams"][0] == null and t["teams"][1] != null:
				t["winner"] = t["teams"][1]
			elif t["teams"][1] == null and t["teams"][0] != null:
				t["winner"] = t["teams"][0]
	for k in ["C", "F"]:
		var t: Dictionary = br[k]
		var f: Array = t["from"]
		if t["teams"][0] == null and br[f[0]]["winner"] != null:
			t["teams"][0] = br[f[0]]["winner"]
		if t["teams"][1] == null and br[f[1]]["winner"] != null:
			t["teams"][1] = br[f[1]]["winner"]
		# both known, nothing played yet: the lower-placed club hosts the first leg
		var tm: Array = t["teams"]
		var rk: Dictionary = br.get("rank", {})
		if tm[0] != null and tm[1] != null and t["legs"].is_empty():
			if int(rk.get(tm[0]["name"], 99)) < int(rk.get(tm[1]["name"], 99)):
				t["teams"] = [tm[1], tm[0]]


## Simulate a whole tie (both legs, extra time, penalties) between two AI clubs.
static func sim_tie(t: Dictionary) -> void:
	var a: Dictionary = t["teams"][0]
	var b: Dictionary = t["teams"][1]
	var ratio := float(a["str"]) / float(b["str"])
	t["legs"] = [[_poisson(1.5 * pow(ratio, 4.0)), _poisson(1.15 * pow(1.0 / ratio, 4.0))],
		[_poisson(1.15 * pow(ratio, 4.0)), _poisson(1.5 * pow(1.0 / ratio, 4.0))]]   # [a goals, b goals] per leg
	var ga: int = t["legs"][0][0] + t["legs"][1][0]
	var gb: int = t["legs"][0][1] + t["legs"][1][1]
	if ga == gb:
		ga += _poisson(0.35 * pow(ratio, 4.0))
		gb += _poisson(0.45 * pow(1.0 / ratio, 4.0))      # second-leg hosts in extra time
		t["extra"] = true
	if ga == gb:
		t["pens"] = true
		if randf() < 0.5 + (ratio - 1.0):
			ga += 1
		else:
			gb += 1
	t["winner"] = a if ga > gb else b


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


## Whole play-offs of a division, simulated. Returns the winner (a club dict).
static func sim_playoffs(seeds: Dictionary) -> Variant:
	var br := bracket(seeds)
	for rnd in [1, 2, 3]:
		advance(br)
		for k in TIES:
			var t: Dictionary = br[k]
			if t["round"] == rnd and t["winner"] == null and t["teams"][0] != null and t["teams"][1] != null:
				sim_tie(t)
	advance(br)
	return br["F"]["winner"]


## End of season for every division. `tables[d]` = final rows [{name, str}] (1st first) — your division's
## real table, the rest simulated; `po_winner[d]` = play-off winner of division d (already decided for the
## play-offs you were in, simulated otherwise). Moves the clubs; returns {name: "up"/"down"} for reports.
func apply_moves(tables: Array, po_winner: Array, blocked: Array) -> Dictionary:
	var moves := {}
	var new_divs := []
	for d in NAMES.size():
		new_divs.append([])
	for d in NAMES.size():
		var rows: Array = tables[d]
		var up := []
		var down := []
		if has_promotion(d):
			var eligible := rows.filter(func(r): return not (r["name"] in blocked))
			for i in mini(2, eligible.size()):
				up.append(eligible[i]["name"])
			var w = po_winner[d]
			if w != null and not (w["name"] in up):
				var above: Array = tables[d + 1] if d + 1 <= TOP else []
				var their_18 = above[17]["name"] if above.size() >= 18 else ""
				if w["name"] != their_18:
					up.append(w["name"])
		if has_relegation(d):
			for i in [18, 19]:
				if i < rows.size():
					down.append(rows[i]["name"])
			# 18th: down unless they won the play-offs of the division below
			if rows.size() >= 18:
				var w2 = po_winner[d - 1]
				if w2 == null or w2["name"] != rows[17]["name"]:
					down.append(rows[17]["name"])
		for r in rows:
			var nm: String = r["name"]
			var club := {"name": nm, "str": r["str"]}
			if nm in up:
				new_divs[d + 1].append(club)
				moves[nm] = "up"
			elif nm in down:
				new_divs[d - 1].append(club)
				moves[nm] = "down"
			else:
				new_divs[d].append(club)
	# a division that lost/gained an uneven number (e.g. the 18th stayed up) is topped up / trimmed
	for d in NAMES.size():
		while new_divs[d].size() > TEAMS:
			var extra = new_divs[d].pop_back()
			new_divs[d - 1 if d > 0 else d + 1].append(extra)
		while new_divs[d].size() < TEAMS:
			var used := {}
			for dd in new_divs:
				for c in dd:
					used[c["name"]] = true
			new_divs[d].append({"name": _club_name(d, used), "str": snappedf(randf_range(0.92, 1.08), 0.001)})
	divisions = new_divs
	return moves


func to_dict() -> Dictionary:
	return {"divisions": divisions, "you": you}


static func from_dict(d: Dictionary) -> RefCounted:
	var p = load("res://scripts/pyramid.gd").new()
	p.divisions = d.get("divisions", [])
	p.you = int(d.get("you", 0))
	if p.divisions.size() != NAMES.size():
		return create()
	return p
