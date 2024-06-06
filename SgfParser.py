"""
SgfParser

Mostly because I don't need all the fancy SGF features.

Supports komi, non-square sizes, PL[] W[] B[] AW[] AB[]
and composed points. Just enough for replay.

All other properties are stored in the syntax tree raw.

GameTrees are supported, though the replay only follows
the main line of the first game in a collection

An SgfNode can provide a list of constructed Gobans of each
position derived from the main line moves and placed stones

"""

# SGF file is just a S-expression pretending not to be.

# It's possible to make every term in the BNF a separate class,
# but the fact is it's just a list of lists of atoms.
# And as long as every entry has a type ("GameTree", "PropList", "AW")
# we're good

import sys
from goban import Goban
from goutils import *

# some value parsing functions

def _sgf2int(c): return ord(c)-97
def _int2sgf(i): return chr(i+97)

def toCoordList(cc:str, ysize: int) -> list[tuple[int, int]]:
	"convert sgf (possibly composed) coordinates to list of int tuple, given the board's ysize"
	parts = cc.split(":")
	result = []
	for part in parts:
		p = part.strip()
		if len(p) != 2:
			result.append((-1,-1))
			break

		x = _sgf2int(p[0])
		y = ysize - _sgf2int(p[1]) - 1
		result.append( (x, y,) )

	if len(result) > 1: # composed points
		r = []
		for x in range(result[0][0], result[1][0]+1):
			for y in range(result[1][1], result[0][1]+1):
				r.append( (x, y) )
		return r

	return result

def toCoord(cc:str, ysize: int) -> tuple[int, int]:
	coords = toCoordList(cc, ysize)
	return coords[0]

def toSize(val:str) -> tuple[int, int]:
	i = val.find(":")
	if i >= 0:
		sz = [int(v) for v in val.split(":")]
	else:
		sz = [int(val), int(val)]
	return sz[0], sz[1]

def toColor(val:str) -> str:
	if val[0].upper() == "W":
		return "white"
	elif val[0].upper() == "B":
		return "black"
	else:
		return None

# Syntax Tree
class SgfNode:
	"the syntax tree"
	def __init__(self, key, val):
		self.key = key
		self.value = val
		self.children = []
		self.parent = None
		self.index = 0

	def addChild(self, node: 'SgfNode') -> None:
		node.parent = self
		node.index = len(self.children)
		self.children.append(node)

	def find(self, key, mainlineOnly=True):
		"find first node with this key"
		if self.key == key:
			return self
		
		for p in self.children:
			if p.key == "GameTree" and mainlineOnly:
				found = p.find(key)
				return found

			found = p.find(key)
			if found:
				return found

	def findAll(self, key, mainlineOnly=True):
		"find all nodes with this key"
		result = []
		if self.key == key:
			result.append(self)
		
		for c in self.children:
			result.extend(c.find(key))
			if c.key == "GameTree" and mainlineOnly:
				return result

		return result

	def pprint(self, depth:int =0) -> None:
		"pretty print the tree, basically outputting to pseudo SGF"
		if self.key == "GameTree":
			print(" "*depth + "(")

		for p in self.children:
			if p.key == "PropList":
				print(";")
				p.pprint(depth+1)
			elif p.key == "GameTree":
				# only the main line
				p.pprint(depth+1)
				print(" " * depth + ")")
				break
			else:
				print(f"{p.key}[{p.value}]", end='')

	def toGobanList(self, boards:list['Goban'] or None =None, testPrint=False) -> list['Goban']:
		"construct a goban for every new position and return these as a list"
		if boards == None:
			sz = self.find('SZ')
			#print("SZ FOUND: ", sz.value)
			if sz:
				x,y = toSize(sz.value)
				g = Goban(x,y)
			else:
				g = Goban() # guess 19x19
			komi = self.find("KM")
			if komi:
				try:
					k = float(komi.value)
					g.komi = k
				except ValueError:
					pass

			boards = [g]
		else:
			g = boards[-1]

		for p in self.children:
			showit = True
			
			if p.key == "PropList":
				p.toGobanList(boards)
			
			if p.key == "W":
				g.toPlay = "white"
				g = g.copy()
				g.play("white", toCoord(p.value, g.ysize))
				g.toPlay = opponent(g.toPlay)
				boards.append(g)
			
			elif p.key == "B":
				g.toPlay = "black"
				g = g.copy()
				g.play("black", toCoord(p.value, g.ysize))
				g.toPlay = opponent(g.toPlay)
				boards.append(g)
			
			elif p.key == "AW":
				# g = g.copy()
				for location in toCoordList(p.value, g.ysize):
					g.place("white", location)
				# boards.append(g)
			
			elif p.key == "AB":
				#g = g.copy()
				for location in toCoordList(p.value, g.ysize):
					g.place("black", location)
				#boards.append(g)
			
			elif p.key == "PL":
				color = toColor(p.value)
				if color:
					g.toPlay = color
			
			elif p.key == "GameTree":
				p.toGobanList(boards)
				break
			
			else:
				showit = False

			if testPrint and showit:
				print(g.asASCII())
		
		return boards

	def play(self, board: 'Goban' or None = None, interactive=False) -> None:
		"play moves and print the positions, for testing"
		
		global _QuitMeDangit
		class _QuitMeDangit(Exception): pass

		g = board
		#print("BOARD IS ", board)
		if board == None:
			sz = self.find('SZ')
			#print("SZ FOUND: ", sz.value)
			if sz:
				x,y = toSize(sz.value)
				g = Goban(x,y)
			else:
				g = Goban() # guess 19x19

			try: 
				self.play(g, interactive)
			except _QuitMeDangit as e:
				pass 
			
			return

		for p in self.children:
			showit = True
			if p.key == "PropList":
				p.play(g, interactive)
			if p.key == "W":
				board.play("white", toCoord(p.value, g.ysize))
			elif p.key == "B":
				board.play("black", toCoord(p.value, g.ysize))
			elif p.key == "AW":
				for location in toCoordList(p.value, g.ysize):
					board.place("white", location)
			elif p.key == "AB":
				for location in toCoordList(p.value, g.ysize):
					board.place("black", location,)
			elif p.key == "GameTree":
				p.play(g, interactive)
				break
			else:
				showit = False

			if showit:
				print(board.asASCII())
				if interactive:
					self.pprint()
					
					res = input("\npress return to continue ")
					if len(res) and res[0].strip().upper() == "Q":
						raise _QuitMeDangit

	def printPlaysPlaces(self) -> None:
		"just print plays and stone placements to stdout, for testing"
		for p in self.children:
			if p.key == "W":
				print(f"Play White {toCoord(p.value)}")
			elif p.key == "B":
				print(f"Play Black {toCoord(p.value)}")
			elif p.key == "AW":
				for location in self.toCoordList(p.value, 19):
					print(f"Add   White {location}")
			elif p.key == "AB":
				for location in toCoordList(p.value, 19):
					print(f"Add   Black {location}")
			elif p.key == "PropList":
				p.printPlaysPlaces()
			elif p.key == "GameTree":
				# first variation only
				p.printPlaysPlaces()
				break

class SgfParser:
	@staticmethod
	def fromFile(filename: str) -> 'SgfParser':
		with open(filename) as f:
			contents = f.read()

		return SgfParser(contents)
	
	@staticmethod
	def fromString(contents: str) -> 'SgfParser':
		return SgfParser(contents)

	def __init__(self, contents:str) -> None:
		self.root = self.parse(contents)

	def nextReal(self, character:str, contents: str, index: int) -> int:
		"find the next unescaped occurence of the character provided and return its index"
		i = index 
		while True:
			i = contents.find(character, i)
			if i < 0:
				raise ValueError(f"Unmatched brace {character}")

			if i > 0 and contents[i-1] == "\\":
				i += 1
				if i >= len(contents):
					raise ValueError(f"unmatched brace {character}")
				
				i = contents.find(character, i)
			else:
				break
		return i


	def gulpProp(self, contents: str, index: int, lastKey="") -> tuple[int, 'SgfNode']:
		"consume a property and return (new cursor, node)"
		i = self.nextReal("[", contents, index)
		if i < 0:
			raise ValueError("Bad property, sry")

		key = contents[index:i].strip()
		if key == "":
			key = lastKey
		i2 = self.nextReal("]", contents, i)

		if i2 < 0:
			raise ValueError("unmatched brace")
		
		value = contents[i+1:i2]
		return i2+1, SgfNode(key, value)

	def gulpProps(self, contents:str, index: int) -> tuple[int, list['SgfNode']]:
		"consume all following properties and return (new cursor, list of nodes)"
		props = []
		i = index
		lastKey = ""
		while True:
			c = contents[i:].lstrip()[0]
			if c == ';' or c == ')' or c == '(' :
				return i, props
			else:
				i2, node = self.gulpProp(contents, i, lastKey)
				i = i2
				lastKey = node.key
				props.append(node)

		return i, props

	def parse(self, contents: str) -> SgfNode:
		"parse contents string and return SgfNode, which probably contains more SgfNodes"
		i = 0
		chaff = ""
		curNode = SgfNode("root", None)
		while i < len(contents):
			c = contents[i]
			if c == "\\":
				# shouldn't happen at this level, but ignore it anyway
				chaff+= contents[i]
				i += 2
				c = contents[i] # FIXME deal with out of range exception

			if c == '(':
				gt = SgfNode("GameTree", None)
				curNode.addChild(gt)
				curNode = gt
				i += 1
			elif c == ')':
				curNode = curNode.parent
				i += 1
			elif c == ';':
				node = SgfNode("PropList", None)
				i, node.children = self.gulpProps(contents, i+1)
				curNode.addChild(node)
			else:
				chaff += contents[i]
				i += 1
		
		if len(chaff):
			print("SGF PARSING CHAFF: ", chaff, file=sys.stderr)
		
		return curNode

if __name__ == "__main__":
	#thing = SgfParser.fromFile("test_files/test_normal.sgf")
	#thing.root.pprint()

	#thing = SgfParser.fromFile("test_files/test_escaped.sgf")


	thing = SgfParser.fromFile("test_files/test_rootplaces.sgf")
	thing.root.pprint()
	sys.exit()
	gl = thing.root.toGobanList()

	print ("GOBANS: ", gl)

	for g in gl:
		# print("### POSITION: ")
		print(g.asASCII())

	thing.root.play(interactive=True)

	thing = SgfParser.fromFile("test_files/test_wacky_nesting.sgf")
	thing.root.play(interactive=True)
