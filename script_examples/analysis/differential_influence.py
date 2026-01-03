# Differential Influence
# Compare current board to previous board, and display
# the shifts in intersection control (aka ownership)

# This can show the impact of a single move
# over the whole board.

# NOTE: we need to play moves to see the effect
# initially because algo need boards to compare & contrast

persist("compareK", k)
persist("previousCompare", k)

# DELTA to view influence shifts
# not DELTA for traditional territory view
DELTA = check1("delta", default_value=True)

# mark intersections where player stole influence from
# opponent:
TRACK_STEALS = check2("track steals")

# show suggested moves by rank
SUGGEST = check3("suggest", default_value=False)
HELP = button1("help")

def ownership():
	"normal territory display"
	whiteSum = 0
	blackSum = 0
	for i in k.intersections:
		if i.ownershipWhite > 0.05:
			hover(i, f"W owns by {100*i.ownershipWhite:.2f}%")
			heat(i, 0.2)
			whiteSum  += i.ownershipWhite
		elif i.ownershipBlack > 0.05:
			hover(i, f"B owns by {100*i.ownershipBlack:.2f}%")
			heat(i, 0.75)
			blackSum += i.ownershipBlack
	
	log(f"White {whiteSum:.2f}")
	log(f"Black {blackSum:.2f}")
	
def delta(before: "KataAnswer", after: "KataAnswer"):
	"compare before with after for ownership shifts and display them."
	
	# gather stats along the way, why not?
	whiteTot = 0
	blackStrengthen = 0
	blackWeaken = 0
	whiteStrengthen = 0
	whiteWeaken = 0

	for i in after.intersections:
		p = before.get_point(i.pos)
		
		whiteChange = i.ownershipWhite - p.ownershipWhite
		blackChange = i.ownershipBlack - p.ownershipBlack

		whiteTot += whiteChange
		
		shift = 0
		shifter = None
		owner = None
		if whiteChange > 0.05:
			percent = round(i.ownershipWhite*1000)/10
			shift = round(whiteChange*1000)/10
			shifter = "W"
			if i.ownershipWhite > 0:
				whiteStrengthen += whiteChange
			else:
				blackWeaken += whiteChange
				
		elif blackChange > 0.05:
			percent = round(i.ownershipBlack*1000)/10
			shift = round(blackChange*1000)/10
			shifter = "B"
			if i.ownershipBlack > 0:
				blackStrengthen += blackChange
			else:
				whiteWeaken += blackChange

		if i.ownershipWhite > 0:
			owner = "W"
			percent = round(i.ownershipWhite*1000)/10

		if i.ownershipBlack > 0:
			owner = "B"
			percent = round(i.ownershipBlack*1000)/10
							
		if owner and shifter:
			if shifter == "B":
				heat(i, 0.7 + blackChange)
			else:
				heat(i, max(0.4 - whiteChange, 0.01))
			
			if TRACK_STEALS and shifter != owner:
				mark(i, "•")					
			
			hover(i, f"{shifter}{shift:+}%\n({owner} owns by {percent}%)")
	
	if whiteTot > 0:
		status(f"Influence Shift: W+{whiteTot:.2f}")
	elif whiteTot < 0:
		status(f"Influence Shift: B+{-whiteTot:.2f}")
	else:
		status(f"Influence Shift: B=W")

	log(f"Black Strengthen: {blackStrengthen:.2f}")
	log(f"White Strengthen: {whiteStrengthen:.2f}")
	log()
	log(f"Black Weaken:     {blackWeaken:.2f}")
	log(f"White Weaken:     {whiteWeaken:.2f}")
	
clearAll() ; clearLog()

if SUGGEST:
	for m in k.moves[:5]:
		mark(m, m.order+1)

if HELP:
	text = "White terri is orange, and black is blue.\n\n"
	text += "delta: show territorial shifts\n"
	text += "track steals: dot intersections where opponent was reduced\n"
	text += "suggest: suggest moves"
	msgBox(text)
	
if k.last_move:
	mark(k.last_move, "square")

if k.gui_run:
	# restore previous compareK because gui
	# use implies reinterpret, not different boards
	compareK = previousCompare

COMPARE = (compareK.thisHash != k.thisHash)
ESTABLISH = (k.depth == "full" and not k.gui_run)
	
if DELTA:
	if COMPARE:
		delta(compareK, k)
else:
	ownership()

if ESTABLISH:
	# save current position as next compare position
	previousCompare = compareK
	compareK = k
