# create the lookup tables for go coordinates
_alphabet = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
_letters = [l for l in _alphabet]
_letters2 = [l+l for l in _letters] # double letters for huge boards
_letters = _letters + _letters2

go2letter = {}
letter2go = {}
_i=0
for l in _letters:
    go2letter[_i] = l
    letter2go[l.upper()] = _i
    letter2go[l.lower()] = _i
    _i = _i+1

# unfortunately a pass in katago policy net is nondeterministically (boardsizeX-1) * (boardsizeY-1) + 1
# so dispense with that and instead use (-1, -1) for a pass, which can never be mistaken for an index
def pointToCoords(point: tuple) -> str:
    "convert 0-indexed point tuple to go coordinates like 'D4', where (-1,-1) is pass" 
    if point[0] >= 0 and point[1] >= 0:
        letter = go2letter[point[0]]
        coord = point[1] + 1
    else:
        return "pass"

    return letter + str(coord)

def coordsToPoint(coords: str) -> tuple[int, int]:
    "convert go goordinate like 'D4' into tuple of 0-indexed point, where 'PASS' becomes (-1, -1)"
    letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    digits = "0123456789"
    c = coords.upper().strip()
    if (c == "PASS"):
        return (-1,-1)
    xStr = ""
    yStr = ""
    for l in c:
        if l in letters:
            xStr = xStr+ l
        elif l in digits:
            yStr = yStr + l

    return (letter2go[xStr], int(yStr.strip())-1)

def isPass(point: tuple[int, int]) -> bool:
    return point[1] < 0 or point[0] < 0

def opponent(color: str) -> str:
    c = color.upper()[0]
    if c == "W":
        return "black"
    elif c == "B":
        return "white"
    else:
        raise ValueError("color string must start with either B or W")

def isOnBoard(point, xsize: int, ysize: int) -> bool:
    "simple check to see if point is inside the board"
    return point[0] >= 0 and point[1] >= 0 and point[0] < xsize and point[1] < ysize

def goban2Query(goban: 'Goban', id: str, maxVisits=2, flipPlayer=False, allowedMoves: list[tuple[int, int]] or None = None) -> dict:
    "convert a goban into a query dict for sending to KataGo."
    # FIXME: maybe goutils isn't a great place for this, but other places are just as dubious 
    import time
    #print("PREPPING QUERY ", idname)
    id = id + "_" + str(time.time_ns())

    initial, moves = goban.stones_n_moves_coords()

    restricted = None
    if allowedMoves:
        restricted = allowedMoves

    if len(moves) == 0:
        if len(initial) > 0:
            moves = [initial[-1]]
            initial = initial[:-1]

    white_stones = goban.white_stones()
    black_stones = goban.black_stones()
    
    query = {
        "id": id,
        "boardXSize": goban.xsize,
        "boardYSize": goban.ysize,
        "initialStones": initial,
        "rules": "Chinese",
        "maxVisits": maxVisits,
        "moves": moves,
        "black_stones": black_stones,
        "white_stones": white_stones,
        "komi": goban.komi,
        "includeOwnership": True,
        "includePolicy": True,
        "includePVVisits": True
    }

    toplay = goban.toPlay.upper()
    if flipPlayer: toplay = opponent(toplay).upper()

    if restricted:
        theMoves= [pointToCoords(p) for p in restricted]
        #print("ALLOW MOVES: ", theMoves)
        theDict = {
                'player': toplay,
                'moves' : theMoves,
                'untilDepth': 1,
                }

        query['allowMoves'] = [theDict]

    if len(moves) == 0:
        query["initialPlayer"] = toplay
    else:
        # KataGo tries to "guess" which perspective I want (black or white's).
        # This leads to nonsense results when moves[] available. So, force a pass
        # if needed to keep the side to play correct
        #print(toplay, opponent(toplay))
        if toplay[0].upper() == (moves[-1][0])[0].upper():
            moves.append([opponent(toplay)[0].upper(), "pass"])
        #print(f"MOVES: {moves}")
    #print(f"TO PLAY: {self.getBoardToPlay()}")
    return query