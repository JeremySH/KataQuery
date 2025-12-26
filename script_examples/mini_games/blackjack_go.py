# Blackjack Go
# a mini-game similar to blackjack

# Each HIT ME generates moves of 
# higher and higher quality.

# If player thinks the move is good,
# he plays it. If not, he HITS again.

# If player HITS on the best move,
# he busts.

# If he "stands" on any move within 3%
# winrate of the best one, he wins!

# A GEN GAME button is provided
# that will put some stones on the
# board

WINRATE_GAP = 0.03

# lower bound of policy at beginning of
# round
POLICY_START = .0008

# tracking the game
persist("previousK", None)
persist("prevChoice", None)
persist("policy_min", POLICY_START)
persist("hitcount", 0)
persist("bustFlag", False)

# GUI
HIT_ME = button1("HIT ME")
GEN_GAME = button2("GEN GAME")


import random

def anim(text):
	"animate text at bottom of board"
	p = (k.xsize//2, -0.5)
	for x in range(k.xsize):
		pre = " "*(k.xsize-x)
		t = pre.join(list(text))
		mark(p, t)
		snooze(.001)
	mark(p, text)

def animPoint(point, theMark):
	"animate a mark at the point"
	for x in range(10, 1, -1):
		mark(point, theMark, scale=x)
		snooze(.001)
		
instructions = \
"""
To start a round, press HIT ME.
Suggestions get better with each HIT.
To stand, play the shown move.
If you play a top move, you win!

BEWARE: you can bust!

To resume after bust, modify the board (e.g. make a play)

Have fun!

"""

clearAll()
clearLog()
log(instructions)

if k.depth != "full":
	bail()

if GEN_GAME:
	g = k.goban.copy()
	ans = k
	for x in range(round(k.xsize*k.ysize/7)):
		m = ans.bestMove
		if random.random() > 0.5:
			m = random.choice(ans.moves_by_policy[:5])
		g.play(g.toPlay, m)
		ghost(m, g.toPlay)
		snooze()
		g.toPlay = opponent(g.toPlay)
		ans = analyze(g)
	
	bookmark(g)
	status("bookmark created. Scroll to it.")
	bail()

if HIT_ME:
	# start a new game if necessary
	if previousK == None:
		previousK = k
		prevChoice = None
		bustFlag = False

# we don't start games unless requested
if previousK == None:
	bail()

# when board changes, check if the last
# move is correct
if previousK.thisHash != k.thisHash:
	if not k.last_move: # can happen on board clear
		pass
	# player selected the move offered?
	elif prevChoice and prevChoice.pos == k.last_move.pos:
		p = previousK.get_point(k.last_move.pos)
		if bustFlag:
			anim(" ")
		elif not p.isMove:
			anim("LOSS")
			mark(previousK.bestMove, "square")
		elif previousK.bestMove.pos == p.pos :
			anim("WIN! BEST MOVE BONUS!")
		elif previousK.bestMove.winrate - p.winrate < WINRATE_GAP and not bustFlag:
			wr = previousK.bestMove.winrate - p.winrate 
			anim(f"WIN! (winrate gap: {round(wr*100)}%)")
		else:
			anim("LOSS")
			mark(previousK.bestMove, "square")
	else: # player played elsewhere or something
		pass
	
	previousK = None
	prevChoice = None
	policy_min = POLICY_START
	hitcount = 0
	bustFlag = False

if HIT_ME:
	busted = prevChoice == k.bestMove
	if busted:
		anim("BUST")
		bustFlag = True
		mark (previousK.bestMove, "square")
	else:
		# pick from moves between top value and
		# lower bound of policy (policy_min)
		selection = [m for m in k.moves_by_policy if m.policy > policy_min]
		if k.bestMove not in selection:
			selection.append(k.bestMove)
		
		if hitcount == 0:
			anim("HIT OR PLAY?")
		else:
			anim(f"YOU HIT ({hitcount})")
		hitcount += 1
		prevChoice = random.choice(selection)
		
		# increase lower bound of policy filter
		policy_min = prevChoice.policy

		# show next idea
		ghost(prevChoice, k.toPlay)
		animPoint(prevChoice.pos, "?")
