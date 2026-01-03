# Current "points at stake" on the board is calculated by
# passing and subtracting the score difference:
# (score - pass score)/2

# if a player can grab that many points, or rescue that
# many points, then she has played an ideal move
# (according to KataGo)

# higher points at stake implies sente,
# fights, and so on
# lower points at stake imply peace, endgame, dame, etc

clearAll()

if k.depth == 'full': # because we use "quickplay" which may take a bit longer

	# determine score change when I pass 
	mePass = quickPlay(k, [[k.player, "pass"]])

	board_value = abs(k.scoreLeadWhite - mePass.scoreLeadWhite)/2
	board_value = round(board_value*10)/10.0

	# these are wild guesses
	if board_value > 20:
		kind = "LIFE OR DEATH"
	elif board_value > 11:
		kind = "FIGHT"
	elif board_value > 8:
		kind = "struggle"
	elif board_value > 5:
		kind = "open play"
	elif board_value > 3:
		kind = "peace"
	elif board_value >= 1:
		kind = "endgame"
	else:
	    kind = "dame"

	status(f"{k.player} to play | points at stake: {board_value} | {k.visits} visits | {kind}")
	mark( (k.xsize/2, -0.5,), f"{board_value} points at stake • {kind}", scale=1.5)


for m in k.moves[:6]:
	mark(m.pos, m.order+1)
