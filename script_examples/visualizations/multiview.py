# MULTIVIEW
# Different views are cycled as you press CTRL-R
# (see bottom for how this is actually done)

def nothin(): 
	status(f"EMPTY VIEW | {k.player} to play")

def terri():
	"show KataGo's guess of territory"
	threshold = 0.02

	terriWhite = 0
	terriBlack = 0

	for i in k.intersections:
		if i.ownershipBlack > threshold:
			heat(i.pos, 1)
			terriBlack += 1
		if i.ownershipWhite > threshold:
			heat(i.pos, 0.25)
			terriWhite +=1

	if k.depth == 'full':
		clearMarks()
		for m in k.moves[:5]:
			mark(m.pos, "circle")

	b_winrate = round(k.winrateBlack* 100)
	status(f"TERRI VIEW | {k.player} to play | white: {terriWhite} | black: {terriBlack} | black winrate: {b_winrate}%")

def nearby():
	"show policy moves near existing stones"
	SUGGESTIONS_PER_STONE= 2.0
	MAX_SUGGESTIONS = 20 # hard limit

	# inspect how far away from stones?
	EXPANSIONS = 3

	def legit(p):
		"is this point within the confines of the board?"
		return p[0] >= 0 and p[1] < k.xsize and p[1] >= 0 and p[1] < k.ysize

	def nearby(thesePoints = None):
		"""
		return set of tuples that include all intersections near thesePoints.
		By default thesePoints are all stones currently on the board
		"""
		if thesePoints == None:
			thesePoints = set([p.pos for p in k.stones])

		points = set(thesePoints)
		for p in thesePoints:
			for neighbor in [(1,0), (-1,0), (0,1), (0,-1)]:
				p2 = (p[0] + neighbor[0], p[1] + neighbor[1])
				if legit(p2):
					points.add(p2)

		return points

	near = None
	for i in range(EXPANSIONS):
		near = nearby(near)

	#print(near)
	policies = []
	max_policy = -1
	min_policy = 10000

	for l in k.legal_moves:
		if l.pos in near:
			policies.append([l.pos, l.policy])
			max_policy = max(l.policy, max_policy)
			min_policy = min(l.policy, min_policy)

	policies = sorted(policies, key=lambda x: x[1], reverse=True)

	stonecount = len(k.stones)
	limit = int(min(stonecount*SUGGESTIONS_PER_STONE, MAX_SUGGESTIONS))

	# mark the policy values by rank
	for i, p in enumerate(policies [:limit]):
		mark(p[0], i+1)
		heat(p[0], (p[1] + min_policy)/(max_policy-min_policy))

	# mark the vitality of stones
	for i in k.stones:
		if i.color == "white" :
			val = max(i.ownershipWhite, 0)*10 -1
		else:
			val = max(i.ownershipBlack, 0)*10-1

		mark(i.pos, round(val))


	status(f"NEARBY VIEW | {k.player} to play")


def vitals():
	"Detect Vital Points"
	global VITAL_COMMENT
	VITAL_GAP = 9.0

	clearAll() 

	VITAL_COMMENT = ""

	def vitals(vitals_gap=9.0):
		global VITAL_COMMENT
		if len(k.moves) < 2: return []
	        
		bestRate = k.winrateMax
		ratio = lambda a,b: a/(b+1e-9) # natural ratio, distances from 0%

		if bestRate > 0.5:
			ratio = lambda a,b: (1.0-b)/((1.0-a)+1e-9) if a < 1.0 else 1.0 #in "distance from 100%"
	    
		lastRate = bestRate
		candidates = []
		drop = 0.0

		for m in k.moves:
			if len(candidates) > 2: return []
			drop = (1.0 - ratio(m['winrate'],lastRate))*100.0
	        
			if drop > vitals_gap: # big drop, anything above this is vital
				break
			else:
				if len(candidates) >= 2: return []
				candidates.append(m.pos)

		if len(candidates):
			VITAL_COMMENT= f"Vitals by {round(drop)}%"
		
		return candidates

	for v in vitals(VITAL_GAP):
		mark(v, "♢")

	if VITAL_COMMENT == "": VITAL_COMMENT = "no vitals found"
	status(f"VITALS VIEW | {k.player} to play | {VITAL_COMMENT}")

def strong_moves():
	"Order the moves but enlarge those that improved in rank through reading (aka visits)"
	policies = k.moves_by_policy

	if k.depth == 'quick':
		for i, m in enumerate(policies[:7]):
			mark(m, i+1)
	else:
		ranks = {}
		for i, p in enumerate(policies):
			ranks[p.pos] = i

		for m in k.moves[:7]:
			if m.order >= ranks[m.pos]:
				# matches policy rank or is inferior
				mark(m, m.order+1)
			else:
				# better than policy rank, make it huge
				mark(m, m.order+1, scale=1.5)

	status(f"MOVE STRENGTH VIEW | {k.player} to play | {k.visits} visits")

# Rotate through the above functions
persist("COUNT", 0)

if k.manual_run: # only True on CTRL-R
	COUNT = (COUNT + 1) % 4

clearAll()

# use the COUNT variable as an index to our functions and call it
[strong_moves, terri, nearby, vitals, nothin][COUNT]()

if k.last_move:
	mark(k.last_move, "square")