# Save SGF
# save an SGF of the current goban
# only activates on CMD-R (Code->Run)

def save_goban_as_sgf(g: "Goban", collapse=False) -> bool:
	"ask for a filename to save to, and save passed goban as sgf"
	
	filename = chooseFile(prompt="Save SGF", save=True, extension="sgf")

	if filename:
		if collapse: # for single-node "diagrams"
			g = g.copy()
			g.collapse()
		
		sgf = g.asSGF()	

		with open(filename, "w") as f:
			f.write(sgf)
		
		return True

	return False

if k.manual_run:
	save_goban_as_sgf(k.goban)