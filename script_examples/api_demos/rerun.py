# rerun()
# Lets you increase the visits and immediately rerun your script.
# this allows for incremental analysis updates.
# Much slower, but more feedback.

# rerun (more_visits, max_visits)

# where more_visits are the amount of visits to add
# and max_visits is the stopping point.

# how it works:
# when rerun() is called, the script
# IMMEDIATELY exits (via bail()) after it
# submits an analysis request.

# After the requested analysis
# is ready, the script will automatically rerun, and `k`
# will have more visits (and deeper info)

# this allows you to create scripts with automatic
# analysis updates.

# it also allows you to guarantee a minimum number of visits
# with something like:
# rerun(1000, 1000)

# if max_visits is already reached,
# rerun() does nothing, does not bail(),
# and control passes through to the subsequent code.

# NOTE: rerun() does NOT run during quick analysis,
# and will simply bail()

# here, we show an auto-update
# of winrate values.
clearAll()

move_count = len(k.moves)

for m in k.moves:
	# scale by move order for fun
	scale = 1.0 + pow(0.5*(move_count-m.order)/move_count,2)
	mark(m, f"{m.winrate*100:0.0f}", scale=scale)
	
	# blue move
	if m.order < 8:
		heat(m, 0.5 + pow(0.5*(8-m.order)/8,2))

# report visits
status(f"{k.visits} visits")

# add 50 more visits, up to 1000, and bail()
# if we're already at 1000 visits,
# fall through and continue 
rerun(50, 1000)

# we only get here after 1000 reached, or quick analysis
status(f"analysis done! {k.visits} visits")