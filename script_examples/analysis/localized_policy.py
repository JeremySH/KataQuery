# Localized Policy
# get similar "policy" values
# when localize is used

# here, localized policies are rescaled to their 
# own domain instead of the entire board, 
# which gives a more consistent impression
# of value

# use the checkbox and Localize... menu to observe effect

LOCALIZE_POLICY = check1("localize pol", default_value=True)
MOVES_PER_STONE = dial1("move limit", min_value=1, max_value=10, default_value=3, value_type="int")

clearLog()
log(f"Moves Shown Per Stone: {MOVES_PER_STONE}")

def normalizePolicy(ans):
	"renormalize policy to allowed moves"
	sumPol = sum(p.policy for p in ans.allowed_moves)
	for m in ans.moves_by_policy:
		m.policy = m.policy/sumPol

if LOCALIZE_POLICY:
	normalizePolicy(k)
	
clearAll()

ourMoves = sorted(k.allowed_moves, key=lambda m: -m.policy)

limit = max(len(k.stones)*MOVES_PER_STONE, MOVES_PER_STONE)

for m in ourMoves[:limit]:
	p = round(len(k.legal_moves) * m.policy)
	mark(m, p)

status(f"{k.player} to play")

# note that we multiply by len(k.legal_moves) instead
# of len(k.allowed_moves) for the simple reason
# that the number remains similar whether you have
# localize turned on or off

