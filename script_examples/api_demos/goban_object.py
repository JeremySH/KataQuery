# Goban Object
# The "k.goban" object is a virtual board of the
# current position which can be played on, 
# converted to SGF/ascii, used to calculate 
# liberties and so on.

COPY_SGF = button1("Copy SGF")
COPY_DIAGRAM = button2("Copy Diag")
HELP = button3("HELP")

g = k.goban.copy() # copy() just in case

print(g.as_ascii())
print(g.as_sgf())

clearLog(); clearAll()

if HELP:
	help(k.goban)
	log("HELP DUMPED TO CONSOLE...")

# coords can be tuple, string, or moveInfo object,
# although tuple is preferred
for coord in [(3,3), 'd4',  k.bestMove]:
	print(type(coord), "legal?", g.legal(k.toPlay, coord))

# groups are lists of tuples (e.g. "[ (3,3), (3,4) ]")
# of the directly connected stones of black and white:
blacks, whites = g.groups()
log(f"Number of black groups: {len(blacks)}")
log(f"Number of white groups: {len(whites)}")

# count the liberties for each group and mark the 
# stones with their group's lib count
lib_set = set()

for group in blacks + whites:

	# any stone in group will report its group's connected liberties
	# with g.libs()
	# so just use the first stone of the group
	count = len(g.libs(group[0]))
	lib_set.update(g.libs(group[0]))
	
	for stone in group:
		mark(stone, count)

status(f"Total liberties: {len(lib_set)}")

# sgf will retain move order if possible:
if COPY_SGF:
	set_clipboard(g.as_sgf())
	status("SGF copied.")

# collapse will convert into a single SGF node (diagram)
if COPY_DIAGRAM:
	g.collapse() # no moves, just stone placements
	set_clipboard(g.as_sgf())
	status("SGF diagram copied.")

# an example of using the play() method:

# make a play
g.play(k.toPlay, k.bestMove)
