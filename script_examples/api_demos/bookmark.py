# bookmarks
# bookmark(goban) inserts the provided goban into the bookmarks.
# This is useful for generating positions.

# WARNING: it's a bit tricky because of the feedback loop:

# 1. the board is NOT refreshed after a bookmark, as this
#    would trigger an endless analyze loop.
# 2. script is rerun at every board change, which could be unexpected!
# 3. Therefore protect from re-runs with a GENERATE 
#    button in the GUI, or by checking k.manual_run


# button protects from runaway generation:
GENERATE = button1("generate")

# create a bookmark per move?
EXPLODE = check1("explode")

clearAll()
if k.depth != "full": bail()


if GENERATE:
	# generate 80 moves from
	# the currently visible position.
	ans = k	
	for i in range(1,80):
		if EXPLODE:
			# location can be "current"(default) "start" or "end"
			bookmark(ans.goban, location='end')
		ans = quickPlay(ans, [[ans.player, ans.bestMove.coords]])
		
		if ans.bestMove == ans.pass_move:
			break

		ghost(ans.bestMove, ans.player)
		snooze()
	
	# just bookmark once if not exploded
	if not EXPLODE:
		bookmark(k.goban) # convenience, bookmark current
		bookmark(ans.goban, location='current')
	
	status(f"Bookmarks ready!")
	clearGhosts()