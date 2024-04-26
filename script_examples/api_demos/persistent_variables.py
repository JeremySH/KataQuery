# Persistent Variables
# persist() allows you to save variables
# across re-runs of the script

# provide the name of the variable and its starting value
persist("thisHash", k.thisHash)
persist("prevWinrate", k.winrateBlack)
persist("changes", [0])

# show the winrate change since last board change

if thisHash != k.thisHash:
	change = k.winrateBlack - prevWinrate
	changes.insert(0, round(change*100))
	changes = changes[:10]
	status(f"winrate change history: {changes}")
	prevWinrate = k.winrateBlack
	thisHash = k.thisHash
