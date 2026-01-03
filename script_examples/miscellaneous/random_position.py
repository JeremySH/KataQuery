# Random Position
# Generate rational but unique positions

HELP_TEXT="""
This script will quickly generate a random position based on \
the current board, then bookmark it. 

Choose a Board Coverage limit, and click "GENERATE"
"""

JOSTLE = 0.5

COVERAGE = dial1("board coverage", default_value=0.15)
GENERATE = button1("GENERATE")
HELP = button2("HELP")


if HELP:
	msgBox(HELP_TEXT)
	bail()
	
def attain_weirdness(ans, max_dist=3):
	"pick a move further away from best move, which leads to creative positions"
	import random
	if not ans.last_move:
		return ans.bestMove

	focusMove = random.choice([ans.bestMove, ans.last_move])
	moves = ans.moves_by_policy[:5]
	moves = [m for m in moves if dist(m, focusMove) < max_dist]
	moves = sorted(moves, key=lambda m: -dist(m,focusMove))

	if len(moves):
		return moves[0]
	else:
		return ans.bestMove

def gen_position(gob = None, jostle=0.5, coverage=0.5):
	"generate a position and bookmark it"
	import random
	if not gob:
		gob = k.goban.copy()
		gob.clear()
		gob.player = "black"
	
	ans = analyze(gob)
	while len(ans.stones) < coverage*gob.xsize*gob.ysize:
		
		m = ans.bestMove
		if ans.pass_move == m:
			break
		
		if ans.winrate > 0.45 and jostle > random.random():
			m = attain_weirdness(ans)
			#m = random.choice(ans.moves_by_policy[:5])
		
		gob.play(gob.player, m)
		ghost(m, gob.player)
		snooze()
		gob.player = opponent(gob.player)
		ans=analyze(gob)
	
	bookmark(gob, location="end")
	status("Position bookmark generated. Scroll to it.")

clearAll() ; clearLog()
log(f"Board Coverage: {COVERAGE*100:0.0f}%")

if GENERATE:
	gen_position(gob=k.goban, jostle=JOSTLE, coverage=COVERAGE)
