# AVOID THE BADDIE
# given 3 moves, avoid the bad one

# increase badness to get worse secret suggestion
BADNESS = 6

CLEAR_SCORE = False

persist("lastBest", None)
persist("hash", None)
persist("color", k.player)
persist("score", [0,0])
persist("OKMoves", [])

if CLEAR_SCORE:
	score = [0,0]

clearAll()

msg = ""
if k.depth == 'full':
	if hash != k.thisHash:
		if lastBest != None and color != k.player:
			found = False
			for m in OKMoves:
				p = k.get_point(m)
				if p.color != "empty":
					found = True
					heat(p.pos, 1)
					score[0] += 1
					break

			if not found:
				for m in OKMoves:
					heat(m, 0.5)
			else:
				msg = " | SUCCESS! "
			score[1] += 1

	hash = k.thisHash
	lastBest = k.moves[0]
	color = k.player

	OKMoves = []
	for m in k.moves[:2]:
		mark(m, "?")
		OKMoves.append(m.pos)

	by_policy = sorted(k.legal_moves, key=lambda p: -p.policy)
	for p in by_policy[BADNESS:]:
		if p.pos not in OKMoves:
			mark(by_policy[7], "?")
			break

status(f"{k.player} to play | score: {score[0]}/{score[1]} {msg}")