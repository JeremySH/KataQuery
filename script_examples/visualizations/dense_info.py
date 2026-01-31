# DENSE INFO
# information gluttony

HIDE =         check1("hide")
DO_TERRI =     check2("terri", default_value=False)
DO_LND =       check3("life")
DO_THICKNESS = check4("thickness")
DO_HOVER =     check5("hover text", default_value=True)
DO_VITALS =    check6("vitals", default_value=True)
DO_PV =        check7("PV")

TERRI_THRESHOLD = dial1("Terri Thresh", default_value=0.02)
VITAL_THRESHOLD = dial2("Vital Thresh", default_value=0.09)
MOVE_COUNT =      dial3("Moves Shown", default_value=5, min_value=0, max_value=20, value_type = 'int')
PV_VARIATION =    dial4("PV variation", default_value=0, max_value=8, value_type="int")
DISPLAY_MODE =    dial5("Display Mode",  default_value=0, max_value=4, value_type="int")
DEEP_VISITS =     dial6("Deep visits", default_value=5000, max_value=50000, min_value=1000, value_type = 'int')

DISP_MODE = ["bubble", "move rank", "winrate", "points", "policy"][DISPLAY_MODE]

CRITICALITY = button1("Criticality")
DREAM_BLACK = button2("Black Dreams")
COPY_SGF    = button3("Copy SGF")
PASTE_SGF   = button4("Paste SGF")
DREAM_WHITE = button6("White Dreams")

SENTES      = button5("Sentes")
SENTE_THRESHOLD = 0.05

GO_DEEP     = button7("Go deep")
SAVE_SGF    = button8("Save SGF")

def terri(threshold=0.02, show=True):
	"show KataGo's guess of territory"
	terriWhite = 0
	terriBlack = 0

	for i in k.intersections:
		if i.ownershipBlack > threshold:
			if show:
				heat(i.pos, 0.75)
			terriBlack += 1
		if i.ownershipWhite > threshold:
			if show:
				heat(i.pos, 0.25)
			terriWhite +=1
	return terriBlack, terriWhite

def life_and_death(ans):
	"mark life, death and questionable status of stones in ans"
	for i in ans.stones:
		if i.color == "white" :
			if i.ownershipWhite < 0:
				mark(i.pos, "x")
			elif i.ownershipWhite < 0.5:
				mark(i.pos, "?")
		else:
			if i.ownershipBlack < 0:
				mark(i.pos, "x")
			elif i.ownershipBlack < 0.5:
				mark(i.pos, "?")

def criticality(ans, by_points=False):
	"measure median winrate devation from the top move"
	from statistics import median
	if len(ans.moves) <= 1:
		return 0

	# limit to 20 so that very bad moves don't skew
	
	if by_points:
		byPoints = ans.sorted("-m.scoreLead", ans.moves[:20])
		data = [w.scoreLead for w in byPoints]
	else:
		byWinrate = ans.sorted("-m.winrate", ans.moves[:20])
		data = [w.winrate for w in byWinrate]
	
	top = max(data)
	
	# treat the top move as the "standard"
	# and compare all other values to it
	dev = [top-w for w in data[1:]]
	
	med = median(dev)

	return med

def vital_points(ans, threshold=9.0, by_points=False):
	"""
	return (criticality, vital_points).
	where criticality is the winrate loss risk
	and vitals are a list of must-play moves (if any)
	"""
	crit = criticality(ans, by_points=by_points)
	vits = []
	if by_points:
		if crit > threshold:
			count = 0
			maxp = ans.max("m.scoreLead", ans.moves).scoreLead
			for m in ans.moves:
				if maxp - m.scoreLead < threshold/3:
					vits.append(m)
					count += 1
					if count > 2:
						break
	else:
		if crit > threshold:
			count = 0
			maxwin = ans.max("m.winrate", ans.moves).winrate
			for m in ans.moves:
				# presuming that 1/3rd of threshold is all we can bear
				if maxwin - m.winrate < threshold/333:
					vits.append(m)
					count += 1
					if count > 2:
						break
				else:
						break
	
	return crit, vits

def points_at_stake(ans):
	"determine score change when I pass "
	mePass = quickPlay(ans, [[ans.player, "pass"]])

	board_value = abs(ans.scoreLeadWhite - mePass.scoreLeadWhite)/2
	board_value = round(board_value*10)/10.0
	return board_value

def score(ans, thresh=0.5):
	"return the predicted territory for (black, white)"
	b = ans.filter(f"m.ownershipBlack > {thresh}")
	w = ans.filter(f"m.ownershipWhite > {thresh}")

	return b, w

def obviousness(ans, aMove):
	"how obvious (to KataGo) is this move? approx range: 0-350"
	sumPol = sum(m.policy for m in ans.moves_by_policy if m.allowedMove)
	return len(ans.legal_moves) * aMove.policy/sumPol

def thickness(ans):
	"how much does ownership support the stone upon it?"
	# goes from -10 (dead) to 10 (immortal)
	# middle is taken at self-ownership of 0.5 instead of 0.0
	# because < 0.5 ownership of your own stone
	# means it's weak
	for stone in k.stones:
		if stone.color == "black":
			thick = stone.ownershipBlack
		else:
			thick = stone.ownershipWhite
		
		if thick > 0.5:
			thick = (thick - 0.5)/0.5
		else:
			thick = (thick - 0.5)/1.5
	
		mark(stone, round(thick*10))
		
def moves(ans, display_mode="bubble", limit=100):
	"mark the suggested moves using the Display Mode chosen."
	count = len(ans.moves)
	if display_mode == "policy":
		for m in ans.merged_moves[:limit]:
			if m.allowedMove:
				mark(m, f"{m.policy*100:0.0f}", scale=1)
		return

	if display_mode == "move rank":
		for m in ans.merged_moves[:limit]:
			if m.allowedMove:
				if m.isMove:
					mark(m, m.order+1, scale=1 + m.visits/(ans.visits/2))				
				else:
					mark(m, m.mergedOrder+1, scale=1)
		return

	for m in ans.moves[:limit]:
		if display_mode == "bubble":
			#mark(m, "circle", scale=0.75 + (count-m.order)/count)
			mark(m, "⃝", scale=0.75 +  m.visits/(ans.visits/2))
		elif display_mode == "winrate":
			mark(m, f"{m.winrate*100:0.0f}", scale=1)
		elif display_mode == "points":
			mark(m, f"{m.scoreLead:0.1f}", scale=0.9)
		else:
			mark(m, "⃝", scale=0.75 +  m.visits/(ans.visits/2))
				
def hovertext(ans, limit=100):
	"build and set hovertext for displayed moves"
	txt = ""
	allmoves =  k.sorted("m.mergedOrder", k.legal_moves)

	for m in allmoves[:limit]:
		txt = str(m.coords) + f" (rank: #{m.mergedOrder+1})\n"
		
		if not m.isMove:
			txt += f"policy:      {m.policy*100:0.2f}%\n"
			txt += f"obvious:     {round(obviousness(ans,m))}\n"
		else:		
			txt += f"winrate:     {m.winrate*100:0.1f}%\n"
			txt += f"score:       {m.scoreLead:0.1f}\n"
			txt += f"WR loss:     {(ans.bestMove.winrate-m.winrate)*100:0.1f}%\n"
			txt += f"score loss:  {(ans.bestMove.scoreLead - m.scoreLead):0.1f}\n"
			txt += f"policy:      {m.policy*100:0.2f}%\n"
			txt += f"obvious:     {round(obviousness(ans,m))}\n"
			txt += f"visits:      {m.visits}/{k.visits} ({round(100*m.visits/k.visits)}%)\n"
			txt += f"uncertainty: {(m.winrate-m.lcb)*100:0.1f}%\n\n"
			
		hover(m.pos, txt)

def pvDisplay(ans, moveNum):
	"""
	show the likely continuations with ghost stones
	where moveNum is the rank of the starter move
	"""
	if moveNum > len(ans.moves):
		return
	
	player = ans.player
	for i, m in enumerate(ans.moves[moveNum].pvPos):
		ghost(m,player)
		mark(m, i+1)
		player = opponent(player)

def markSentes(ans):
	"detect which available moves are also sente"
	found = False
	crit = criticality(ans)
	for m in ans.moves[:8]:
		g = ans.goban.copy()
		g.play(g.player,m)
		g.player = opponent(g.player)
		ans2 = analyze(g, visits=20)
		crit2 = criticality(ans2)
		#if crit2 > crit:
		if crit2 > SENTE_THRESHOLD:
			mark(m, "S")
			found = True
	if not found:
		log("No Sente found...")

def getSGF(ans, collapsed=False):
	"""
	get the current position as an SGF string.
	if `collapsed`, convert stones to placements 
	in a single node, instead of plays
	"""
	
	g = ans.goban.copy()
	if collapsed:
		g.collapse()
	
	return g.as_sgf()
	
def main_stuff ():
	"do main markings"
	clearAll()
	
	mark(k.last_move, "●") 
	mark(k.ko, "Ko", scale=0.75)

	if HIDE:
		b,w = score(k, TERRI_THRESHOLD)
		return (len(b), len(w))
	
	blackScore, whiteScore = terri(TERRI_THRESHOLD, DO_TERRI)

	moves(k, DISP_MODE, limit=MOVE_COUNT)
	
	if DO_VITALS:
		crit, vitals = vital_points(k, VITAL_THRESHOLD)
	else:
		crit = criticality(k)
		vitals = []
	
	if DO_LND:
		life_and_death(k)
	
	if DO_THICKNESS:
		thickness(k)
	

	if DO_PV:
		pvDisplay(k, PV_VARIATION)
	
	if DO_HOVER:
		hovertext(k, limit=MOVE_COUNT)

	BOTTOM_COMMENT = ""
	
	if len(vitals):
		for v in vitals:
			mark(v, "♢", scale=1+v.visits/k.visits)
		BOTTOM_COMMENT += f"♢ VITALS BY {crit*100:0.1f}%"
	
	if k.depth == "full":
		stake = points_at_stake(k)
		if len(BOTTOM_COMMENT) > 0:
			BOTTOM_COMMENT += " | "
		
		BOTTOM_COMMENT += f"Points At Stake: {stake:0.1f}"
	
	mark((k.xsize//2, -0.5), BOTTOM_COMMENT)
	return blackScore, whiteScore

def button_stuff():
	"handle button presses"
	if CRITICALITY:
		msgBox(f"Criticality: {100*criticality(k):.1f}")
	
	if DREAM_WHITE or DREAM_BLACK:
		player = "black"
		if DREAM_WHITE:
			player = "white"
	
		g = k.goban.copy()
		g.player = player
		ans = k
		for x in range(5):
			ghost(ans.bestMove, g.player)
			mark(ans.bestMove, f"#{x+1}")
			g.play(g.player, ans.bestMove)
			ans = analyze(g)
	
	if COPY_SGF:
		button = msgBox("Collapsed or as moves?", buttons=["With Moves", "Collapsed"])
		col = False
		if button == "Collapsed":
			col = True
		sgf = getSGF(k, col)
		set_clipboard(sgf)
		msgBox("Copied SGF to clipboard!")
	
	if PASTE_SGF:
		from SgfParser import SgfParser
		sgf = SgfParser.fromString(get_clipboard())
		g = sgf.root.toGobanList()[-1]
		if g.xsize != k.xsize or g.ysize != k.ysize:
			msgBox(f"SGF is {g.xsize}x{g.ysize} but your board is {k.xsize}x{k.ysize}", buttons=["Cancel"])
		else:
			bookmark(g, location="end")
			log("Created new Bookmark for SGF!\n")
		
	if SENTES:
		markSentes(k)

	if SAVE_SGF:
		button = msgBox("Collapsed or with moves?", buttons=["With Moves", "Collapsed"])
		col = False
		if button == "Collapsed":
			col = True
		sgf = getSGF(k, col)
		
		file = chooseFile("Save SGF", save=True, extension=".sgf")
		if file:
			with open(file, "w") as f:
				f.write(sgf)

# main script entry
if GO_DEEP:
	# request a high level of visits and rerun the script
	mark((k.xsize//2, k.ysize//2), "GOING DEEP, PLEASE WAIT...", scale=2.0)
	snooze()
	rerun(DEEP_VISITS, DEEP_VISITS)
	
clearLog()
blackScore, whiteScore = main_stuff()
button_stuff()

# build status text
estimate = k.scoreLeadBlack
wr = k.winrateBlack
if estimate > 0:
	scoreText = f"B+{estimate:0.1f} ({wr*100:0.0f}%)"
else:
	scoreText = f"W+{-estimate:0.1f} ({(1-wr)*100:0.0f}%)"
	
status(f"{k.player} to play | {k.visits} visits | points: B {blackScore}, W {whiteScore+k.komi} | final: {scoreText}")

# GUI feedback
log(f"Display Mode:    {DISP_MODE}")
log(f"Terri threshold: {TERRI_THRESHOLD}")
log(f"Vital threshold: {VITAL_THRESHOLD*100:0.1f}% winrate loss")
log(f"Move Count:      {MOVE_COUNT}")
log(f"PV Var:          {PV_VARIATION}")
log(f"Deep Visits:     {DEEP_VISITS}")

log(f"\nResult:          {scoreText}")
