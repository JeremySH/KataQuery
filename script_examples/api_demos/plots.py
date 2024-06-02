# Plots
# matplotlib is a big hack right now.
# By default it opens a new window per plt.show(),
# which can be frightening when the script is rerun
# every millisecond

# there are two workarounds:
# 1. protect plt.show() with a GUI button, 
#    so that user gets a new plot
#    on-demand instead of automatically
# 2. persist a figure and reuse the same window

# both are shown below

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

SHOW_SCATTER = button1("scatter plt")
SHOW_WR = button2("winrate plt")

# we must persist both the figure and the axis
# it uses
persist("fig", None)
persist("axis", None)

if k.depth == 'quick':
	bail()

if SHOW_SCATTER:
	# this will create a new window every run,
	# which is default behavior. It is protected by a button
	# so window creation doesn't get out of control
	clearAll()
	df = k.dfInfos
	df = df.query('isMove')
	df = df[['winrate', 'scoreLead']]
	df.plot.scatter(y='winrate', x='scoreLead')
	plt.show()
	bail()

if SHOW_WR:
	# creates new window
	clearAll()
	df = k.dfInfos
	df = df.query("isMove")
	df = df[['winrate', 'info', 'coords']]
	df = df.sort_values('winrate', ascending=False)
	df.plot.bar(y='winrate', x='coords', legend=False)
	for m in df['info']:
		mark(m, m.coords)
	bail()

	
# SHOW POLICY PIE
# this updates the same window over and over,
# so it's safe to automatically rebuild
# the chart every run

# Key points:
# 1. Create persisted figure (persist("figure"))
# 2. enable ion() (interactive mode)
# 3. delete and re-add the axes every time

# it takes a while to render the plot, so
if k.depth != "full":
	bail()

# create a persisted figure
if not fig:
	fig = plt.figure()

plt.ion() # interactive mode is required 

# you must de/reconstruct the axis because
# its labels stick around otherwise
if axis:
	fig.delaxes(axis)
	
axis = fig.add_subplot()

df = k.dfInfos
df = df.query('legal')
df = df.sort_values('policy', ascending=False)
df = df[['policy', 'coords', 'info']]

# plot it. MAKE SURE YOU USE THE PERSISTED FIGURE'S AXIS
# as this will force an in-place update
df = df.set_index('coords')
df.plot.pie(y='policy', ax=axis, legend=False)
fig.show()

clearAll()

for m in df['info'][:10]:
	mark(m, m.coords)

clearLog()
log("Top Policy Value: ", df.iloc[0]['policy'])


