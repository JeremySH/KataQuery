# Query Points
# (experimental!)
# Query points allow you to click the
# board to send your script intersections.

# This is useful for triggering deeper analysis
# or for creating games/trainers

# Points can be specified using Query Mode
# or with amiddle-click of the mouse.

# In Query mode:
# Click to create one query_point
# Shift-click to add query_points
# Right-click to delete a query_point

clearAll()

for q in k.query_points:
	# do amazing calculations here
	hover(q, f"ownership: {q.ownership}")
	mark(q, "square")

