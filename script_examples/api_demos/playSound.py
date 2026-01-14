# playSound() -- play a sound

# playSound() can always play .wav
# but may also be able to play mp3, mp4, ogg
# depending on platform

# volume is from 0 to 100, e.g.
# playSound("My file.wav", volume=50)

BEEP   = button1("BEEP")
CUSTOM = button2("CUSTOM SOUND")
STOPIT = button3("STOP")

VOLUME = 50

if k.manual_run:
	# missing sounds are ignored
	playSound("I don't exist")
	msgBox("Hm")

if BEEP:
		# play the system alert sound
		playSound("beep")
		msgBox("Beep!")

if CUSTOM:
		# play stuff like .wav, .mp3, etc (if available)
		soundfile = chooseFile()
		if soundfile:
			playSound(soundfile, VOLUME)

if STOPIT:
		# stop all playback
		playSound(None)
