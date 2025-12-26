# functional examples
# functions like k.reduce(), k.map()
# use a functional style, for those who
# like it.

# Each takes an eval_string that uses variable 'm'
# to compute values against a move/interseection, e.g.:

most_settled = k.max("abs(m.ownership)")

# which will return the intersection info object
# that has the highest ownership.

# If vector is not supplied, the function is applied
# to every intersection and the pass move.

# These methods can also take functions/lambdas instead
# of eval_strings, if desired.

# Generators are never returned (it's lists only), 
# because you cannot reuse generators.


clearAll()

EXTRA_HELP = False # True dumps docs to console

def by_dist(m):
	"example function to pass to k.min()"
	if k.last_move:
		return dist(m, k.last_move)
	else:
		return 0

# get the best score move:
best_score_move  = k.max("m.scoreLead", k.moves)

# find a hugger move (using a function instead of string)
hugger = k.min(by_dist, k.moves)

# mark weak black stones
for m in k.filter("m.color=='black' and m.ownershipBlack < 0.5"):
	mark(m, "?")
	
# quick sorting:
print("Best Ideas:")
print(k.map("m.coords", k.sorted("-m.policy"))[:5])

# map some winrates to percent and mark them
winrates_percent = k.map('round(m.winrate*100)', k.moves)
for wr, move in zip(winrates_percent, k.moves):
	mark(move, wr)

# filterv() is special as you can apply filters
# in succession
for m in k.filterv("m.isMove", "m.policy > 0.05"):
	heat(m, 1.0)

# calculate the territorial score using reduce().
# reduce uses TWO arguments, "m" and "acc"
# you can use any starting value for acc
# Here, we use 0.
s = k.reduce(0, "acc + round(m.ownership)")
if s < 0:
	status(f"Current score: B+{-s - k.komi}")
else:
	status(f"Current score: W+{s + k.komi}")
	
mark(best_score_move, "square")
mark(hugger, "H")

# find invasion/reduction moves
inv = k.filter("m.legal and m.ownershipOpponent > 0.5")
inv = k.sorted("-m.policy", inv)
if len(inv):
	mark(inv[0], "INV")

# other functional style functions:
if EXTRA_HELP:
	for func in [k.takewhile, k.takeuntil, k.min, k.avg, k.sum]:
		help(func)


