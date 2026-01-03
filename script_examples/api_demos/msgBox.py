# An Obvious Nag
# Show a message box every time an obvious move appears.
# msgBox() will return the name of the button
# that was clicked

persist("IGNORE_ME", False)

THRESHOLD = 200

clearAll()

# only do it when mouse released
if k.depth == 'quick' or IGNORE_ME:
	bail()

found = []
for m in k.moves_by_policy:
	if m.policy*len(k.legal_moves) > THRESHOLD:
		found.append(m)
		
if len(found):
	for f in found:
		heat(f, f.policy*(len(k.legal_moves))/THRESHOLD)
	
	mess = "an obvious move"
	if len(found) > 1:
		mess = "some obvious moves"
		
	buttonReturned = msgBox(f"I found {mess} for you.",
		buttons=["Thanks", "Shut up"])

	if buttonReturned == "Shut up":
		IGNORE_ME = True

status(f"{k.player} to play")