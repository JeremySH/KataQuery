# special goban for KataQuery
# that is flexible enough for a freeform goban GUI
# The main funcitonality  separates the position
# into static placed stones and a subsequent move list,
# depending on what operations were performed on it.
# This allows for a freeform goban but can also 
# track ko, captures, etc. Also, it's kinder to katago's caching

import numpy as np
from goutils import to_gopoint, is_pass, gopoint_to_str
import typing as T

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


def same_color(col: str):
    "normalize e.g 'black' 'Black' 'B' and 'bLaCk' to just 'black' "
    if col[0].upper() == "W":
        return "white"
    elif col[0].upper() == "B":
        return "black"
    else:
        return "empty"

class Bifurcator:
    "An observer that separates moves into established stones and played stones. This is to help Katago keep track of ko"
    def __init__(self, board: 'Goban'):
        self._placements = ([], []) # black, white
        self._plays = [] 
        self._board = board

    def play(self, color: str, location: T.Tuple[int, int], as_new: bool = False) -> T.List[T.Tuple[int,int]]:
        """
        play, return list of captured stone coords. If "as_new" is True,
        collect first
        """
        if is_pass(location): return []
        if as_new:
            self.collect()
        self._plays.append([color, location])
        
        return self._board._play(color, location)
    
    def copy(self, newBoard: 'Goban') -> 'Bifurcator':
        b = Bifurcator(newBoard)
        b._placements = (list(self._placements[0]), list(self._placements[1]))
        b._plays = list(self._plays)
        return b

    def place_equals_play(self, color: str, location: T.Tuple[int,int]) -> bool:
        "is this place of a stone equivalent to playing a stone?"
        if is_pass(location): return True
        g1 = self._board.copy()
        g2 = self._board.copy()
        g1.play(color, location)
        g2.place(color, location)

        return np.array_equal(g1.board, g2.board)

    def place_modifies_plays(self, color: str, location: T.Tuple[int,int]) -> bool:
        "does this place change the meaning of the moves?"
        # basically if the only difference is that there's a stone here
        # then the moves aren't affected

        g = self._board.copy()
        blacks, whites = self._placements
        blacks, whites = list(blacks), list(whites)
        if color == "black":
            blacks.append(location)
        elif color == "white":
            whites.append(location)

        g.clear()
        g._place_many(blacks, whites)

        for p in self._plays:
            g._play(p[0], p[1])

        result = np.not_equal(g.board, self._board.board)
        return result.sum() != 1 or result[location] == False

    def change_play(self, srcLoc, destLoc):
        index = None
        for i, m in enumerate(self._plays):
            if m[1] == srcLoc:
                index = i
                break

        if index != None:
            col = self._plays[index][0]
            self._plays[index] = (col, destLoc)
            self._board.board[srcLoc] = 0
            self._board._place(col, destLoc)

    def find_stone(self, location: T.Tuple[int,int]) -> T.Tuple[str, T.Tuple[int,int]]:
        "find a stone and return kind, index. Kind is 'place_black' 'place_white' 'play' or None"
        plays = self._plays
        blacks, whites = self._placements

        for i, p in enumerate(reversed(plays)):
            if p[1] == location:
                return "play", len(plays) - i - 1

        for i, b in enumerate(blacks):
            if b == location:
                return "place_black", i

        for i, w in enumerate(whites):
            if w == location:
                return "place_white", i

        return None, None
    
    def try_remove(self, location: T.Tuple[int,int]) -> bool:
        "try to remove and keep move order, return true if success "
        kind, index = self.find_stone(location)
        
        if kind == None: return True

        blacks, whites = self._placements
        blacks, whites = list(blacks), list(whites)

        moves = list(self._plays)

        if kind == 'play':
            del moves[index]
        elif kind == 'place_black':
            del blacks[index]
        elif kind == 'place_white':
            del whites[index]
        else:
            return False

        g = self._board.copy()
        g.clear()
        g._place_many(blacks, whites)
        for m in moves:
            g.play(m[0], m[1])

        result = np.not_equal(g.board, self._board.board)            
        if result.sum() == 1 and result[location] == True :
            self._board.board[location] = 0
            self._plays = moves
            self._placements = (blacks, whites)
            return True

        return False

    def try_relocate(self, srcLoc: T.Tuple[int,int], destLoc: T.Tuple[int,int])-> bool:
        "relocate and try to keep move order, return if success"
        if srcLoc == destLoc: return True
        #FIXME: this is fugly
        moveIndex = None
        for i, m in enumerate(self._plays):
            if m[1] == srcLoc:
                moveIndex = i
                break
        
        if moveIndex != None:
            # it's a move, replay & check
            g = self._board.copy()
            col = g.bifurcator._plays[moveIndex][0]
            g.bifurcator._plays[moveIndex] = (col, destLoc)
            plays = list(g.bifurcator._plays)
            b, w = g.bifurcator._placements
            g.clear()
            g._place_many(b,w)
            for p in plays:
                g._play(p[0], p[1])

            result = np.not_equal(g.board, self._board.board)

            if result.sum() == 2 and result[srcLoc] == True and result[destLoc] == True:
                self.change_play(srcLoc, destLoc)
                return True
            else:
                return False
        else:
            # yeah this is nasty
            blacks, whites = self._placements
            srcIndex = None
            srcColor = None
            for i,b in enumerate(blacks):
                if srcLoc == b:
                    srcIndex = i
                    srcColor = "black"
                    break

            for i,w in enumerate(whites):
                if srcLoc == w:
                    srcIndex = i
                    srcColor = "white"
                    break

            if srcIndex == None: 
                #print("NOT FOUND: ", srcLoc)
                #print(self._placements)
                return False

            group = 0
            if srcColor == "white":
                group = 1

            g = self._board.copy()
            
            # move it
            g.bifurcator._placements[group][srcIndex] = destLoc
            blacks, whites = g.bifurcator._placements
            plays = g.bifurcator._plays

            g.clear()
            g._place_many(blacks, whites)
            for p in plays:
                g._play(p[0], p[1])

            result = np.not_equal(g.board, self._board.board)
            
            # is it legit?
            if result.sum() == 2 and result[srcLoc] == True and result[destLoc] == True:
                #print("REPLACING ", srcLoc, destLoc)
                self._placements = (blacks, whites)
                self._board.board[srcLoc] = 0
                self._board._place(srcColor, destLoc)
                return True

    def place(self, color: str, location: T.Tuple[int,int]):
        if is_pass(location): return
        
        modified = self.place_modifies_plays(color, location)
        res = self._board._place(color, location)
        
        if modified:
            self.collect()
        else:
            if color == "black":
                self._placements[0].append(location)
            
            if color == "white":
                self._placements[1].append(location)

        return res

    def collect(self) -> None:
        "collect all the stones into a placement instead of move order"
        self._placements = (self._board.black_stones(), self._board.white_stones())
        self._plays = []

    def clear(self) -> None:
        self._placements = ([], []) # black, white
        self._plays = []

    def stones_n_moves(self) -> T.Tuple[list, list]:
        "return the current position as a list of placd stones and a list of plays after these placements"
        stones = []
        blacks = self._placements[0]
        whites = self._placements[1]
        for w in whites:
            stones.append(["W", w])
        for b in blacks:
            stones.append(["B", b])

        return stones, self._plays

    def stones_n_moves_coords(self) -> T.Tuple[list, list]:
        "just like stones_n_moves except the coordinates are GTP style (e.g. 'D4'). Useful for sending to KataGo"
        #print("placements ", self._placements)
        #print("plays", self._plays)
        blacks = [['B', gopoint_to_str(p)] for p in self._placements[0]]
        whites = [['W', gopoint_to_str(p)] for p in self._placements[1]]

        whites.extend(blacks)
        stones = whites        
        
        plays = [[p[0][0].upper(), gopoint_to_str(p[1])] for p in self._plays]

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

        self.bifurcator = Bifurcator(self)

    @property
    def komi(self): 
        "the komi used in this position. Only used for SGF export."
        return self._komi
    
    @komi.setter
    def komi(self, newK): self._komi = newK

    @property
    def toPlay(self): 
        "Meta-information of the current player to play. Only really used for SGF export."
        return self._toPlay

    @toPlay.setter
    def toPlay(self, value): self._toPlay = same_color(value)

    @property
    def player(self): # to get rid of camelCase eventually
        "who's move is it? 'black' or 'white'?"
        return self.toPlay()
    
    @player.setter
    def player(who: str):
        self.toPlay = who

    def copy(self) -> 'Goban':
        "return a duplicate of myself"
        c = Goban(self.xsize, self.ysize, makingCopy=True)
        c.board = np.copy(self.board)
        c.bifurcator = self.bifurcator.copy(c)
        c.komi = self.komi
        c.toPlay = self.toPlay
        return c

    def as_ascii(self) -> str:
        "return an ASCII text rendering of the board"
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

    def as_sgf(self) -> str:
        "Convert to SGF text suitable for importing into an SGF editor"
        # sgf format inverts the y axis 
        letters = 'abcdefghijklmnopqrstuvwxyz'
        initial, moves = self.bifurcator.stones_n_moves()

        sgf = f"(;GM[1]FF[4]CA[UTF-8]KM[{self.komi}]"
        x,y = letters[self.xsize-1], letters[self.ysize-1]
        sgf += f"SZ[{self.xsize}:{self.ysize}]"
        sgf += f"PL[{self.toPlay[0].upper()}]"

        for i in initial:
            pos = i[1]
            color = i[0]
            coord = letters[pos[0]] + letters[self.ysize-pos[1]-1]
            if color[0].upper() == "W":
                sgf += f"AW[{coord}]"
            else:
                sgf += f"AB[{coord}]"


        for m in moves:
            pos = m[1]
            color = m[0]
            coord = letters[pos[0]] + letters[self.ysize-pos[1]-1]
            if color[0].upper() == "W":
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
        "print the ASCII board to stderr"
        res = self.as_ascii()
        eprint(res, end='')


    def clear(self) -> None:
        "clear the board"
        self.bifurcator.clear()
        self.board.fill(0)

    def play(self, color: str, gopoint: T.Tuple[int,int]):
        "play a move"
        point = to_gopoint(gopoint)
        #print("Playing ", gopoint)
        if is_pass(point): return []

        removed =  self.bifurcator.play(color, point)

        self.board[self.board == 4] = 0 # remove ko
        
        if len(removed) == 1:
            self.board[removed[0]] = 4 # add ko

        #print("PLAYS ", self.bifurcator._plays)
        return removed

    def place (self, color:str, gopoint: T.Tuple[int,int]) -> None:
        "place a stone of color at gopoint"
        point = to_gopoint(gopoint)
        if is_pass(point): return
        res = self.bifurcator.place(color, point)
        
        # a "place" resets ko
        self.board[self.board == 4] = 0
        return res

    def place_many(self, blackpoints: T.List[T.Tuple[int,int]] = [], whitepoints: T.List[T.Tuple[int,int]] =[]) -> None:
        "place many stones, ignoring legality and captures"
        for p in blackpoints:
            self.place("black", to_gopoint(p))
        for p in whitepoints:
            self.place("white", to_gopoint(p))

    def play_many(self, toPlay: str, moves: T.List[T.Tuple[int,int]]) -> T.Tuple[list, list]:
        "play list of moves, alternating players between"
        c = toPlay
        black_caps = []
        white_caps = []

        for p in moves:
            caps = self.play(c, to_gopoint(p))
            if c == "white": 
                c = "black"
                black_caps = black_caps + caps
            else: 
                c = "white"
                white_caps = white_caps + caps

        return black_caps, white_caps

    def _play(self, color:str, gopoint: T.Tuple[int,int]) -> T.List[T.Tuple[int,int]]:
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

    def _place(self, color:str, gopoint: T.Tuple[int,int]) -> None:
        "place a stone (or ko) on the board, ignoring legality and captures"
        c = color2int[color[0].upper()]
        
        self.board[gopoint] = c

    def _place_many(self, blackpoints: T.List[T.Tuple[int,int]] = [], whitepoints: T.List[T.Tuple[int,int]] =[]) -> None:
        "place many but without keeping track"
        for p in blackpoints:
            self._place("black", p)
        for p in whitepoints:
            self._place("white", p)

    def cap_all_stones(self, toPlayColor: str) -> T.Tuple[T.List[T.Tuple[int,int]], T.List[T.Tuple[int,int]]]:
        """
        Capture all stones, assuming toPlayColor is first to play.
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

    def legal(self, color:str, gopoint: T.Tuple[int,int]) -> bool:
        "is this play legal for this color?"
        point = to_gopoint(gopoint)
        if self.board[point] & 1 != 0:
            return False

        if self.board[point] == 4:
            return False

        legal = False

        caps = self._play(color, point)

        #eprint(f"play: {color} {gopoint}, caps: {caps}")
        if self.haslibs(point):
            #eprint(f"play: {color} {gopoint} haslibs: True")
            legal = True

        if color2int[color[0].upper()] == 1:
            self._place_many(whitepoints=caps)
        else:
            self._place_many(blackpoints=caps)

        self._remove(point)

        return legal
    
    def nearby_stones(self, hops: int) -> T.Set[T.Tuple[int,int]]:
        "return the set of intersections nearby the current stones on the board, at distance hops"
        hopset = set(self.black_stones() + self.white_stones())
        v = set(hopset) #visited

        return self._nearby_stones_rec(v, hopset, hops)

    def _nearby_stones_rec(self, v: T.Set[T.Tuple[int,int]], hopset: T.Set[T.Tuple[int,int]], hop: int):
        if hop == 0: return hopset
        nexthop = set()
        for b in hopset:
            for neighbor in self.adjacent(b):
                if neighbor not in v:
                    nexthop.add(neighbor)
                    v.add(neighbor)
        
        return set.union(hopset, self._nearby_stones_rec(v, nexthop, hop-1))

    def nearby_these(self, thesePoints = None) -> T.Set[T.Tuple[int,int]]:
        "get the intersections nearby the stones"
        if thesePoints == None:
            thesePoints = self.black_stones() + self.white_stones()
        
        points = set(to_gopoint(p) for p in thesePoints)
        for p in thesePoints:
            for neighbor in self.adjacent(p):
                #if self.board[neighbor] & 1 == 0:
                points.add(neighbor)
        return points
    
    def remove(self, gopoint: T.Tuple[int,int]) -> None:
        "remove the stone at this go point"
        point = to_gopoint(gopoint)
        if not self.bifurcator.try_remove(point):
            self._remove(point)
            self.bifurcator.collect()

    def undo(self, count: int = 1) -> None:
        "undo count moves"
        stones, moves = self.stones_n_moves()
        self.clear()

        for col, stone in stones:
            self.place(col, stone)

        for col, move in moves[:-count]:
            self.play(col, move)

    def relocate(self, srcPoint: T.Tuple[int,int], destPoint: T.Tuple[int,int]) -> None:
        "Try to relocate a move/stone from srcPoint to destPoint, requires a tuple"

        if self.bifurcator.try_relocate(srcPoint, destPoint) : return

        col = int2color[self.board[srcPoint]]
        self._remove(srcPoint)
        self._place(col, destPoint)
        self.bifurcator.collect()

    def goban_when_play(self, color: str, gopoint: T.Tuple[int,int]) -> "Goban":
        "return a copy of this goban with the specified play played"
        g = self.copy()
        g.play(color, gopoint)
        return g

    def _remove(self, gopoint: T.Tuple[int,int]) -> None:
        "remove a stone from this location"
        self.board[gopoint] = 0

    def _remove_group(self, gopoint: T.Tuple[int,int]) -> T.List[T.Tuple[int,int]]:
        "remove all connected stones of this gopoint and return a list of them"
        if self.board[gopoint] & 1 == 0:
            return []

        con = self.connected(gopoint)
        removed = []
        for c in con:
            self._remove(c)
            removed.append(c)
        return removed

    def get(self, gopoint: T.Tuple[int,int]) -> str: # "black" "white", "empty"
        "get the color of the stone at this point"
        point = to_gopoint(gopoint)
        if self.board[point] & 1 == 0:
            return "empty"
        if self.board[point] == 1:
            return "black"
        if self.board[point] == 3:
            return "white"

    def getI(self, gopoint:T.Tuple[int,int]) -> np.ubyte:
        "return the color of the intersection as an int8"
        return self.board[gopoint]

    def _recast(self, thing) -> T.List[T.Tuple[int,int]]:
        return [(int(p[0]), int(p[1])) for p in thing]

    def empties(self) -> T.List[T.Tuple[int,int]]:
        "return indices of all empty points on board"
        s = zip(*np.where(self.board & 1 == 0))
        return self._recast(s)

    def stones(self) -> T.List[T.Tuple[int,int]]:
        "return gopoints of all stones on board"
        s = zip(*np.where(self.board & 1 == 1))
        return self._recast(s)

    def stones_by_color(self, color:str) -> T.List[T.Tuple[int,int]]:
        "like stones() but only of specified color (e.g. 'white')"
        c = color2int[color[0].upper()]
        #return list(zip(*np.where(self.board == c)))
        # sadly we must recast it so JSON works
        s = zip(*np.where(self.board == c))
        return self._recast(s)

    def white_stones(self) -> T.List[T.Tuple[int,int]]:
        "return list of gopoints of all white stones on board"
        return self.stones_by_color("white")

    def black_stones(self) -> T.List[T.Tuple[int,int]]:
        "return list of gopoints of all black stones on board"
        return self.stones_by_color("black")

    def groups(self)-> T.Tuple[T.List[T.Tuple[int,int]], T.List[T.Tuple[int,int]]]:
        "return black_groups, white_groups on the board"
        v = {} 

        result = {"black": [], "white": []}

        for col in ["black", "white"]:
            for s in self.stones_by_color(col):
                if s not in v:
                    v[s] = True
                    group = self.connected(s)
                    for stone in group:
                        v[stone] = True
                    result[col].append(group)

        return result["black"], result["white"]

    def stones_n_moves(self) -> T.Tuple[list, list]:
        "return stones, movelist suitable for (eventually) sending to katago for analysis"
        return self.bifurcator.stones_n_moves()

    def stones_n_moves_coords(self) -> T.Tuple[list, list]:
        "return stones, movelist as go coordinates format, e.g. D4"
        return self.bifurcator.stones_n_moves_coords()

    def ko_location(self): # returns tuple or None
        "return a tuple of the current ko location or None"
        k = list(zip(*np.where(self.board == 4)))
        if len(k):
            return k[0]
        return None

    def adjacent(self, gopoint: T.Tuple[int,int]) -> T.List[T.Tuple[int,int]]:
        "return list of gopoints adjacent to this point"
        point = to_gopoint(gopoint)
        res = []
        for d in [(1,0), (-1, 0), (0, 1), (0, -1)]:
            res.append((point[0] + d[0], point[1] + d[1]))

        return [i for i in res if i[0] >= 0 and i[0] < self.xsize and i[1] >= 0 and i[1] < self.ysize]

    def connected(self, gopoint: T.Tuple[int,int]) -> T.List[T.Tuple[int,int]]:
        "return the stones connected to this gopoint, given they are the same color"
        point = to_gopoint(gopoint)
        visited = {}
        grouped = {}
        col = self.board[point]

        self._connectedRec(col, [point], visited, grouped)
        #eprint(f"grouped: {grouped.keys()}")
        return list(grouped.keys())

    def _connectedRec(self, col: np.ubyte, gopoints: T.List[T.Tuple[int,int]], visited: dict, grouped: dict) -> None:
        "recursive subroutine for connected()"
        for p in gopoints:
            if p in visited: continue
            visited[p] = True
            if self.board[p] == col:
                grouped[p] = True
                self._connectedRec(col, self.adjacent(p), visited, grouped)

    def libs(self, gopoint: T.Tuple[int,int]) -> T.List[T.Tuple[int,int]]:
        "return list of empty gopoints that count as this group's liberties"
        point = to_gopoint(gopoint)
        group = self.connected(point)
        empties = {}
        for i in group:
            surrounding = [p for p in self.adjacent(i) if self.board[p] & 1 == 0]
            for s in surrounding:
                empties[s] = True

        return list(empties.keys())

    def haslibs(self, gopoint: T.Tuple[int,int]) -> bool:
        "a quick check for capture"
        point = to_gopoint(gopoint)
        group = self.connected(point)
        for i in group:
            for a in self.adjacent(i):
                if self.board[a] & 1 == 0:
                    return True
        return False

    def diff(self, other_goban: 'Goban') -> T.List[T.Tuple[int,int]]:
        "return a list of intersections that are different between these boards. Boards of different sizes is undefined."
        s = zip(*np.where(self.board != other_goban.board))
        return list(s)

    def collapse(self) -> None:
        "collapse all plays into placements"
        self.bifurcator.collect()

    def _random_legal(self, color = None) -> T.Tuple[str, T.Tuple[int,int]]:
        "generate a random legal move and return (color, move tuple)"
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
    def _random_play(self, color = None) -> T.Tuple[str, T.Tuple[int,int], list]:
        "play a random move and return the move as (color, intersection, resulting_captures)"
        import random

        col, move = self._random_legal(color)
        caps = self.play(col, move)

        return col, move, caps

    def _capture_go(self, col) -> T.Tuple[str, T.Tuple[int,int], list]:
        "randomly pick an opponent's liberty to fill"
        import random
        #col = random.choice(["white", "black"])

        black_groups, white_groups = self.groups()

        othergroup = white_groups
        if col == "white": othergroup = black_groups 

        if len(othergroup) == 0:
            return self._random_play(color=col)

        libs = []
        
        for g in othergroup:
            libs.extend(self.libs(g[0]))


        if len(libs):
            for x in range(10):
                move = random.choice(libs)

                if self.legal(col, move):
                    caps = self.play(col, move)
                
                    return col, move, caps
        
        return self._random_play(col)


    def _least_lib_go(self, col) -> T.Tuple[str, T.Tuple[int,int], list]:
        "pick a group with least liberties and play at one of them"
        import random
        #col = random.choice(["white", "black"])

        black_groups, white_groups = self.groups()

        black_groups.extend(white_groups)
        allgroups = black_groups

        if len(allgroups) == 0:
            return self._random_play(color=col)

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
        
        return self._random_play(col)

def test(length: int = 180) -> 'Goban':
    b = Goban(19)
    for m in range(length):
        #eprint("MOVE NUMBER:", m)
        col, move, caps = b._least_lib_go(["black", "white"][m % 2])
        if len(caps):
            pass #print(f"# captured: {caps}")
            #b.print()
            #return b
        
        #b.print()

    return b

if __name__ == "__main__":
    import time, sys

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

    b2 = test(movecount)
    
    b2 = b.copy()
    b2._random_play()

    print("DIFF: ")
    print(b2.diff(b))

    #b = Goban(19)
    b.print()

    #print(b.stones_n_moves_coords())

    if True:
        p.start('randomlegal')
        for x in range(movecount):
            b._random_legal()
        p.show()

        moves = list(map(b._random_legal, [None]*movecount))

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
    
    print(b.as_sgf())
