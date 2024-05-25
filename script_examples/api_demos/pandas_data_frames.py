# Data Frames
# KataQuery has pandas support for the
# people who like it.

# There are two dataframes: 
# k.dfInfos -- all information for both legal and illegal plays
# k.dfRoot -- general position information, single row

# You probably want k.dfInfos, which is dataframe version
# of (k.pass_move + k.intersections)

# in addition to the standard columns (policy, etc.)
# k.dfInfos also provides these columns:
# 'x', 'y', 'info' 

# The 'info' column contains the original moveInfo python object,
# which is convenient for marking up the board

# ANYHOO...
# Let's find invasions and harrassments
# by selecting moves that play close to or inside
# enemy territory.

# Also, highlight the ideas that are also suggested moves.

PERIL = slider1("Peril")
MOVE_COUNT = slider2("Move Count", min_value=1, max_value=20, value_type="int", default_value=5)

clearLog()
log(f"Peril: {PERIL}")
log(f"Move Count: {MOVE_COUNT}")

clearAll()
df = k.dfInfos
df = df.query("legal")
df = df.query("ownershipOpponent > @PERIL")
df = df.sort_values("mergedOrder")
df = df.head(MOVE_COUNT)

clearAll()

for m in df['info']:
	mark(m)
	if m.isMove:
		heat(m, 1)
		hover(m, m.pv)
