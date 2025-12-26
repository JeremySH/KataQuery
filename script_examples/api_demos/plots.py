# Plots
# matplotlib is a big hack right now.
# By default, plt.show() creates a new window every time,
# which can be frightening when the script is rerun
# every millisecond

# there are two workarounds:
# 1. protect plt.show() with a GUI button, so it creates
#    a new window on-demand
# 2. use figure(num=1) to reuse a figure window

# both are shown below

import pandas as pd
import matplotlib.pyplot as plt
plt.ion() # interactive mode is REQUIRED 

SHOW_SCATTER = button1("scatter plt")

if k.depth == 'quick':
	bail()

if SHOW_SCATTER:
	# this is easier, but plt.show() creates new windows,
	# so we protect it with a GUI Button
	clearAll()
	df = k.dataframe
	df = df.query('isMove')
	df = df[['winrate', 'scoreLead']]
	df.plot.scatter(y='winrate', x='scoreLead')
	plt.show()
	bail()

# REUSING A FIGURE WINDOW
# by specifying a figure ID (aka "num") we use the same window
# over and over:
fig = plt.figure(num=1)

# but we need to make sure the axes and/or layout is legit
# for our purpose.
if len(fig.get_axes()) == 1:
	axis = fig.get_axes()[0]
else:
	for a in fig.get_axes():
		fig.delaxes(a)
	axis = fig.add_subplot()

# clean previous labels, etc
axis.clear()

# munge some data
df = k.dataframe
df = df.query('legal')
df = df.sort_values('policy', ascending=False)
df = df[['policy', 'coords', 'info']]

# plot it, using proper axes (ax=axis)
df = df.set_index('coords')
df.plot.pie(y='policy', ax=axis, legend=False)
fig.show() # NOTE: don't use plt.show()!
		
# mark up the board for easy cross-ref
clearAll()

for m in df['info'][:10]:
	mark(m, m.coords)

clearLog()
log("Top Policy Value: ", df.iloc[0]['policy'])


