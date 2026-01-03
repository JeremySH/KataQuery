# "It's Complicated" Bot

# This bot chooses the move that produces the most complexity,
# as implied by k.scoreStdDev
# (see complex_move())

# when the evaluation is inverted,
# bot tends to simplify the board

GEN_GAME = button1("Gen Game")
persist("HUMAN", "neither")
HUMAN_SELECTED = button2("Player...")
MARK_BEST = check1("Mark Best Move")
INVERT = check2("Simplify instead")

SELECT_PROB = 1.0  # ajdust lower to get different games

def complex_move(ans, invert=False):
	"""
	return a moveinfo that represents
	the move that creates the most complexity.
	if `invert`, return a move with least complex result.
	"""
	# don't go too crazy
	if ans.bestMove.winrate < .45:
		return ans.bestMove
	
	#moves = ans.filter(f"{ans.bestMove.scoreLead} - m.scoreLead < 0.5", ans.moves)
	moves = ans.filter(f"{ans.bestMove.winrate} - m.winrate < 0.03", ans.moves)
	
	for m in moves:
		# try the move
		g = ans.goban.copy()
		g.play(ans.player, m)
		g.player = opponent(g.player)
		
		# quickly calculate complexity (scoreStdev)
		a = analyze(g, visits = 2)
		m['complexity'] = a.scoreStdev
	
	if invert:
		return ans.min("m.complexity", moves)
		
	return ans.max("m.complexity", moves)

import random

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
		ans = analyze(g, visits=10)
		move = ans.bestMove
		
		if random.random() <= SELECT_PROB:
			move = complex_move(ans, invert=INVERT)
		
		g.play(g.player, move)
		ghost(move, g.player)
		snooze()
		g.player = opponent(g.player)

	bookmark(g, location="end")
	msgBox("New Game bookmarked!")

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