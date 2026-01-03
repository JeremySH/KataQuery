# play against katago

humanColor = "black"

clearAll()
if k.depth == "full": # after a full analysis
	if k.player != humanColor:
		mark(k.bestMove, "circle")
		coord = k.bestMove.coords
		status(f"MY PLAY: {k.player[0].upper()} {coord} | {k.visits} visits")
	else:
		status(f"Your play? ({k.player}) | {k.visits} visits")

