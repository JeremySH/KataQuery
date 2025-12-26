# chooseFile()
# Ask for a filename to load or save to.
# Does not actually open the file, 
# you must use python's open() for that

# example uses, doesn't open or save
QUICKIE = button1("QUICKIE")
LOAD = button2("LOAD")
SAVE = button3("SAVE")

# this button will actually save an SGF
SAVE_SGF = button4("Save SGF")

# when default= keyword is used, the dialog box
# navigates to the path provided,
# or the working directory if it's the empty string

persist("defaultName", "")
name = None

clearLog()
if QUICKIE:
	# quick and simple
	name = chooseFile() 
	
	if name:
		log("you opened ", name)
	else:
		log("you canceled.")
		
if LOAD:
	# `multi` enables multiple selection and returns a list
	name = chooseFile("Open What?", default=defaultName, multi=True)

	if name:
		log("you opened ", name)
	else:
		log("you canceled.")
			
if SAVE:
	# `save` presents a save dialog
	name = chooseFile("Save What?", save=True, default=defaultName)

	if name:
		log("you saved", name)
	else:
		log("you canceled.")

if SAVE_SGF:
	# `extension` appends the given extension
	name = chooseFile("Save To:", save=True, extension="sgf")
	
	if name: 
		sgf = k.goban.as_sgf()
	
		with open(name, "w") as file:
			file.write(sgf)

if name:
	defaultName = name