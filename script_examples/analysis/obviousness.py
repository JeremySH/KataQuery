# Obviousness
# Calculate an "obviousness" score using the policy net.

# "Obvious" and "common" moves are
# moves that are well-tested by KataGo over 
# zillions of games. If you missed an OBV
# or "com" idea, it's an opportunity to understand
# it fully, as it will show up in your games
# over and over again.

# this uses
# policy value * len(k.legal_moves)
# to stabilize scores across positions

HIDE = check1("hide")
HOVER = check2("hover text")
MOVES_SHOWN = dial1("Moves Shown", default_value=10, min_value=1, max_value=50, value_type="int")

clearAll() ; clearLog()

if HIDE:
	bail()

log(f"MOVES SHOWN: {MOVES_SHOWN}")

# normalize for when board is in localize mode
sumPol = sum(p.policy for p in k.allowed_moves)

# prepare our list of policy moves
considered = [m for m in k.moves_by_policy if m.allowedMove]

for m in considered[:MOVES_SHOWN]:
	score = len(k.legal_moves)*m.policy/sumPol

	if score > 1:
		heat(m, score/50)
		
		if score > 100:  text = "OBV"
		elif score > 25: text = "com"
		elif score > 10: text = "unc"
		else:            text = "rar"

		mark(m, text, scale=0.9)
		
		if HOVER:
			hover(m, f"{m.coords}\nCommonality: {score:0.1f}")

status(f"{k.player} to play")