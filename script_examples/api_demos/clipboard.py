# COPY SGF
# you can set clipboard to arbitrary text

# only activates on ctrl-R (Code->Run)

clearStatus()

if k.manual_run:
	sgf = k.goban.asSGF()
	set_clipboard(sgf)
	status("SGF copied to clipboard")