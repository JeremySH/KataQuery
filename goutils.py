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
