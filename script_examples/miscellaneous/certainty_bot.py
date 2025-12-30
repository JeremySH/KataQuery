# Certainty Bot

# A bot that uses "certainty" for move decisions, instead of visits.
# This keeps KataGo's move quality more consistent.

# more usefully, analyzing by a consistent certainty can stablise the
# conclusions you make using KataGo's analysis data (e.g. scoreLead).

# NOTE: high certainty (> 98%) takes much visits!

# CALCULATION
# uncertainty  = k.bestMove.utility- k.bestMove.utilityLcb
# certainty    = 1.0 - uncertainty

persist("HUMAN", "black")
VISIT_LIMIT = 3000

CERTAINTY = slider1("certainty", default_value=0.75)
CHOOSE_HUMAN = button1("Player...")

if CHOOSE_HUMAN:
	b = msgBox("Who do you play?", buttons=["black", "white", "neither"])
	HUMAN = b

def analyze_til_error(goban, error, maxVisits, allowedMoves=None, ghostUpdates=True):
	"""
	analyze `goban` until bestMove.utility - bestMove.utilityLcb < error, 
	giving up after `maxVisits`.
	return (kataanswer, error_utility, error_winrate) with this analysis
	"""
	# visits are added in chunks of 50
	# so that the final error value "kinda" hits the same spot
	# every time..
	
	e = 2.0 # greater than max as a starter value
	v = 0   # visits
	a = None # answer
	best = None
	
  # we need at least 2 visits to get bestMove info
	maxVisits = max(2, maxVisits)
	error = min(1, error)
		
	while e > error:
		if v >= maxVisits:
			break
		else:
			v = min(maxVisits, v+50)
			a = analyze(goban, allowedMoves=allowedMoves, visits=v)
			v = a.visits
			e = a.bestMove.utility - a.bestMove.utilityLcb
			e2 = a.bestMove.winrate - a.bestMove.lcb
			if ghostUpdates:
				if best:
					clearGhosts()
					mark(best, "")
				best = a.bestMove.pos
				ghost(best, a.player)
				mark(best, f"{e*100:0.0f}")
				status(f"calculating... visits {a.visits} | {e} {a.bestMove.utility-a.bestMove.utilityLcb}")
				snooze(.001)
	
	return a, e, e2

clearLog()
log(f"Minimum Certainty: {CERTAINTY*100:0.1f}")

if k.player == HUMAN:
	clearAll()
	status(f"{HUMAN} to play.")
	bail()

if k.depth == "full":
	allowed = [m.pos for m in k.allowed_moves]
	clearAll()
	status("calculating...") ; snooze(0.1)
	ans, error, wrErr = analyze_til_error(k.goban, 1.0-CERTAINTY, maxVisits=VISIT_LIMIT, allowedMoves=allowed)
	ghost(ans.bestMove, ans.player)
	mark(ans.bestMove, round((1-error)*100))
	status (f"Certainty: {(1-error)*100:0.1f} (util), {(1-wrErr)*100:0.1f} (wr) | visits: {ans.visits}")
else:
	clearAll()
	error = k.bestMove.winrate - k.bestMove.lcb
	ghost(k.bestMove, k.player)
	mark(k.bestMove, round((1-error)*100))
	status (f"Certainty: {(1-error)*100:0.1f}")
