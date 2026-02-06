# print out the fields/methods
# etc. for kata analysis information
# so you can get an idea of what's
# available (see terminal output)

# NOTE: you don't have to "import kq"! It's
# imported automatically for your script, 
# similar to "from kq import *"
import kq

# print out general help
help(kq) # the built in KataQuery amenities
help(k)  # the global k, which your script always sees

clearStatus()

# an example intersection which isn't an "evaluated"
# move (unvisited). These intersections are missing
# many fields (such as winrate)

print("\n#### INTERSECTION INFO EXAMPLE ####")
i = k.get_point((0,0))

if len(k.illegal_moves):
	i = k.illegal_moves[0]

for key,val in i.items():
	if type(val) == str:
		print(f"'{key}': '{val}'")
	else:
		print(f"'{key}': {val}")

# an example intersection that is also an evaluated move.
# this will contain all kinds of stuff
print("\n#### MOVE INFO EXAMPLE ####")
for key,val in k.moves[0].items():
	if type(val) == str:
		print(f"'{key}': '{val}'")
	else:
		print(f"'{key}': {val}")

# functions and stuff for the global 'k'
print("\n#### dir(k) ####")
callables = []
primitive = []
other = []

for x in dir(k):
	if x[0] != "_":
		if callable(getattr(k,x)):
			callables.append(f"{x}()")
		else:
			if type(getattr(k,x)) in [int, float, bool]:
				primitive.append(f"{x}: {getattr(k,x)}")
				#print(x, ": ", getattr(k,x))
			else:
				if type(getattr(k,x)) is str:
					primitive.append(f"{x}: '{getattr(k,x)}'")
				else:
					other.append(f"{x}: {type(getattr(k,x))}")

for c in callables:
	print(c)

for p in primitive:
	print(p)

for o in other:
	print(o)

# k.answer is a raw answer dict
# with the basic json stuff
# that's passed to/from katago
print("\n#### k.answer ####")
for key, val in k.answer.items():
	if type(val) in [int, float, bool]:
		print(key, ": ", val)
	else:
		if type(val) == str:
			print(f"'{key}': ", "'" + val + "'")
		else:
			print(f"'{key}'", type(val))
