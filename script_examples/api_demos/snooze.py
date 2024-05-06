# Snooze
# snooze() delays for a specified number of seconds.
# This allows you to make rudimentary animations, or
# update the display during long calculations.
# Press cmd-R to run this script.

# WARNING: executing commands during snoozes can
# muck with your script

if k.manual_run:
	clearAll()

	toplay = k.toPlay
	q = k
	
	for x in range(10):
		best = q.bestMove
		
		ghost(best, toplay)
		mark(best, x+1)

		q = quickPlay(q, [[toplay, best.coords]])
		toplay = opponent(toplay)
		
		snooze(0.25)
	
	snooze(3)
	clearAll()
