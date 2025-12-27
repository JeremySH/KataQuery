# Style Bots
# pick what style you want KataGo to play

STYLE_HELP = """
Do Your Best -- pick best move
Bully Me     -- threaten "just because"
Seek Peace   -- prefer calm results
Invade Me    -- play near/inside opponent terri
Get Thick    -- play near/inside own terri
Be Greedy    -- stretch to unclaimed areas
Be Weird     -- wakka wakka bweeet
Fight Me     -- prefer lots of local fighting

Safety Level -- lower values mean weaker but more style

"""

persist("style", "Do Your Best")
SHOW_HELP = check1("Show Help")
SHOW_BEST = check2("Show Best")

SAFETY  = slider1("Safety Level", default_value=0.8)

BEST    = button1("Do Your Best")
BULLY   = button2("Bully Me")
NICE    = button3("Seek Peace")
INVADE  = button4("Invade Me")
THICKEN = button5("Get Thick")
EXPAND  = button6("Be Greedy")
WEIRD   = button7("Be Weird")
TENUKI  = None # button8("Mr. Tenuki")
FIGHT   = button8("Fight Me")

if INVADE:  style = "Invade Me"
if BULLY:   style = "Bully Me"
if EXPAND:  style = "Be Greedy"
if THICKEN: style = "Get Thick"
if BEST:    style = "Do Your Best"
if NICE:    style = "Seek Peace"
if WEIRD:   style = "Be Weird"
if TENUKI:  style = "Mr. Tenuki"
if FIGHT:   style = "Fight Me"

def bestByFilter(ans, filt):
	df = k.as_dataframe
	df = df.query("isMove")
	df = df.query(filt)	
	df = df.sort_values("mergedOrder")
	df = df.head()
	
	for m in df['info']: # just to acces the series
		if isSafe(ans, m):
			if ans.bestMove.pos != m.pos:
				log("lemme try this...")
			return m
		break
	
	log("Picking a safe move.")
	
	return ans.bestMove

def criticality(ans):
	"measure median winrate devation from the top move"
	from statistics import median
	if len(ans.moves) <= 1:
		#log("not enough moves:")
		return 0

	byWinrate = sorted(ans.moves, key=lambda m: -m.winrate)
	wrs = [w.winrate for w in byWinrate]
	top = max(wrs)
	
	# treat the top move as the "standard"
	# and compare all other values to it
	dev = [top-w for w in wrs[1:]]
	
	med = median(dev)

	return med

def criticalityPoints(ans):
	"measure median scoreLead deviation from the top move"
	from statistics import median
	if len(ans.moves) <= 1:
		return 0

	maxLead = ans.bestMove.scoreLead
	deviation = [maxLead - m.scoreLead for m in ans.moves[1:]]
	med  = median(deviation)
	#print("criticality points: ", med)
	return med

def fightValue(m):
	"scores moves by how much local play they provoke."
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

def isSafe(ans, move):
	#if criticalityPoints(ans) > 10: return False
	#if criticality(ans) > 0.09: return False
	#print("crit points: ", criticalityPoints(ans))
	risk = 1-SAFETY
	if ans.bestMove.winrate - move.winrate > 0.15 * risk: 
		return False
	if ans.bestMove.scoreLead - move.scoreLead > 25*risk: 
		return False

	return True

def bullyMove(ans, max_depth=6, invert=False):
	"return a safe-ish move that does the  most bullying"
	import random
	
	# some random comments to make when style is used
	comment = random.choice(["Bwaahaahaa!", "Hyah!!", "BAM!", "Just tenuki and see what happens 😏"])
	if invert:
		comment = random.choice(["What a beautiful day.", "Let's relax.", "Go is so calming.", "I'm feeling cozy.", "The persuit of peace enobles a man."])
	
	test = lambda a, b: a > b
	if invert: 
		test = lambda a, b: a < b
	
	# try some plays to determine max point threat,
	# and use this info to get "war" or "peace" move
	#log("thinking...")
	futures = []
	for m in k.moves[:max_depth]:
		g = k.goban.copy()
		g.play(k.toPlay, m.coords);
		g.toPlay = opponent(g.toPlay)
		analysis = analyze(g, visits=20)
		#log(f"future length: {len(analysis.moves)}")			
		futures.append((m, analysis))
		
	bestCrit = 0
	if invert: bestCrit = 100
	
	bestMove = k.bestMove
	for m, future in futures:
		#log(f"win drop: {k.winrate - future.winrateOpponent}") 
		if k.winrate - future.winrateOpponent > 0.03: 
			#log(f"{m.coords} win drop too big: {k.winrate - future.winrateOpponent}") 
			break

		crit = criticality(future)
		#log(m.move, f"criticality: {crit}")
		if test(crit ,bestCrit): 
			bestCrit = crit
			bestMove = m

	if ans.bestMove.pos != bestMove.pos:
		log(comment)

	return bestMove

def weirdMove(ans, max_dist=3):
	"pick a move further away from best move, which leads to weird stuff"
	import random
	comment = random.choice(["Woohoo!", "Let's get SPICY!", "I so clever!", "Oooh let me try this!"])

	if not ans.last_move:
		return ans.bestMove

	focusMove = random.choice([ans.bestMove, ans.last_move])
	moves = [m for m in ans.moves if dist(m, focusMove) < max_dist]
	moves = sorted(moves, key=lambda m: -dist(m, focusMove))
	#print([dist(m, ans.bestMove) for m in moves])
	#print(k.map("(m.winrate, m.coords)", moves))
	#print(k.map("m.coords", k.moves))
	for m in moves:
		if isSafe(ans, m):
			if m.pos == ans.bestMove.pos:
				log("meh.")
			else:
				log(comment)
			return m

	log(f"*sigh*")
	return ans.bestMove

def fightMove(ans):
	moves = sorted(ans.moves, key=lambda m: -fightValue(m))
	for m in moves:
		if isSafe(ans, m):
			if ans.bestMove.pos == m.pos:
				log("playing it straight.")
			else:
				log("let's fight!")
			return m

	log("playing safer best move")
	return ans.bestMove

def marky(move):
	mark(move, "square")
	ghost(move, k.toPlay)

clearAll()
clearLog()
log(f"Style:        {style}")
log(f"Safety Level: {SAFETY*100:0.1f}\n")

if k.depth == "quick": 
	if SHOW_HELP: log(STYLE_HELP)
	bail()

if style == "Do Your Best":
	marky(k.bestMove)
elif   style == "Invade Me":
	marky(bestByFilter(k, "legal and ownershipOpponent > 0.4"))
elif style == "Bully Me":
	marky(bullyMove(k))
elif style == "Be Greedy":
	marky(bestByFilter(k, "legal and abs(ownership) < 0.4"))
elif style == "Get Thick":
	marky(bestByFilter(k, "legal and ownership > 0.099"))
elif style == "Seek Peace":
	marky(bullyMove(k, invert=True))
elif style == "Be Weird":
	marky(weirdMove(k))
elif style == "Mr. Tenuki":
	marky(weirdMove(k, 100))
elif style == "Fight Me":
	marky(fightMove(k))
	
# mark(k.bestMove, "square")

if SHOW_HELP:
	log(STYLE_HELP)
	
if SHOW_BEST:
	mark(k.bestMove, "B")
