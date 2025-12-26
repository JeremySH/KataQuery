# Joseki Explorer
# Focus on a corner of the board
# and provide features useful
# for studying AI joseki

# recommended:
# Localize: NONE
# Neural Nets: PURE

# NOTE: GUI is a bit finicky, so you may have to click some settings on and off
# to get them activated


HIDE = check1("hide")

# focus on quadrant?
FOCUS = check2("quad focus", default_value=True)

# show continuation as ghost stones?
SEQUENCE = check3("sequence")

# scale letter labels by policy-calculated knowledge?
KNOWLEDGE_SCALE = check4("knowledge", default_value=True)

# use only policy to generate sequences?
POLICY_ONLY = check5("policy only")
TENUKI_ALERTS = check6("tenuki alerts")
HOVER_TEXT = check7("hover text", default_value=True)

PREV = button1("◀︎ Seq")
NEXT = button2("Seq ▶︎")
HELP = button3("Help")
Q_MINUS = button5("◀︎ Quad")
Q_PLUS = button6("Quad ▶︎")

persist("MOVERANK", 1)
persist("QUADRANT", 0)

# FUNCTIONS
# separated because they could be 
# useful elsewhere

def quad_points(quadrant: int) -> list:
	"return all the points in the provided quadrant 0-3"
	QUADS = [
		[(k.xsize//2, k.xsize), (k.ysize//2, k.ysize)],
		[(k.xsize//2, k.xsize), (0, k.ysize//2+1)],
		[(0, k.xsize//2+1), (0, k.ysize//2+1)],
		[(0, k.xsize//2+1), (k.ysize//2, k.ysize)],
	]
	
	quad = QUADS[quadrant]
	
	quad_places = []
	xs = quad[0]
	ys = quad[1]
	for x in range(min(xs[0], xs[1]), max(xs[0], xs[1])):
		for y in range(min(ys[0], ys[1]), max(ys[0], ys[1])):
			quad_places.append( (x, y,) )
	return quad_places

def known(m, ans=k, allowed=None):
	"return a stable score for how known this move is, given KataAnswer ans."
	allowed_moves = ans.legal_moves
	if allowed:
		allowed_moves = allowed
	s = sum(p.policy for p in allowed_moves)	
	return len(ans.legal_moves) * m.policy/s

def hoverText(m, ans=k):
	"create hover text for this move, given KataAnswer ans"
	t = f"{m.coords}\n"
	if m.isMove:
		t += f"WINRATE:   {round(m.winrate*1000)/10}\n"
		t += f"SCORELEAD: {round(m.scoreLead*10)/10}\n"
	
	t += f"FAMILIAR: {round(known(m, ans))}"
	hover(m, t)

def labels(ans, limit=10, policy=False, focus_on=None):
	"mark suggested moves using ranked letters"
	# moves by rank (A,B,C)
	letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
	merged = ans.moves
	
	if policy:
		selection = ans.legal_moves
		if focus_on:
			selection = [ans.get_point(m) for m in focus_on]
			selection = [m for m in selection if m.legal]
		merged = sorted(selection, key=lambda m: m.mergedOrder)

	index = 0
	# known() needs moveInfos, not tuples
	allowed = ans.legal_moves
	if focus_on:
		allowed = [ans.get_point(m) for m in focus_on]
		allowed = [m for m in allowed if m.legal]
	
	for m in merged:
		s = 1.0
		if KNOWLEDGE_SCALE:
			s = 0.75 + min(known(m, ans, allowed)/100, 3.0)
			
		mark(m, letters[index], scale=s)
		if HOVER_TEXT:
			hoverText(m)
		
		index +=1
		if index >= limit: break

def focus(prev, new, hops=3):
	"return union of prev points and new + 3 hops"
	fresh = list(new)

	for _ in range(hops):
		fresh = k.goban.nearby_these(fresh)
	
	return set(fresh).union(set(prev))

def sequence_policy(ans, focus_on=None, rank=1, length=10):
	"generate moves within focus_on using only policy net"
	res = ans
	g = ans.goban.copy()
	prevPoints = None
	plays = []
	for x in range(length):
		if focus_on:
			allowed = focus(QUAD_ALLOWED, plays)
		else:
			allowed = None
			
		res = analyze(g, allowedMoves=allowed)
		
		candidates = []
		if allowed:
			for m in allowed:
				if m not in plays and res.get_point(m).legal:
					candidates.append(res.get_point(m))
			candidates = sorted(candidates, key=lambda m: -m.policy)
		else:
			candidates = res.moves_by_policy
		
		best = candidates[0]
		
		if x == 0:
			i = min(rank-1, len(candidates))
			best = candidates[i]
		
		g = res.goban
		ghost(best, g.toPlay)
		mark(best, x+1)
		if HOVER_TEXT:
			hoverText(best)

		plays.append(best.pos)

		#snooze(0.2)
		g.play(g.toPlay, best.pos)
		g.toPlay = opponent(g.toPlay)		

	return res

def sequence (ans, focus_on=None, rank=1):
	"generate and show sequence as ghost stones"
	res = ans
	g = ans.goban.copy()
	prevPoints = None
	plays = []
	allowed = focus_on
	
	for x in range(10):
		if focus_on:
			allowed = focus(focus_on, plays)
			
		if x == 0:
			# need more visits to get move ranks
			res = analyze(g, allowedMoves=allowed, visits=k.visits)
		else:
			res = analyze(g, allowedMoves=allowed, visits=4)
	
		best = res.bestMove
		if x == 0:
			candidates = sorted(res.allowed_moves, key=lambda m: m.mergedOrder)
			i = min(rank-1, len(candidates)-1)
			best = candidates[i]
		
		g = res.goban
		ghost(best, g.toPlay)
		mark(best, x+1)
		if HOVER_TEXT:
			hoverText(best)

		plays.append(best.pos)

		#snooze(0.2)
		g.play(g.toPlay, best.pos)
		g.toPlay = opponent(g.toPlay)

	return res

# MAIN PROGRAM
clearAll()
clearLog()
if HELP:
	log("HELP:")
	log("""
	hide:            display nothing
	quad focus:      only moves in the chosen quad
	sequence:        show expected sequence
	knowledge:       scale labels by KataGo's confidence
	◀︎ ▶︎ :            cycle through sequences & quads
	policy only      generate sequences with only policy values
	tenuki alerts    mention when tenuki may be OK
	""")
	log("NOTE: KataGo always sees the whole board, so joseki choice\ncan be influenced by remote stones/empty corners.\n")


if HIDE: bail()

# browse possible continuations
if PREV:
	MOVERANK = max(MOVERANK - 1, 1)
if NEXT:
	MOVERANK = min(MOVERANK + 1, 10)

# change the focused quadrant
if Q_MINUS:
	QUADRANT = (QUADRANT + 3) % 4

if Q_PLUS:
	QUADRANT = (QUADRANT + 1) % 4

# disable/enable focus
if FOCUS:
	QUAD_ALLOWED = quad_points(QUADRANT)
else:
	QUAD_ALLOWED = None

log("Quadrant: ", QUADRANT+1)
log(f"First Move Rank: {MOVERANK}")

# show last move
if k.last_move:
	mark(k.last_move, "●")

# rank moves with ABC...
if k.depth == "quick":
		labels(k, policy=True, focus_on=QUAD_ALLOWED)
else:
	if not SEQUENCE: # don't show letters if sequence is used
		if POLICY_ONLY:
			labels(k, policy=True, focus_on=QUAD_ALLOWED)
		else:
			ans = analyze(k.goban, allowedMoves=QUAD_ALLOWED, visits=k.visits)
			labels(ans, policy=False, focus_on=QUAD_ALLOWED)
	
# check tenuki, say so in log
if QUAD_ALLOWED and TENUKI_ALERTS:
	tenuki = k.moves_by_policy[0].pos not in QUAD_ALLOWED
							
	if tenuki:
		log(f"\n{k.toPlay.capitalize()} can tenuki.")
		mark((k.xsize//2, -0.5), f"{k.toPlay.capitalize()} can tenuki.")


# don't do deep analysis if quick
if k.depth == "quick":
	bail()

def wrText(ans):
	return f"B {round(ans.winrateBlack*1000)/10} W {round(ans.winrateWhite*1000)/10}"

# generate sequence display and show winrates
seqWinrateText = ""
res = None
if SEQUENCE:
	if POLICY_ONLY:
		res = sequence_policy(k, focus_on=QUAD_ALLOWED, rank=MOVERANK)		
		seqWinrateText = "| after sequence: " + wrText(res)
	else:
		res = sequence(k, focus_on=QUAD_ALLOWED, rank=MOVERANK)
		seqWinrateText = "| after sequence: " + wrText(res)

status(f"Winrates: {wrText(k)} {seqWinrateText}")

log(f"\nWinrates: {wrText(k)}")
if res:
	log(f"|    SEQ: {wrText(res)}")
