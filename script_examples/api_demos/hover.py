# Hover Text
# Show some intersection information when hovered over.
# This is useful to keep the board clean

clearHovers()
for i in k.intersections:
	adjPol = i.policy * len(k.legal_moves)

	if adjPol < 0:
		txt = f"{i.coords}\nPolicy: illegal move\n"
	else:
		txt = f"{i.coords}\nPolicy: {round(adjPol)}\n"
		
	if i.ownershipBlack > i.ownershipWhite:
		txt += f"Black's Point by {i.ownershipBlack}"
	elif i.ownershipBlack < i.ownershipWhite:
		txt += f"White's Point by {i.ownershipWhite}"
	else:
		txt += f"Nobody's point"
	
	hover(i, txt)
