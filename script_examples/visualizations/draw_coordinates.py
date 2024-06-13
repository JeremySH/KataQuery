# draw coordinates
def coords():
	letters="ABCDEFGHJKLMNOPQRSTUV"
	for x in range(k.xsize):
		mark((x, k.ysize-0.5), letters[x], scale=0.9)
	
	for y in range(k.ysize):
		mark((-0.5, y), y+1, scale=0.9)

clearAll()
coords()