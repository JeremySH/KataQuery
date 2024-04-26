# GUI ELEMENTS
# Interacting with the GUI controls is not necessary, of course.
# But when you want to use it, here is a guide.

# the GUI api is made to be easy, not robust. The GUI controllers
# aren't created or destroyed, they are CONNECTED to by your script.
# Once connected, your entire script is re-run on any GUI controller
# change -- as long as your script uses the GUI element in question.

clearAll()
# You both connect & retreive the current value of a GUI item
# at the same time:
show_policy = check1("Show Policy", default_value=True)

# here, we connect show_policy to checkbox 1. On first run,
# the GUI element "check1" will be renamed "Show Policy", it will
#  be checked as per default_value, and default_value will be 
# returned into show_policy.

# After the first run, check1() will always return the value as
# seen in the GUI.

# You can now use show_policy like any other variable:
if show_policy:
	for m in k.moves_by_policy[:20]:
		heat(m, m.policy*50)

# DO NOT use check1() etc. more than ONCE in your script.
# these functions change internal state, and it will get
# irrational.

# BUTTONS
# Buttons are easy:
hello = button1("Say Hello")

if hello: log("HELLO THERE")

# Buttons are ONLY true if the user just clicked them.
# i.e. they cannot be held down.

# SLIDERS
# sliders (aka "dials") have more settings than the above.
move_limit = slider1("Move Limit", default_value=0, min_value=0, max_value=100, value_type='int')

# You don't need to specify all the keywords.
# by default, sliders provide a float value from 0.0 to 1.0.
# You can only use two different value_types: "float" or "int"

for i,m in enumerate(k.moves_by_policy[:move_limit]):
	mark(m, i+1)

# THE LOG
# You can print to the GUI log:
log("Interesting moves marked with !")

# You can also clear the log, which is nice
# for displaying standard info:
clearLog()
for m in k.moves[:move_limit]:
	log(f"{m.coords} winrate: {m.winrate}")

# MODIFYING
# Modifying is easy. Just edit the default parameters
# and the GUI element will be updated, and its default re-set.
# (you may want to press cmd-R to update)
# Change the params in the following to see the effect
# in the GUI:
spamalot = check2("Spamalot!", default_value=False)
if spamalot:
	for _ in range(10):
		log("SPAM")
