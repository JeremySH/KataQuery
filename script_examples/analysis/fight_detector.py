# Fight Detector
# fighting moves marked with squares
# uses gui to set thresholds

FIGHT_THRESHOLD = slider1("Fight Thresh", default_value=0.2)
SHOW_RANKS = check1("Show Ranks")
MAX_MOVES = slider2("Max Moves", max_value=30, default_value=12.0)
MAX_MOVES= int(MAX_MOVES)

clearLog()
log(f"Fight Threshold : {FIGHT_THRESHOLD}")
log(f"Max moves       : {MAX_MOVES}")

def dist(p1, p2):
	"return the manhattan distance between two points"
	return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def fightValue(movelist):
	global dist
	if len(movelist) < 2: return 0

	m = movelist[0]
	d = 0
	for p in movelist:
		d += dist(m, p)
		m = p

	return len(movelist)/float(d)

clearAll()
if SHOW_RANKS:
	for m in k.moves[:MAX_MOVES]:
		mark(m, m.order+1)
maxfight = 0
for m in k.moves[:MAX_MOVES]:
	fv = fightValue(m.pvPos)
	if fv > FIGHT_THRESHOLD:
		mark(m, "square", scale=0.5+fightValue(m.pvPos))
		maxfight = max(maxfight, fv)
	
status(f"{k.toPlay} to play | Fight Value: {maxfight}")

