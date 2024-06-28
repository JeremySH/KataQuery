# Some basic use examples.
#
# scripts could stack in the future, but for now
# we must clear the board every analysis
# if we don't want junk hanging around
clearMarks() ; clearStatus() ; clearHeat()

# or simply:
clearAll()

# connect & use GUI (see GUI_demo.py for more info)
HELLO_WORLD = button1("Hello World")
if HELLO_WORLD:
	# button was pressed, so:
	msgBox("Hello world!")

# log to GUI (see GUI tab):
clearLog() # log is cleared separately from clearAll()
log("Welcome to the World of Go!")

# set the status line:
status(f"{k.toPlay} to play | scorleadBlack: {k.scoreLeadBlack}")

# mark the board by gopoint tuple
mark((9,9), "square") # "circle" "square", "triangle" or any text

# mark by info object -- a little easier
m = k.moves[0] # the best move
m = k.bestMove # also the best move
mark(m, "circle")

# mark by move position
# k.moves[-1] is least favorable suggestion
mark(k.moves[-1].pos) # uses default triangle

# generate some heat on the board
# with floats from 0.0 to 1.0
for i in k.intersections:
	heat(i, i.ownershipHeat)

# get a future play analysis.
# NOTE this blocks the GUI, so be judicious with visits
if k.depth == 'full':
	# grab the current goban
	goban = k.goban

	# play the best move on it
	goban.play(k.toPlay, k.bestMove.pos)
	
	# analyze
	future = analyze(goban, visits=2)
	
	# mark future move
	mark(future.bestMove, "F")

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

# showing a quick display as stones are dragged
# This is  when visits are speedy and low, like 2
if k.depth == 'quick': # either 'quick' or 'full'
	for i,m in enumerate(k.moves_by_policy[:10]):
		mark(m, i+1)
		# place a "ghost stone"
		ghost(m, k.toPlay)

# set the clipboard:
# NOTE: commented out to be nice
# set_clipboard("THANKS FOR PLAYING")
# print(get_clipboard())

# determining opponent:
print(f"my opponent is {opponent(k.toPlay)}")

# RUN REASONS
if k.manual_run:
	print("I was run manually")

if k.gui_run:
	print("I was run by GUI")
	
if k.depth == 'full':
	print("I was run with full analysis")

if k.depth == 'quick':
	print("I was run in quick mode.")

if k.visits > 1000:
	print("Okay, you like them visits don't you?")


# ITERATIONS
# these are lists of move infos you can iterate over or do
# list-type stuff with

# e.g.:
text = "KataGo Prefers: "
for m in k.moves: # suggested moves
	text += m.coords + " "
	pass
print(text)

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
