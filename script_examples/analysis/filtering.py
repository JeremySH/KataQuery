# Filtering
# Filtering is a powerful teaching tool
# because it forces KataGo to suggest plays
# by subject matter.

# Use buttons to set the mode,
# dials to adjust thresholds, etc

TERRI = check1("terri")

TERRI_THRESH = slider1("Terri. Threshold", min_value=0.01, default_value=0.1)
MOVES_MAX = slider2("Moves", min_value=1, max_value=30, default_value=5, value_type="int")
FIGHT_THRESH = slider3("Fight Value", default_value=0)
DISPLAY = slider4("Display", min_value=0, max_value=5, default_value=0, value_type="int")

BEST = button1("Best")
INVADE = button2("Invade")
STRENGTHEN = button3("Thicken")
EXPAND = button4("Expand")
HELP = button5("Help")

# The filter and mode we use
persist("filt", "legal")
persist("kind", "best")

def fightValue(m):
	"scores move m by how much local play it provokes."
	if not m.isMove: return 0
	if len(m.pv) < 2: return 0
	
	length = len(m.pv)
	distance = 0
	current = m.pos
	for p in m.pvPos:
		distance += dist(current, p)
		current = p
	
	if distance:
		return length/distance
	else:
		return 0

def threatValue(m):
	"return the raw point gain of this move"
	if not m.legal: return 0
	
	g = k.goban.copy()
	g.play(g.toPlay, m.pos)
	answer = analyze(g)

	return answer.scoreLead - k.scoreLead

def showHelp():
	txt = "HELP\n----\n"
	txt += "this script filters move choice by purpose.\n\n"
	txt += "Choose a move purpose:\n"
	txt += "Best:       show best moves\n"
	txt += "Invade:     show top moves inside enemy territory\n"
	txt += "Thicken:    show top moves inside own territory\n"
	txt += "Expand:     show top moves in unclaimed areas\n\n"
	
	txt += "TERRI THRESH: ownership confidence.\n"
	txt += "FIGHT VALUE:  filter for fighting moves.\n"
	txt += "MOVES:        show more/less moves.\n"
	txt += "DISPLAY:      change what numbers to display\n\n"
	txt += "Check TERRI to show territory prediction.\n"
	
	clearLog()
	msgBox(txt)

def markTitle(title):
    "mark `title` at bottom of board"
	mark((k.xsize//2, -0.5), title)

if HELP:
	showHelp()
	bail()
	
# set up filter
if INVADE:
	kind = "invade"
	filt = "legal and ownershipOpponent > @TERRI_THRESH"
elif STRENGTHEN:
	kind = "thicken"
	filt = "legal and ownership > @TERRI_THRESH"
elif EXPAND:
	kind = "expand"
	filt = "legal and abs(ownership) < @TERRI_THRESH"
elif BEST:
	kind = "best"
	filt = "legal"

DISP = ["rank", "winrate", "point lead", "policy", "point threat", "fight value"][DISPLAY]	
clearAll()
clearLog()

log("Mode:                ", kind)
log("Display:             ", DISP)
log("Move Limit:          ", MOVES_MAX)
log("Teritory Threshold:  ", TERRI_THRESH)
log("Fight Value:         ", FIGHT_THRESH)
log("Visits:              ", k.visits)

# now do the actual filtering
df = k.dataframe
df['fight'] = df['info'].apply(fightValue)

df = df.query(filt)

df = df.query("fight >= @FIGHT_THRESH")
df = df.sort_values("mergedOrder")
df = df.head(MOVES_MAX)

# display moves
markTitle(f"{kind} moves, by {DISP}")
for i, m in enumerate(df['info']):
	scale = 1
	if m.isMove:
		scale = 1.35

	if DISP== "rank": 
		mark(m, m.mergedOrder+1)
	elif DISP == "winrate":
		if m.isMove:
			mark(m, f"{m.winrate*100:0.0f}")
		else:
			mark(m, "?")
	elif DISP== "point lead": 
		if m.isMove:
			mark(m, f"{m.scoreLead:0.1f}")
		else:
			mark(m, "?")
	elif DISP == "policy": 
		mark(m, f"{m.policy*100:0.1f}")
	elif DISP == "point threat":
		mark(m, round(threatValue(m)), scale=scale)
	elif DISP == "fight value":
		mark(m, round(fightValue(m)*100), scale=scale)
	else:
		mark(m, i+1, scale=scale)

# show territory
if TERRI:
	for i in k.intersections:
		if i.ownershipWhite > TERRI_THRESH:
			heat(i, .01)
		if i.ownershipBlack > TERRI_THRESH:
			heat(i, 1)