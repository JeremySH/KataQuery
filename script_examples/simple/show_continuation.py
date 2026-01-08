# Show Continuation
# show the top continuation using the PV information

NUMBER = check1("number moves")

def show_continuation(answer, labels=False):
	"show continuation plays with ghost stones"

	player = k.player 

	for i, m in enumerate(answer.bestMove.pvPos):
		ghost(m, player)
		player = opponent(player)
		if labels:
			mark(m, i+1)

clearAll()
show_continuation(k, NUMBER)
