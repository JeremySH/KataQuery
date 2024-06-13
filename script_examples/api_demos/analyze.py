# analyze() example
# this is an easier way to get analysis than quickPlay().
# It uses a goban object instead of a KataAnswer, which
# simplifies things.

# use these buttons to generate moves:

GENERATE_FAST = button1("Gen Fast")
GENERATE_NEAR = button2("Gen Nearby")
GENERATE_LOCAL = button3("Gen Local")
HELP = button4("help")

status(f"{k.toPlay} to play")

if HELP:
	import pydoc
	log(pydoc.plain(pydoc.render_doc(analyze)))

if GENERATE_FAST:
	# generate 30 moves quickly
	clearAll()
	goban =  k.goban
	for i in range(1,30):
		
		# returns a KataAnswer object, just like 'k'
		ans = analyze(goban)

		ghost(ans.bestMove, goban.toPlay)
		snooze() # update display

		# make sure you use .pos to play a gopoint
		goban.play(goban.toPlay, ans.bestMove.pos)
		goban.toPlay = opponent(goban.toPlay)

	status("DONE.")

if GENERATE_NEAR:
	# generate moves nearby existing stones,
	# to show some of the parameters
	clearAll()
	goban = k.goban
	for i in range(1,10):
		ans = analyze(goban, nearby=2, visits=20)
		
		best = ans.bestMove.pos
		ghost(best, goban.toPlay)
		snooze()
		
		goban.play(goban.toPlay, best)
		goban.toPlay = opponent(goban.toPlay)

	status("DONE.")

if GENERATE_LOCAL:
	# manually specify region of interest
	# with the allowedMoves keyword.
	# here, we play near the last move
	
	clearAll()
	goban = k.goban
	ans = k
	latest = None
	if k.lastMove:
		latest = k.lastMove.pos
	
	for i in range(1,20):
		near = None
		if latest:
			# generate moves 3 hops near last played
			points = set([latest])
			for x in range(3):
				points = points.union(goban.nearby_these(points))
			near = list(points)

		ans = analyze(goban, allowedMoves=near, visits=5)
		
		best = ans.bestMove.pos
		latest = best
		ghost(best, goban.toPlay)
		snooze() # update
		
		goban.play(goban.toPlay, best)
		goban.toPlay = opponent(goban.toPlay)

	status("DONE.")


