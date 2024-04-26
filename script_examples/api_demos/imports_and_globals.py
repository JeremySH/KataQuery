# shows the quirks of importing and global scope
# this behavior will be fixed Sometime™

AM_I_TRULY_GLOBAL = "who knows?"

from functools import reduce
from statistics import mean

def getMean(values):
	# global imports are lost inside function scope unless you 
	# declare them global or import, e.g.:
	# global mean # OR:
	from statistics import mean

	return mean(values)

def global_check():
	# fails unless you use global keyword to rescope
	# global AM_I_TRULY_GLOBAL
	print("Truly global? ", AM_I_TRULY_GLOBAL) 

# works fine at top level
policies = [p.policy for p in k.moves]
pMax = reduce(max, policies)
pMin = reduce(min, policies)
pMid= getMean(policies)

#global_check() 

status(f"POLICY NET STATS | max: {pMax} | min: {pMin} | median: {pMid}")