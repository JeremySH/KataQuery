# Bubble Ranks
# this view shows relative ranks by
# size, which could be more intuitive
# than colors

def bubbleRankPolicy(limit):
	from math import pow
	pol = [p for p in k.moves_by_policy if p not in k.moves]
	moves = k.moves + pol
	for i, m in enumerate(moves[:limit]):
		score = (len(moves)-i) / len(moves)
		mark(m, "circle", scale = 0.75 + m.policy*3.5)

def bubbleRankMoves():
	from math import pow
	winrateRange = k.winrateMax-k.winrateMax
	if winrateRange != 0:
		for m in k.moves:
			score = (m.winrate-k.winrateMakx)/winrateRange
			mark(m, "circle", scale = 0.75 + pow(score,2))
	else:
		mark(k.bestMove, "circle")
		
clearAll()
bubbleRankPolicy(20)
bubbleRankMoves() # replace policy with winrate bubbles if available
status(f"{k.player} to play | {k.visits} visits")
