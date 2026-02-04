# goban2senseis
# copy a "sensei's library" style diagram
# of the position, suitable for pasting
# into the wiki.

# NOTE: needs to be manually run (CMD-R)

def goban2senseis(goban, title="", number_last=0, coordinates=True):
	"""
	return a Sensei's Library diagram of the passed goban.
	`title`       : a comment beneath the board
	`number_last` : number the latest n moves (limit: 10)
	`coordinates` : show coordinates on the board
	"""

	digits = "1234567890"
	
	who = goban.player[0].upper()
	coords = "c" if coordinates else ""

	# board header
	s = f"$${who}{coords} {title}\n"
	s += "$$ +" + "-"*(2*goban.xsize+1) + "+\n"

	# grab latest moves, if desired
	number_last = max(0, min(number_last, 10))

	if number_last:
		places, moves = goban.stones_n_moves()
		latest = [m[1] for m in moves[-number_last:]]
	else:
		latest = []
			
	last = goban.last_move()[1]

	# render each row
	for yflipped in range(goban.ysize):
		y = goban.ysize-yflipped-1
		s += "$$ | "
		for x in range(goban.xsize):
			color = goban.get((x,y))
			
			is_last = (x,y,) == last
			if (x,y,) in latest:
				print(latest.index((x,y,)))
				s += digits[latest.index((x,y,))] + " "
			else:
				if color == "white":
					if is_last:
						s += "W "
					else:
						s += "O "
				elif color == "black":
					if is_last:
						s += "B "
					else:
						s += "X "
				else:
					s += ". "
					
		s += "|\n"
	s += "$$ " + "+" + "-"*(2*goban.xsize+1) + "+\n"

	return s

if k.manual_run:
	# construct some comment text
	other = opponent(k.player)[0].upper()
	title = f"{k.player.capitalize()}'s best response to {other}2?"
	
	# get diagram
	diagram = goban2senseis(k.goban, title, number_last=2)

	# copy it
	set_clipboard(diagram)
	notify("Sensei's Diagram", "Copied!")