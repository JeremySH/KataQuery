# Some basic use examples.
#
# scripts could stack in the future, but for now
# we must clear the board every analysis
# if we don't want junk hanging around
clearMarks() ; clearStatus() ; clearHeat()

# or simply:
clearAll()

# set the status line:
status(f"{k.toPlay} to play | scorleadBlack: {k.scoreLeadBlack}")

# mark by tuple
mark((9,9), "square") # "circle" "square", "triangle" or any text

# mark by info object -- a little easier
m = k.moves[0] # the best move
mark(m, "circle")

# mark by move position
# k.moves[-1] is least favorable suggestion
mark(k.moves[-1].pos) # uses default triangle

# generate some heat on the board
for i in k.intersections:
	heat(i, i.ownershipHeat)

# get a future play analysis:
# this is rather ugly ATM 
# NOTE; it also blocks the GUI, so be judicious
if k.depth == 'full': # only when full analysis ready
	future = quickPlay(k, [[k.toPlay, k.moves[0].coords]])
	mark(future.moves[0], "F")

# save variables across runs:
# NOTE: only works at top-level scope
persist("count", 0) # name, starting value

count = count+1
print("run count: ", count) # goes to terminal output

# iterate over stones on the board:
for s in k.stones:
	if s.color == "black":
		mark(s, "B")
	else:
		mark(s, "W")

# when you need to get an info by intersection
m = k.get_point((3,3,))
print("4-4 value: ", m.policy)

# showing a quick display as stones are dragged:
# This is  when visits are speedy and low, like 2
if k.depth == 'quick': # either 'quick' or 'full'
	for i,m in enumerate(k.moves_by_policy[:10]):
		mark(m, i+1)

# set the clipboard:
# NOTE: commented out to be nice
# set_clipboard("THANKS FOR PLAYING")
# print(get_clipboard())

# determining opponent:
print(f"my opponent is {opponent(k.toPlay)}")


# ITERATIONS
# these are lists you can iterate over or do
# list-type stuff with

for m in k.moves: # suggested moves
	pass

for m in k.stones: # stones on board
	pass

for m in k.white_stones: # white stones
	pass

for m in k.black_stones: # black stones
	pass

for m in k.legal_moves: # all legal moves (including (-1,-1) which is pass)
	pass

for m in k.illegal_moves: # illegal moves
	pass

for m in k.moves_by_policy: # legal moves, but sorted by policy value
	pass

for m in k.empties: # empty intersections
	pass
