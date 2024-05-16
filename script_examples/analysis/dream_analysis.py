# Dream Analysis

# by giving KataGo 3+ free moves
# we can reveal what its big dream is
# (usually: surround & kill)

# Interrupting "the dream" with occasionaal
# opponent moves can peel back the layers of 
# the big dream

# GUI Controls
# "Dream Depth"       : how far into the future?
# "1st move rank" knob: show different plans
# "Numbers"           : show order of moves taken
# "Hide"              : just hide it


USE_NUMBERS = check1("Numbers")
HIDE = check2("Hide")

FUTURE_COUNT = int(slider1("Dream depth", min_value=0, max_value=10, default_value=3))
FIRST_RANK = int(slider2("1st move rank", min_value=0, max_value=10))

clearAll()
clearLog()
log(f"Dream Depth: {FUTURE_COUNT}")
log(f"1st Move Rank: {FIRST_RANK+1}")

status(f"{k.toPlay} to play | {k.visits} visits")

if HIDE:
	bail()
	
def katagoDream(amount: int) -> list:
	"play future moves with a single color and return them"
	other = opponent(k.toPlay)
	ans = k

	if len(k.moves) > FIRST_RANK:
		ans.bestMove = k.moves[FIRST_RANK]
	else:
		ans.bestMove = k.moves[-1]

	result  = [ans.bestMove]

	for _ in range(amount-1):
		ans = quickPlay(ans, [[k.toPlay, ans.bestMove.coords], [other, "pass"]])
		result.append(ans.bestMove)
	return result
	
if k.depth == "full":
	if FUTURE_COUNT <=0: bail()
	moves = katagoDream(FUTURE_COUNT)
	for i, m in enumerate(moves):
		ghost(m, k.toPlay)
		if USE_NUMBERS:
			mark(m, i+1)

	mark((k.xsize//2, -0.5), f"({k.toPlay} wants stones here)")
