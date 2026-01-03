# The "Perfect" Game
# WARNING: this will take some time to execute.
# (press cmd-R)

# This uses KataGo's policy net to show
# what its raw brain thinks is the "perfect game"
# from the current position.

# SHOULD BE RUN WITH "pure" checked in "Neural Nets..."
# dialog box, which will give the same game every time.

# use evaluated moves instead of policy?
PERFECT_MEANS_EVAL = False

if k.manual_run:
	clearAll()
	g = k.goban.copy()
	ans = k
	
	for _ in range(500):
		if len(ans.moves_by_policy) == 0:
			break

		if ans.bestMove == ans.pass_move:
			break # game over

		if PERFECT_MEANS_EVAL:
			next_move = ans.bestMove
		else:
			next_move = ans.moves_by_policy[0]

		ghost(next_move, g.player)
		snooze() # update display
	
		g.play(g.player, next_move.pos)
		
		g.player = opponent(g.player)
		ans = analyze(g)
		g = ans.goban.copy()
	
	set_clipboard(g.as_sgf())
	snooze(1.0)
	clearAll()
	status("SGF copied to clipboard")