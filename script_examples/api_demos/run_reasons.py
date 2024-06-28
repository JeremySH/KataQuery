# Different run reasons
# that you can test.
# Try stuff, and watch the
# GUI log

check1("check me!")

clearLog()

if k.manual_run:
	msgBox("You ran me!")

if k.gui_run:
	log("A GUI control triggered me.")

# k.depth will be either "full" or "quick"

# "full" when full visits are used:
if k.depth == "full":
	log(f"k is a full analysis, moves available: {len(k.moves)}")

# "quick" when user is dragging stones around:
if k.depth == "quick":
	log(f"k is a quick analysis, moves available: {len(k.moves)}")

