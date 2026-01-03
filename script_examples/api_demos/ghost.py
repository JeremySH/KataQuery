# Dream Analysis
# to show off ghost stones

# by giving KataGo 3+ free moves
# we can see what its big dream is
# (usually: surround & kill)
# Kinda neat with Localize... on

FUTURE_COUNT = int(dial1("Future count", min_value=1, max_value=10, default_value=3))

clearAll()

def katagoDream(amount):
	other = opponent(k.player)
	result  = [k.bestMove]
	ans = k
	for _ in range(amount-1):
		ans = quickPlay(ans, [[k.player, ans.bestMove.coords], [other, "pass"]])
		result.append(ans.bestMove)
	return result
	
if k.depth == "full":
	moves = katagoDream(FUTURE_COUNT)
	for i, m in enumerate(moves):
		ghost(m, k.player)
	mark((k.xsize//2, -0.5), f"({k.player} wants stones here)")
	
status(f"{k.player} to play")