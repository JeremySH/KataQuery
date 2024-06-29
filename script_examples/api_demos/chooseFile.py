# chooseFile()
# Ask for a filename to load or save to.
# Does not actually open the file, 
# you must use python's open() for that

# example uses, doesn't open or save
LOAD = button1("LOAD")
SAVE = button2("SAVE")
QUICKIE = button3("QUICKIE")

# this button will actually save an SGF
SAVE_SGF = button4("Save SGF")

# when default= keyword is used, the dialog box
# navigates to the path provided,
# or the working directory if it's the empty string

persist("defaultName", "")
name = None

clearLog()
if LOAD:
	name = chooseFile("Open What?", default=defaultName)

	if name:
		log("you opened ", name)
	else:
		log("you canceled.")
			
if SAVE:
	name = chooseFile("Save What?", save=True, default=defaultName)

	if name:
		log("you saved", name)
	else:
		log("you canceled.")

if QUICKIE:
	# short version opens file
	name = chooseFile() 
	
	if name:
		log("you opened ", name)
	else:
		log("you canceled.")

if SAVE_SGF:
	name = chooseFile("Save To:", save=True)
	sgf = k.goban.asSGF()
	
	with open(name, "w") as file:
		file.write(sgf)

if name:
	defaultName = name