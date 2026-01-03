# goban2gif
# must be manually run (CMD-R)

# convert all the moves in the current position to a tiny animated GIF
# and save it.

# Also, inject the whole SGF into the comment field
# of the GIF?
SGF_IN_COMMENT = False

from PIL import Image

if not k.manual_run:
	bail()

images = []

g = k.goban.copy()
g.clear()

stones, moves = k.goban.stones_n_moves()
setup = Image.new("P", (k.xsize, k.ysize), 2)
setup.putpalette([0,0,0, 255,255,255, 249,200,0 ], rawmode="RGB")

# place setup stones if any
for color, stone in stones:
	g.place(color, stone)

	x,y = stone[0], k.ysize-stone[1]-1
	
	if color[0].upper() == "B":
		color = 0
	else:
		color = 1

	setup.putpixel((x,y), color)

# construct frame for every postion 
image = setup
for color, move in moves:
	image = image.copy()
	prev = g.copy()
	g.play(color, move)

	for intersection in g.diff(prev):
		x,y = intersection[0], k.ysize-intersection[1]-1
		col = g.get(intersection)
		if col == "black":
			image.putpixel((x,y,), 0)
		elif col == "white":
			image.putpixel((x,y,), 1)
		elif col == "empty":
			image.putpixel((x,y,), 2)
			
	images.append(image)
		
filename = chooseFile(save=True, extension=".gif")

comment = None
if SGF_IN_COMMENT:
	comment = k.goban.as_sgf()
	
if filename:
	setup.save(filename, 
		format="gif",
		save_all=True, 
		append_images=images, 
		duration=10, 
		loop=0,
		comment = comment,
		background = 2)
