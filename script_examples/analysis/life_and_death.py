# Life And Death
# mark the life, death, and questionable status
# of stones

clearMarks()
clearHeat()

for i in k.stones:
	if i.color == "white" :
		if i.ownershipWhite < 0:
			mark(i.pos, "x")
		elif i.ownershipWhite < 0.5:
			mark(i.pos, "?")
	else:
		if i.ownershipBlack < 0:
			mark(i.pos, "x")
		elif i.ownershipBlack < 0.5:
			mark(i.pos, "?")

#heat(i.pos, i.ownershipHeat)

status(f"{k.toPlay} to play | {k.visits} visits")