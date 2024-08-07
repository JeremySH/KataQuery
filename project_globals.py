# for project-level information set in main
import sys, os
from PyQt5.QtWidgets import QApplication, QMainWindow

import sys, os
def appIsFrozen() -> bool:
	return getattr(sys, 'frozen', False)

if appIsFrozen():
    app_directory = sys._MEIPASS
else:
    app_directory = os.path.abspath(os.path.dirname(__file__))

resource_directory = os.path.join(app_directory, "resources")

def getMainWindow() -> 'QMainWindow':
	"get the main window, or None if not found"
	tops = QApplication.instance().topLevelWidgets()
	w = None
	for t in tops:
	    if issubclass(t.__class__, QMainWindow):
	        w = t
	        break
	return w