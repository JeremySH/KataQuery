# COPY SGF
# you can set clipboard to arbitrary text

# only activates on ctrl-R (Code->Run)

clearStatus()

if k.manual_run:
	sgf = f"(;GM[1]FF[4]CA[UTF-8]SZ[{k.xsize}:{k.ysize}]"

	sgf += f"PL[{k.toPlay[0].upper()}]"

	letters = 'abcdefghijklmnopqrstuvwxyz'

	if len(k.black_stones):
		sgf += "AB"
		for s in k.black_stones:
			coord = letters[s.pos[0]] + letters[k.ysize-s.pos[1]-1]
			sgf += f"[{coord}]"

	if len(k.white_stones):
		sgf += "AW"
		for s in k.white_stones:
			coord = letters[s.pos[0]] + letters[k.ysize-s.pos[1]-1]
			sgf += f"[{coord}]"

	sgf += ")"


	set_clipboard(sgf)
	status("SGF copied to clipboard")