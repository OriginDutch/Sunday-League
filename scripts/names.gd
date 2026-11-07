class_name Names
extends RefCounted
## Random people for the "Who can play for you" list, and friendly opponents.

const FIRST := ["Dave", "Gary", "Barry", "Kevin", "Steve", "Darren", "Lee", "Wayne", "Craig", "Neil",
	"Paul", "Mark", "Terry", "Dean", "Shane", "Jamie", "Ryan", "Callum", "Liam", "Kyle",
	"Trevor", "Colin", "Keith", "Ian", "Phil", "Rob", "Danny", "Jordan", "Nathan", "Tony"]
const LAST := ["Smith", "Jones", "Taylor", "Brown", "Wilkins", "Hughes", "Parker", "Turner", "Cooper",
	"Walsh", "Bennett", "Dawson", "Fletcher", "Hodges", "Pratt", "Booth", "Simms", "Rudd", "Pike",
	"Clegg", "Haynes", "Mott", "Butcher", "Baker", "Fowler", "Platt", "Stubbs", "Crouch", "Dunn", "Ball"]
const NICK := ["Big", "Little", "Old", "Mad", "Young", "Fat", "Lanky", "Slow", "Posh"]
const ORIGINS := ["Regular at the pub", "Neighbour across the road", "Your cousin", "Kid from the street",
	"Guy from the supermarket", "Your postman", "Plays five-a-side on Tuesdays", "Your uncle",
	"Bloke from the chippy", "Window cleaner", "Your mate's flatmate", "Dog walker from the park",
	"Retired PE teacher", "Builder next door", "Says he had a trial at Stoke"]
const OPP_A := ["Red Lion", "Dog & Duck", "Station Road", "St. Barnaby's", "Kings Arms", "Mill Lane",
	"Railway Tavern", "Crown & Anchor", "Elm Park", "Gasworks", "Bridge Street", "Old Bell",
	"White Hart", "Plough Inn", "Canal Side", "Royal Oak", "Hollybush", "Brewery Lane", "Coach & Horses",
	"Chapel End", "Rose & Crown", "Fox & Hounds", "Park View", "Quarry Road"]
const OPP_B := ["XI", "FC", "Athletic", "Old Boys", "Rovers", "United", "Wanderers", "Casuals"]


static func person() -> Dictionary:
	var first: String = FIRST.pick_random()
	var name := "%s %s" % [first, LAST.pick_random()]
	if randf() < 0.18:
		name = "%s %s" % [NICK.pick_random(), first]
	return {"name": name, "origin": ORIGINS.pick_random()}


## A league opponent whose first part isn't taken yet (keeps 19 teams distinguishable).
static func opponent_unique(used: Dictionary) -> String:
	var free: Array = OPP_A.filter(func(a): return not used.has(a))
	var a: String = free.pick_random() if not free.is_empty() else OPP_A.pick_random()
	used[a] = true
	return "%s %s" % [a, OPP_B.pick_random()]


static func opponent() -> String:
	return "%s %s" % [OPP_A.pick_random(), OPP_B.pick_random()]
