# KataGoQueryError
# you can catch query errors during analyze() 
# with KataGoQueryError.

# see the GUI Log

g = k.goban.copy()
g.komi = 300 # out of range

clearLog()
try:
	a = analyze(g)
except KataGoQueryError as e:
	# these are the attributes avaiable
	log(e.message)
	log("field:", e.field)
	log(e.contents) 
	# the katago response as dictionary	
	log("e.contents type: ", type(e.contents))
