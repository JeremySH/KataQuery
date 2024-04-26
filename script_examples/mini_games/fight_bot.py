# FIGHT BOT
# play against a KataGo that prefers fighting

# calculate a "fight value" which is len(pv)/(total distance)
# assuming that a lot of local plays means "fight"

myColor = "black"
cheat = False

BOTH_SIDES = False # katago plays both sides?

def dist(p1, p2):
	"return the manhattan distance between two points"
	return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def fightValue(movelist):
	"calculate the fightValue (len(pv)/total_dist)"
	global dist
	if len(movelist) < 2: return 0

	m = movelist[0]
	d = 0
	for p in movelist:
		d += dist(m, p)
		m = p
	return len(movelist)/float(d)

clearAll()
best_value = None
best_move = k.bestMove
if k.depth == 'full':
	best_value = 0
	for m in k.moves:
		if m.pos[0] < 0: continue # skip pass

		#protect from self-harm:
		if k.winrate - m.winrate > 0.01: continue
		f = fightValue(m.pvPos)
		if f > best_value:
			best_move = m
			best_value = f
	best_value = round(best_value*100)/100

if BOTH_SIDES or k.toPlay != myColor:
	mark(best_move, "●")
elif cheat:
	for m in k.moves: mark(m)

if k.toPlay == myColor:
	status(f"Your play ({k.toPlay})")
else:
	status(f"My play ({k.toPlay} | fight value = {best_value})")
