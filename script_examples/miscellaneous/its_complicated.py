# "It's Complicated" Bot
# recommended:
# Network: b15
# Pure:    OFF

# This bot chooses the move that produces the most complexity,
# as implied by move.scoreStdDev
# (see complex_move())

# when the evaluation is inverted,
# bot tends to simplify the board

import random

persist("HUMAN", "neither")

GEN_GAME =       button1("Gen Game")
HUMAN_SELECTED = button2("Player...")
MARK_BEST =      check1("Mark Best Move")
INVERT =         check2("Simplify instead")

SELECT_PROB = 0.75  # how likely to go complicated
	
def complex_move(ans, invert=False):
	"""
	return a moveinfo that represents
	the move that creates the most complexity
	(within reason).
	if `invert`, return a move with least complex result.
	"""
	import random
	SLACK = 0.1 # for a bit of randomness
	
	# don't go too crazy
	if ans.bestMove.winrate < .45:
		return ans.bestMove

	moves = ans.filter(f"{ans.bestMove.winrate} - m.winrate < 0.02", ans.moves)
		
	if invert:
		moves = ans.sorted("m.scoreStdev", moves)
	else:
		moves = ans.sorted("-m.scoreStdev", moves)
	
	m = moves.pop(0)
	
	while random.random() < SLACK and len(moves):
		m = moves.pop(0)

	return m

if HUMAN_SELECTED:
	HUMAN = msgBox("Who do you play?", buttons=["black", "white", "neither"])

if GEN_GAME:
	
	# choose amount of board coverage desired
	coverage = int(msgBox("Board Coverage (%)?", buttons=["15", "25", "50", "70"]))
	moveCount = int((coverage/100)*k.xsize*k.ysize)
	
	# play up until board coverage is reached
	g = k.goban.copy()
	g.clear()
	g.player = "black"
	
	for p in range(moveCount):
		ans = analyze(g, visits=30)
		move = ans.bestMove
		
		if random.random() <= SELECT_PROB:
			move = complex_move(ans, invert=INVERT)
		
		g.play(g.player, move)
		ghost(move, g.player)
		snooze()
		g.player = opponent(g.player)

	bookmark(g, location="end")
	msgBox("New Game bookmarked!")

# generate a bot move if appropriate
if k.player != HUMAN:	
	if k.depth == "full":
		complicated = k.bestMove
		
		if random.random() <= SELECT_PROB:
			complicated = complex_move(k, invert=INVERT)
		
		clearAll()
		mark(complicated)
		ghost(complicated, k.player)
		
		if MARK_BEST:
			mark(k.bestMove, "B")
			
		status(f"scoreStdev: {k.scoreStdev}")
else:
	clearAll()
	status(f"{k.player} to play")