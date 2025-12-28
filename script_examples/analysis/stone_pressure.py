# Stone Pressure
# Here, the "pressure" of a stone is the change of score
# when it is removed.
# it indicates how much "work" a stone is doing 
# for the player's position.

# larger dots mean more pressure, "heavier" stone
# smaller dots mean less pressure, "lighter" stone

# press "Calc" to calculate


from statistics import mean

persist("scores", None)
persist("previous_k", k)

CALCULATE = button1("Calc")
NUMBERS = check1("Numbers")
WINRATE = check2("Winrate")

def pressure(point) -> tuple[float, float]:
	g = k.goban.copy()
	g.collapse()
	g.remove(point.pos)
	ans = analyze(g)
	if point.color == "black":
		point = k.scoreLeadBlack - ans.scoreLeadBlack
		winrate = (k.winrateBlack - ans.winrateBlack) *100
	else:
		point = k.scoreLeadWhite - ans.scoreLeadWhite
		winrate = (k.winrateWhite - ans.winrateWhite) *100

	return point, winrate
	
if k.thisHash != previous_k.thisHash or k.visits > previous_k.visits:
	scores = None # recalculate

kminus = k

clearAll()

if WINRATE:
	KIND = "winrate"
else:
	KIND = "points"


if CALCULATE or k.manual_run or k.gui_run:
	if not scores:
		scores = {}
		for s in k.stones:
			points, winrate = pressure(s)
			scores[s.pos] = {"points":points, "winrate": winrate}
	
	for stone, d in scores.items():
		score = d[KIND]
		
		hover(stone, f"Pressure: {round(score*10)/10}")

		if score < 1.0: continue
		
		if NUMBERS:
			mark(stone, round(score))
		else:	
			if KIND == "winrate":
				factor = 60
			else:
				factor = 25
				
			mark(stone, "●", scale = max(score/factor, 0.25))

	whiteAvg = 0
	blackAvg = 0

	if len(k.stones) > 1:
		whiteAvg = mean(scores[s.pos][KIND] for s in k.white_stones)
		blackAvg = mean(scores[s.pos][KIND] for s in k.black_stones)
	
	clearLog()
	log("Pressure Per Stone")
	log(f"B: {blackAvg}")
	log(f"W: {whiteAvg}")
	
mark(k.bestMove)
