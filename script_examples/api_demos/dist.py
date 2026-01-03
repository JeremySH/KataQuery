# dist()
# Calculates manhattan distance between 2 points.
# Here it's used to show a move blob around
# the last move or tengen

MAX_SHOWN = 20
RADIUS = 4

middle = (k.xsize//2, k.ysize//2)
middle = k.last_move if k.last_move else middle

clearAll()

i = 1
for m in k.moves_by_policy:
	# calculate distance
	d = dist(m, middle)
	
	# display only if close enough
	if d <= RADIUS:
		# mark by rank
		mark(m, i)
		i = i+1
		if i > MAX_SHOWN: break