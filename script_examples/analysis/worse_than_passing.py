# moves scored by terribleness
# where the bigger the number, the crappier
# it is.
# moves only worse than passing are shown

clearAll()

def worseThanPassing():
	x = k.pass_move.policy
	pol = [p for p in k.moves_by_policy if p.policy < x]
	
	return enumerate(pol,1)

for i, m in worseThanPassing():
	mark(m, i)

status(f"{k.toPlay} to play")

