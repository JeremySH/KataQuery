# show the DMZ (contestable area) in blue
# interestingly, Katago sees some areas as already
# claimed by the player yet to make a move

clearAll()

def dmz():
	for i in k.intersections:
		if abs(i.ownership) < 0.03:
			mark(i.pos, "x")

		if abs(i.ownership) == 0.0: continue # avoid divide by zero

		if abs(i.ownership) < 0.08:
			heat(i.pos, 0.02/abs(i.ownership))

dmz()
status(f"{k.toPlay} to play | {k.visits} visits")