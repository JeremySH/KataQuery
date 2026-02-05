# opponent()
# get the opponent of a color ("black", "white")

# let's mark the last move for clarity
clearAll()
mark (k.last_move)

# get the opponent's color
other = opponent(k.player)

# impart wisdom
status(f'As {k.player}, you must first think: "what does {other} want?"')