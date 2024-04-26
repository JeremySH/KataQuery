# play against katago

humanColor = "black"

clearAll()
if k.depth == "full": # after a full analysis
	if k.toPlay != humanColor:
		mark(k.bestMove, "circle")
		coord = k.bestMove.coords
		status(f"MY PLAY: {k.toPlay[0].upper()} {coord} | {k.visits} visits")
	else:
		status(f"Your play? ({k.toPlay}) | {k.visits} visits")

