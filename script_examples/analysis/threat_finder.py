# Threat Finder
# Find threats and mark by points threatened.
# If the threat amount is ko-like (exceeds current board value), 
# highlight it.

# Use CMD-R to search for more threats

# GUI controls:
# "Ranks"     -- show threat ranks instead of points
# "Max Shown" -- tweak the max amount of threats shown

# "Threats" are sorted by how many points the player gets
# if opponent ignores the move. Thus, threats can
# be territory grabs, they don't have to be local sente

persist("boardValue", None)
persist("threats", {})
persist("lastHash", None)

SHOW_RANKS = check1("Ranks")
MAX_SHOWN = int(dial1("Max Shown", max_value=300, default_value=10))
INIT_VISITS = 5
STEP_VISITS = 50

def calcBoardValue(ka):
	"calculate points at stake on board for katanswer object"
	mePass = quickPlay(ka, [[ka.player, "pass"]])

	board_value = abs(ka.scoreLeadWhite - mePass.scoreLeadWhite)/2
	return board_value


def calcThreat(m):
	future = quickPlay(k, [[k.player, m.coords], [opponent(k.player), "pass"]])
	return (future.scoreLead - k.scoreLead)/2	

def grabThreats(visits):
	"grab visits many threats and add them to threats dict"
	i = 0
	for m in k.moves_by_policy:
		if m.pos not in threats:
			i += 1
			if i > visits: break
			val = calcThreat(m) 
			threats[m.pos] = val

if k.depth == "full":
	clearAll()
	if lastHash == None or lastHash != k.thisHash:
		lastHash = k.thisHash
		boardValue = calcBoardValue(k)
		threats = {}
		grabThreats(INIT_VISITS)

	if k.manual_run:
		grabThreats(STEP_VISITS)

	tlist = sorted(list(threats.items()), key=lambda x: -x[1])
	
	i = 0
	for pos, val in tlist[:MAX_SHOWN]:
		i += 1
		if SHOW_RANKS:
			mark(pos, i)
		else:
			mark(pos, round(val*10*2)/10, scale=.9)
		if val > boardValue:
			heat(pos, 1)
	clearLog()
	log(f"Max Moves shown:  {MAX_SHOWN}")
	log(f"Threats searched: {len(threats)}/{len(k.legal_moves)}")

bv_rounded =	round(boardValue*10)/10
bv_doubled = round(boardValue*20)/10

status(f"{k.player} to play \
	| board value: {bv_rounded} ({bv_doubled}) \
	| threats searched: {len(threats)}/{len(k.legal_moves)}")
