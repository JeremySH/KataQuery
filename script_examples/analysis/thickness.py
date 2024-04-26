# Calculate "Thickness"
# Thickness here is the amount of intersection ownership 
# that matches the stone upon it

# It ranges from -30 (dead & in the bowl) to 10 (immortal).
# Ownership is shifted down by 0.5 with the
# assumption that stones are not like spaces:
# if stones have quetionable ownership they are dying or weak

# Because Katago's analysis of ownership is sophisticated,
# "thickness" differences can be obvious or subtle depending on
# position

clearAll()

for i in k.stones:
	if i.color == "white" :
		val = (i.ownershipWhite - 0.5) * 20
	else:
		val = (i.ownershipBlack -0.5) * 20

	mark(i.pos, round(val))

status(f"{k.toPlay} to play | {k.visits} visits")