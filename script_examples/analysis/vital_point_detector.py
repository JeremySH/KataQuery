# VITAL MOVE DETECTOR
# a "vital move" is a top move that has an exceedingly higher
# score than other move candidates. It's' considered "necessary"
# by KataGo.

# This is calculated by comparing the winrate drop
# between ranked moves, and if the gap is big enough,
# then the top moves are considered "elite,"
# and returned as vitals

# anecdotally, pros can see vitals when the gap is about 9%
# and everybody can see them when it's > 50%

def vitals(vitals_gap=9.0):
	"return detected (vitals, gap) if any"
	# winrates are normalized to k.winrateMax
	# to prevent tiny or huge winrates from screwing
	# up the calculation.
	
	if len(k.moves) < 2: return [], 0
        
	bestRate = k.winrateMax
	worstRate = k.winrateMin
	winRange = bestRate-worstRate
	
	ratio = lambda a,b: a/(b+1e-9) 

	lastRate = 1.0
	
	candidates = []
	drop = 0.0
	found = False
	for m in k.moves:
		thisrate = m.winrate/k.winrateMax 
		drop = (1.0 - ratio(thisrate,lastRate))*100.0        
		if drop > vitals_gap: # big drop, anything above this is vital
			found = True
			break
		else:
			lastRate = thisrate
			if len(candidates) > 2: break
			else:
				candidates.append(m)
				
	if found:
		return candidates, drop
	else:
		return [], 0

clearAll()
vit, drop = vitals()

for i, v in enumerate(vit):
	mark(v, "♢", scale= 0.75+(len(vit)-i)/(len(vit)))

if len(vit):
	# put a title on the board margin
	S=""
	if len(vit)>1: S="S"
	mark( (k.xsize/2, -0.5), f"♢ VITAL{S} BY {round(drop)}%")
