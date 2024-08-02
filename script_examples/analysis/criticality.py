# Criticality
# Works best with 15b network (provides more data)

# This measures the median deviation from the top move's
# winrate. In other words, it gauges how crucial it is
# to play a top move.

# You can think of it as the risk of "winrate loss."
# E.g. in life or death situations, criticality is
# very high.

# High criticality (> 10) implies sente, vital points, big moves. 
# Low Criticality implies tenuki, safe positions, open play...

# A "Fake Komi" can be used to equalize player points 
# when the score is too lopsided to find deviations.

from statistics import median
import pandas as pd
import matplotlib.pyplot as plt
plt.ion() # needed to show plot window

GRAPH_IT = check1("winrate graph", default_value=True)
RESCALE = check2("equalize with komi")

if len(k.moves) <= 1:
	bail()

# *** functions ***
def criticality(ans):
	"measure median winrate devation from the top move"
	if len(ans.moves) <= 1:
		return 0

	byWinrate = sorted(ans.moves, key=lambda m: -m.winrate)
	wrs = [w.winrate for w in byWinrate]
	top = max(wrs)
	
	# treat the top move as the "standard"
	# and compare all other values to it
	dev = [top-w for w in wrs[1:]]
	
	med = median(dev)

	return med

def rescale(thisAnswer):
	"adjust komi of thisAnswer to equalize position and return new kata answer"
	newKomi = thisAnswer.komi + round(thisAnswer.scoreLeadBlack*2)/2
	newKomi = max(min(150, newKomi), -150)
	g = thisAnswer.goban.copy()
	g.komi = newKomi
	return analyze(g, visits=k.visits)

def graphWinrates(ans):
	"graph all winrates of visited moves in ans"
	df = ans.dfInfos
	df = df.query("isMove").sort_values('winrate', ascending=False)
	df = df.head(20)
	df['rank'] = range(1, len(df)+1)
	df = df[['winrate', 'rank']]

	fig = plt.figure(num=1)
	
	for ax in fig.get_axes():
		fig.delaxes(ax)
	
	a = fig.add_subplot()
	
	df.set_index('rank')
	df.plot.bar(ax=a, x='rank', y="winrate")

# *** MAIN PROGRAM ***

clearAll()

ans = k

if RESCALE:
	ans = rescale(k)

wrb = round(k.winrateBlack*100)
wrw = round(k.winrateWhite*100)

# criticality is from 0-100
c = round(criticality(ans)*1000)/10
status(f"criticality: {c} | B {wrb}% | W {wrw}%")
mark((k.xsize//2, -0.5), f"criticality: {c}", scale = 0.75 + c/40)

if RESCALE:
	mark((k.xsize//2, k.ysize-0.5), f"fake komi: {ans.komi}")

# mark moves for the graph
for i, m in enumerate(sorted(k.moves[:20], key=lambda w: -w.winrate)):
	mark(m, i+1)
	
# graph winrates to get an idea of distribution
if GRAPH_IT:
	if k.depth == "full":
		graphWinrates(ans)
else:
	plt.close()