# Query Points
# (experimental!)
# Query points allow you to click the
# board to send your script intersections.

# This is useful for triggering deeper analysis
# or for creating games/trainers

# Points can be specified via Query Mode
# or a simple middle-click of the mouse.
		
def localFight(point):
	"show a possible local fight near point"
	g = k.goban.copy()
	ans = k
	plays = []
	thePlay = point
	
	# show 9 local moves
	for x in range(1,10):
		# play current move
		g.play(g.toPlay, thePlay)
		ghost(thePlay, g.toPlay)
		mark(thePlay, x)
		plays.append(thePlay)
		
		# analyze for next move
		allowed = plays
		for _ in range(3):
			allowed = g.nearby_these(allowed)
		
		g.toPlay = opponent(g.toPlay)
		ans = analyze(g, allowedMoves=allowed)
		thePlay = ans.bestMove
	
clearAll()
if k.depth == "full":
	# use the first legal query point
	# to generate a local fight
	if len(k.query_points):
		play = None
		for p in k.query_points:
			if p.legal:
				play = p
				break
		
		if play:
			localFight(k.query_points[0])
