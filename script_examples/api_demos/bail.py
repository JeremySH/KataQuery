# BAIL
# Use bail() to exit the script immediately.

if k.depth == 'quick':
	bail()
	
# redraw only on full analysis
clearAll() 
for m in k.moves:
	mark(m, m.order+1)
	