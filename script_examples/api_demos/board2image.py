# board2image()
# capture the board as an image
# which includes markings, etc

# the type is QImage
# for easily copying to clipboard, saving, etc.

if k.manual_run:
	# width is optional, and defaults to 1024
	image = board2image(1024)

	set_clipboard(image)

	# or save:
	#image.save("my image.png")
