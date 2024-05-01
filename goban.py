# special goban for KataQuery
# that is flexible enough for a freeform goban GUI
# The main funcitonality  separates the position
# into static placed stones and a subsequent move list,
# depending on what operations were performed on it.
# This allows for a freeform goban but can also 
# track ko, captures, etc. Also, it's kinder to katago's caching

import numpy as np
from goutils import pointToCoords, isPass

color2int = {"E": 0, "B": 1, "W": 3, "K": 4, 0: 0, 1: 1, 3: 3, 4: 4} # empty black white ko
int2color = {0: "empty", 1: "black", 3: "white", 4: "empty"} # just make ko "empty" for now

def eprint(*args, **kwargs):
    import sys
    "just like print() but to stderr"
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)

def opposite(col: np.ubyte):
    if col == 1: return 3
    elif col == 3: return 1
    else: return col # should be value error


class Bifurcator:
    "An observer that separates moves into established stones and played stones. This is to help Katago keep track of ko"
    def __init__(self, board: 'Goban'):
        self._placements = ([], []) # white, black
        self._plays = [] 
        self._board = board

    def play(self, color: str, location: tuple[int,int], as_new: bool = False) -> list[tuple[int,int]]:
        """
        play, return list of captured stone coords. If "as_new" is True,
        collect first
        """
        if isPass(location): return []
        if as_new:
            self.collect()
        self._plays.append([color, location])
        
        return self._board._play(color, location)
    
    def copy(self, newBoard: 'Goban') -> 'Bifurcator':
        b = Bifurcator(newBoard)
        b._placements = (list(self._placements[0]), list(self._placements[1]))
        b._plays = list(self._plays)
        return b

    def place(self, color: str, location: tuple[int,int]):
        if isPass(location): return        
        res = self._board._place(color, location)
        self.collect()
        return res

    def collect(self) -> None:
        "collect all the stones into a placement instead of move order"
        self._placements = (self._board.white_stones(), self._board.black_stones())
        self._plays = []

    def clear(self) -> None:
        self._placements = ([], []) # white, black
        self._plays = []

    def stones_n_moves(self) -> tuple[list, list]:
        stones = []
        whites = self._placements[0]
        blacks = self._placements[1]
        for w in whites:
            stones.append(["W", w])
        for b in blacks:
            stones.append(["B", b])

        return stones, self._plays

    def stones_n_moves_coords(self) -> tuple[list, list]:
        #print("placements ", self._placements)
        #print("plays", self._plays)
        whites = [['W', pointToCoords(p)] for p in self._placements[0]]
        blacks = [['B', pointToCoords(p)] for p in self._placements[1]]

        whites.extend(blacks)
        stones = whites        
        
        plays = [[p[0][0].upper(), pointToCoords(p[1])] for p in self._plays]

        #print(stones, plays)
        return stones, plays

class Goban:
    def __init__(self, xsize:int = 19, ysize = None, makingCopy:bool =False) -> None:
        self.xsize = xsize
        self.ysize = ysize
        self._komi = 6.5 # useful only for sgf export
        self._toPlay = "black" # useful only for sgf export
        if ysize == None:
            self.ysize = xsize

        if not makingCopy:
            self.board = np.zeros((self.xsize,self.ysize), dtype=np.ubyte)
            self.visited_template = np.zeros((self.xsize,self.ysize), dtype=np.ubyte)

        self.bifurcator = Bifurcator(self)

    @property
    def komi(self): return self._komi
    
    @komi.setter
    def komi(self, newK): self._komi = newK

    @property
    def toPlay(self): return self._toPlay

    @toPlay.setter
    def toPlay(self, value): self._toPlay = value

    def copy(self) -> 'Goban':
        "return a duplicate of myself"
        c = Goban(self.xsize, self.ysize, makingCopy=True)
        c.board = np.copy(self.board)
        c.visited_template = self.visited_template
        c.bifurcator = self.bifurcator.copy(c)

        return c

    def asASCII(self) -> str:
        res = "\n   "
        for x in range(self.board.shape[0]):
            if x < 10: res += " "
            res += str(x)

        rownum = self.board.shape[1]-1
        for y in np.flip(self.board.T, axis=0):
            res += "\n"
            if rownum < 10: res += " "
            res += f"{rownum} "

            for x in y:
                if x == 3:
                    res += " O"
                elif x == 1:
                    res += " X"
                else:
                    res += " ."
            rownum -= 1

        res += "\n"
        return res

    def asSGF(self) -> str:
        # sgf format inverts the y axis 

        sgf = f"(;GM[1]FF[4]CA[UTF-8]KM[{self.komi}]"
        sgf += f"PL[{self.toPlay[0].upper()}]"

        letters = 'abcdefghijklmnopqrstuvwxyz'
        initial, moves = self.bifurcator.stones_n_moves()

        if len(initial):
            sgf += ";"
        for i in initial:
            pos = i[1]
            color = i[0]
            coord = letters[pos[0]] + letters[self.ysize-pos[1]-1]
            if color[0].upper() == "W":
                sgf += "AW[{coord}]"
            else:
                sgf += "AB[{coord}]"


        for m in moves:
            pos = m[1]
            color = m[0]
            coord = letters[pos[0]] + letters[self.ysize-pos[1]-1]
            if color[0].upper() == "B":
                sgf += f";W[{coord}]"
            else:
                sgf += f";B[{coord}]"

        # not sure if this is the right way,
        # perhaps user wants to specify toPlay even if same color played last? 
        # But THAT ends up with confusing SGF, so..
        if len(moves) == 0:
            sgf += f";PL[{self.toPlay[0].upper()}]"
        sgf += ")"
        return sgf

    def print(self) -> None:
        res = self.asASCII()
        eprint(res, end='')


    def clear(self) -> None:
        "clear the board"
        self.bifurcator.clear()
        self.board.fill(0)

    def play(self, color: str, gopoint: tuple[int,int]):
        "play a move"
        #print("Playing ", gopoint)
        if isPass(gopoint): return []

        removed =  self.bifurcator.play(color, gopoint)

        self.board[self.board == 4] = 0 # remove ko
        
        if len(removed) == 1:
            self.board[removed[0]] = 4 # add ko

        #print("PLAYS ", self.bifurcator._plays)
        return removed

    def place (self, color:str, gopoint: tuple[int,int]) -> None:
        "place a stone"
        if isPass(gopoint): return
        res = self.bifurcator.place(color, gopoint)
        
        # a "place" resets ko
        self.board[self.board == 4] = 0
        return res

    def place_many(self, blackpoints: list[tuple[int,int]] = [], whitepoints: list[tuple[int,int]] =[]) -> None:
        "place many stones, ignoring legality and captures"
        for p in blackpoints:
            self.place("black", p)
        for p in whitepoints:
            self.place("white", p)

    def play_many(self, toPlay: str, moves: list[tuple[int,int]]) -> tuple[list, list]:
        "play list of moves, alternating players between"
        c = toPlay
        black_caps = []
        white_caps = []

        for p in moves:
            caps = self.play(c, p)                
            if c == "white": 
                c = "black"
                black_caps = black_caps + caps
            else: 
                c = "white"
                white_caps = white_caps + caps

        return black_caps, white_caps

    def _play(self, color:str, gopoint: tuple[int,int]) -> list[tuple[int,int]]:
        "play a stone, perform captures, and return list of captured indicies"
        c = color2int[color[0].upper()]
        if c & 1 == 0: return []

        self._place(color, gopoint)
        removed = []
        for a in self.adjacent(gopoint):
            #eprint("a is ", a)
            if self.board[a] == opposite(c) and not self.haslibs(a):
                removed.extend(self._remove_group(a))

        return removed

    def _place(self, color:str, gopoint: tuple[int,int]) -> None:
        "place a stone (or ko) on the board, ignoring legality and captures"
        c = color2int[color[0].upper()]
        
        self.board[gopoint] = c

    def _place_many(self, blackpoints: list[tuple[int,int]] = [], whitepoints: list[tuple[int,int]] =[]) -> None:
        "place many but without keeping track"
        for p in blackpoints:
            self._place("black", p)
        for p in whitepoints:
            self._place("white", p)

    def cap_all_stones(self, toPlayColor: str) -> tuple[list[tuple[int,int]], list[tuple[int,int]]]:
        """
        cap all stones, assuming toPlayColor is first to play.
        This is not good for a standard move capture as it gathers all stones into _placements.
        Use only if the board was modified with place() etc.
        """
        capped_black = []
        capped_white = []

        black,white = self.groups()
        removed = False
        def capblack() -> None:
            for b in black:
                if not self.haslibs(b[0]):
                    #print("NO LIBS: ", b)
                    capped_black.extend(b)
                    for c in b: self._remove(c)
                    removed = True
        def capwhite() -> None:
            for w in white:
                if not self.haslibs(w[0]):
                    #print("NO LIBS W: ", w)
                    capped_white.extend(w)
                    for c in w: self._remove(c)
                    removed = True

        if toPlayColor == "white":
            capblack() ; capwhite()
        else:
            capwhite() ; capblack()

        if removed:
            self.bifurcator.collect()

        return capped_black, capped_white

    def legal(self, color:str, gopoint: tuple[int,int]) -> bool:
        "is this play legal for this color?"
        if self.board[gopoint] & 1 != 0:
            return False

        if self.board[gopoint] == 4:
            return False

        legal = False

        caps = self._play(color, gopoint)

        #eprint(f"play: {color} {gopoint}, caps: {caps}")
        if self.haslibs(gopoint):
            #eprint(f"play: {color} {gopoint} haslibs: True")
            legal = True

        if color2int[color[0].upper()] == 1:
            self._place_many(whitepoints=caps)
        else:
            self._place_many(blackpoints=caps)

        self._remove(gopoint)

        return legal
    
    def nearby_stones(self, hops: int) -> set[tuple[int,int]]:
        hopset = set(self.black_stones() + self.white_stones())
        v = set(hopset) #visited

        return self._nearby_stones_rec(v, hopset, hops)

    def _nearby_stones_rec(self, v: set[tuple[int,int]], hopset: set[tuple[int,int]], hop: int):
        if hop == 0: return hopset
        nexthop = set()
        for b in hopset:
            for neighbor in self.adjacent(b):
                if neighbor not in v:
                    nexthop.add(neighbor)
                    v.add(neighbor)
        
        return set.union(hopset, self._nearby_stones_rec(v, nexthop, hop-1))

    def nearby_these(self, thesePoints = None) -> set[tuple[int,int]]:
        "get the intersections nearby the stones"
        if thesePoints == None:
            thesePoints = self.black_stones() + self.white_stones()
        
        points = set(thesePoints)
        for p in thesePoints:
            for neighbor in self.adjacent(p):
                #if self.board[neighbor] & 1 == 0:
                points.add(neighbor)
        return points
    
    def remove(self, gopoint: tuple[int,int]) -> None:
        self._remove(gopoint)
        self.bifurcator.collect()

    def relocate(self, srcPoint: tuple[int,int], destPoint: tuple[int,int]) -> None:
        "Try to relocate a move/stone from srcPoint to destPoint"
        # ATM we just collapse the stones
        # but better would be to retain move order if possible
        # self.bifurcator.collect()
        col = int2color[self.board[srcPoint]]
        self._remove(srcPoint)
        self._place(col, destPoint)
        self.bifurcator.collect()

    def goban_when_play(self, color: str, gopoint: tuple[int, int]) -> "Goban":
        "return a copy of this goban with the specified play played"
        g = self.copy()
        g.play(color, gopoint)
        return g

    def _remove(self, gopoint: tuple[int,int]) -> None:
        "remove a stone from this location"
        self.board[gopoint] = 0

    def _remove_group(self, gopoint: tuple[int,int]) -> list[tuple[int,int]]:
        "remove all connected stones of this gopoint and return a list of them"
        if self.board[gopoint] & 1 == 0:
            return []

        con = self.connected(gopoint)
        removed = []
        for c in con:
            self._remove(c)
            removed.append(c)
        return removed

    def get(self, gopoint: tuple[int,int]) -> str: # "black" "white", "empty"
        "get the color of the stone at this point"
        if self.board[gopoint] & 1 == 0:
            return "empty"
        if self.board[gopoint] == 1:
            return "black"
        if self.board[gopoint] == 3:
            return "white"

    def getI(self, gopoint:tuple[int,int]) -> np.ubyte:
        "return the color of the intersection as an int8"
        return self.board[gopoint]

    def _recast(self, thing) -> list[tuple[int,int]]:
        return [(int(p[0]), int(p[1])) for p in thing]

    def empties(self) -> list[tuple[int,int]]:
        "return indices of all empty points on board"
        s = zip(*np.where(self.board & 1 == 0))
        return self._recast(s)

    def stones(self) -> list[tuple[int,int]]:
        "return indices of all stones on board"
        s = zip(*np.where(self.board & 1 == 1))
        return self._recast(s)

    def stones_byCol(self, color:str) -> list[tuple[int,int]]:
        c = color2int[color[0].upper()]
        #return list(zip(*np.where(self.board == c)))
        # sadly we must recast it so JSON works
        s = zip(*np.where(self.board == c))
        return self._recast(s)

    def white_stones(self) -> list[tuple[int,int]]:
        "return indices of all white stones on board"
        return self.stones_byCol("white")

    def black_stones(self) -> list[tuple[int,int]]:
        "return indices of all black stones on board"
        return self.stones_byCol("black")

    def groups(self)-> tuple[list[tuple[int, int]], list[tuple[int,int]]]:
        "return black_groups, white_groups on the board"
        v = {} #self.visited_template.copy()

        result = {"black": [], "white": []}

        for col in ["black", "white"]:
            for s in self.stones_byCol(col):
                if s not in v:
                    v[s] = True
                    group = self.connected(s)
                    for stone in group:
                        v[stone] = True
                    result[col].append(group)

        return result["black"], result["white"]

    def stones_n_moves(self) -> tuple[list, list]:
        "return stones, movelist suitable for sending to katago for position"
        return self.bifurcator.stones_n_moves()

    def stones_n_moves_coords(self) -> tuple[list, list]:
        "return stones, movelist as go coordinates format, e.g. D4"
        return self.bifurcator.stones_n_moves_coords()

    def ko_location(self): # returns tuple or None
        k = list(zip(*np.where(self.board == 4)))
        if len(k):
            return k[0]
        return None

    def adjacent(self, gopoint: tuple[int,int]) -> list[tuple[int,int]]:
        "return indices of spaces adjacent to this point"
        res = []
        for d in [(1,0), (-1, 0), (0, 1), (0, -1)]:
            res.append((gopoint[0] + d[0], gopoint[1] + d[1]))

        return [i for i in res if i[0] >= 0 and i[0] < self.xsize and i[1] >= 0 and i[1] < self.ysize]

    def connected(self, gopoint: tuple[int,int]) -> list[tuple[int,int]]:
        visited = {}
        grouped = {}
        col = self.board[gopoint]

        self._connectedRec(col, [gopoint], visited, grouped)
        #eprint(f"grouped: {grouped.keys()}")
        return list(grouped.keys())

    def _connectedRec(self, col: np.ubyte, gopoints: list[tuple[int,int]], visited: dict, grouped: dict) -> None:
        for p in gopoints:
            if p in visited: continue
            visited[p] = True
            if self.board[p] == col:
                grouped[p] = True
                self._connectedRec(col, self.adjacent(p), visited, grouped)

    def libs(self, gopoint: tuple[int,int]) -> list[tuple[int,int]]:
        "return list of empty gopoints that count as this group's liberties"
        group = self.connected(gopoint)
        empties = {}
        for i in group:
            surrounding = [p for p in self.adjacent(i) if self.board[p] & 1 == 0]
            for s in surrounding:
                empties[s] = True

        return list(empties.keys())

    def haslibs(self, gopoint: tuple[int,int]) -> bool:
        "a quick check for capture"
        group = self.connected(gopoint)
        for i in group:
            for a in self.adjacent(i):
                if self.board[a] & 1 == 0:
                    return True
        return False

    def _randomLegal(self, color = None) -> tuple[str, tuple[int,int]]:
        import random

        col = color
        if col == None:
            col = random.choice(["white", "black"])

        move = (0,0)
        while True:
            try:
                move = random.choice(self.empties())
            except IndexError as e:
                self.print()
                raise e


            if self.legal(col, move):
                break

        return col, move

    # some terrible bots to test the board
    def _randomPlay(self, color = None) -> tuple[str, tuple[int,int], list]:
        import random

        col, move = self._randomLegal(color)
        caps = self.play(col, move)

        return col, move, caps

    def _captureGo(self, col) -> tuple[str, tuple[int,int], list]:
        import random
        #col = random.choice(["white", "black"])

        black_groups, white_groups = self.groups()

        othergroup = white_groups
        if col == "white": othergroup = black_groups 

        if len(othergroup) == 0:
            return self._randomPlay(color=col)

        libs = []
        
        for g in othergroup:
            libs.extend(self.libs(g[0]))


        if len(libs):
            for x in range(10):
                move = random.choice(libs)

                if self.legal(col, move):
                    caps = self.play(col, move)
                
                    return col, move, caps
        
        return self._randomPlay(col)


    def _leastLibGo(self, col) -> tuple[str, tuple[int,int], list]:
        import random
        #col = random.choice(["white", "black"])

        black_groups, white_groups = self.groups()

        black_groups.extend(white_groups)
        allgroups = black_groups

        if len(allgroups) == 0:
            return self._randomPlay(color=col)

        libs = []
        minlibs = 8888
        mingroup = None

        for g in allgroups:
            l = self.libs(g[0])
            if len(l) < minlibs:
                minlibs = len(l)
                mingroup = l

        if mingroup != None:
            for x in range(10):
                move = random.choice(mingroup)

                if self.legal(col, move):
                    caps = self.play(col, move)
                
                    return col, move, caps
        
        return self._randomPlay(col)

def test(length: int = 180) -> 'Goban':
    b = Goban(19)
    for m in range(length):
        #eprint("MOVE NUMBER:", m)
        col, move, caps = b._leastLibGo(["black", "white"][m % 2])
        if len(caps):
            pass #print(f"# captured: {caps}")
            #b.print()
            #return b
        
        #b.print()

    return b

if __name__ == "__main__":
    import time

    class Perf:
        def __init__(self):
            self._start = 0
            self._end = 0
            self.title = "no name"
        
        def start(self, title:str) -> None:
            self.title = title
            self._start = time.perf_counter()

        def end(self) -> None:
            self._end = time.perf_counter()

        def show(self) -> None:
            self.end()
            print(f"{self.title} execution time: {self._end-self._start}")

    p = Perf()

    movecount = 180
    p.start('moves')
    b = test(movecount)
    p.show()

    #b = Goban(19)
    b.print()

    #print(b.stones_n_moves_coords())

    if True:
        p.start('randomlegal')
        for x in range(movecount):
            b._randomLegal()
        p.show()

        moves = list(map(b._randomLegal, [None]*movecount))

        p.start('goban_when_play')
        for m in moves:
            blah = b.goban_when_play(m[0], m[1])
        p.show()

        p.start('groups')
        for x in range(movecount):
            blacks, whites = b.groups()
        p.show()


        p.start('get')
        for x in range(movecount):
            blah = b.get((12,12))
        p.show()


        p.start("adjacent")
        for x in range(movecount):
            blah = b.adjacent((12,12))
        p.show()

        p.start("connected")
        for x in range(movecount):
            blah = b.connected((2,0))
        p.show()

        p.start("copy")
        for x in range(movecount):
            blah = b.copy()
        p.show()

        p.start("stones_n_moves")
        for x in range(movecount):
            blah = b.stones_n_moves()
        p.show()

        p.start("stones_n_moves_coords")
        for x in range(movecount):
            blah = b.stones_n_moves_coords()
        p.show()
    
    print(b.asSGF())
