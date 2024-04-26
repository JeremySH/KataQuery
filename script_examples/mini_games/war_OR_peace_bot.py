# WAR OR PEACE BOT
# Play against Katago, 
# but choose how  Katago plays :

# aggressive moves: ●
# peaceful moves: ○
# best moves: □

humanColor = "black" # human's color
cheat = False

MAX_MOVES = 6
BOTH_SIDES = False  # let katago play both sides


def getMove(futures, testFunction):
	# as long as Katago stays within a winrate drop
	# and uses its top moves,
	# it can play with a "style" by choosing
	# moves using different criteria

	global MAX_MOVES
	bestJump = None
	bestMove = k.moves[0]
	for m, future in futures:
		# prevent KataGo from self-harm:
		if k.winrate - m.winrate > 0.02: break

		scoreJump = future.scoreLead - k.scoreLead 
		
		if bestJump == None: bestJump = scoreJump

		if testFunction(scoreJump, bestJump):
			bestJump = scoreJump
			bestMove = m
	
	return bestMove

clearMarks() ; clearHeat() 

fightMessage = ""
if k.depth == 'full':
	if BOTH_SIDES or humanColor != k.toPlay:

		# try some plays to determine max point threat,
		# and use this info to get "war" or "peace" move
		futures = []
		for m in k.moves[:MAX_MOVES]:
			analysis = quickPlay(k, [[k.toPlay, m.coords], [opponent(k.toPlay), "pass"]])
			futures.append((m, analysis))

		peaceMove = getMove(futures, lambda a,b: a < b)
		warMove = getMove(futures, lambda a,b: a > b)

		mark(peaceMove, "circle")
		mark(warMove, "●")			

		if peaceMove == k.bestMove:
			mark(peaceMove, "square")
		if warMove == k.moves[0]:
			mark(warMove, "square")
	elif cheat:
		for m in k.moves: mark(m)

if BOTH_SIDES or humanColor != k.toPlay:
	status(f"my play ({k.toPlay}) {fightMessage} | {k.visits} visits")
else:
	status(f"your play {fightMessage}")
