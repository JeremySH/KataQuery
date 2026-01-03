# use the heat map to show "obvious" moves
# as they occur
clearAll()

# allowed_moves is set through the "Localize" menu item
for m in k.allowed_moves:
	if m.policy*len(k.legal_moves) > 150:
		heat(m, 1)
	elif m.policy*len(k.legal_moves) > 80:
		heat(m, 0.5)
		
status(f"{k.player} to play")