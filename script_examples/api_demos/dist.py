# dist()
# Calculates manhattan distance between 2 points.
# Here it's used to show a move blob around tengen

MAX_SHOWN = 20
RADIUS = 4

clearAll()

i = 1
for m in k.moves_by_policy:
	middle = ((k.xsize-1)/2,(k.ysize-1)/2)
	d = dist(m, middle)
	if d <= RADIUS:
		mark(m, i)
		i = i+1
		if i > MAX_SHOWN: break