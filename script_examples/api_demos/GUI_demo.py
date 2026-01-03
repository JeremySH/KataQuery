# Move Ranks & Territory
# With some simple GUI controls

limit = dial1("max moves", value_type="int", max_value=100, default_value=20)
use_policy = check1("use policy")
show_terri = check2("Show Territory")
terri_limit = dial2("Terri Border")

clearAll()
clearLog()
log(f"MAX MOVES: {limit}")
log(f"TERRI THRESH: {terri_limit}")

if use_policy:
	log("using policy")
	policies = [p for p in k.moves_by_policy if p not in k.moves and p.allowedMove]
else:
	policies = []

movelist = [m for m in k.moves if m.allowedMove] + policies
for i, m in enumerate(movelist[:limit]):
	mark(m, i+1)
	
if show_terri:
	for i in k.intersections:
		if i.ownershipBlack >= terri_limit:
				heat(i, 1)
		if i.ownershipWhite >= terri_limit:
				heat(i, .01)

status(f"{k.player} to play")