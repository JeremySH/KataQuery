# kq
# all the custom commands available to KataQuery scripts

# this module is automatically imported
# by kataquery before running a user script,
# similar to `from kq import *`

# however, externally created modules by 
# the user MUST use `import` to get these functions,
# as injecting kq into module globals on the fly is
# too BlackMagic™

import PyQt5.QtWidgets, PyQt5.QtGui

import pydoc, time, io

import GlobalSignals
import goutils
import kataproxy 

class Bail(Exception):
    "an exception to allow bailing out of a script"
    pass

def helptext(thing) -> str:
    "return the documentation text for a `thing``"
    return pydoc.plain(pydoc.render_doc(thing))

def bail() -> None:
    "exit the script immediately"
    raise Bail

def status(info: str, **kwargs) -> None:
    "change status line to provided `info`"
    GlobalSignals.GS.statusBarPrint.emit(str(info))

def mark(gopoint: tuple or str or dict, label: str="triangle", 
         halign: str='center', valign: str='center', scale: float=1.0) -> None:
    """
    Mark a `gopoint` [e.g. (3,3), or moveInfo] with a symbol or
    text. Symbol types are 'triangle' 'square' 'circle', 'x'
    all other text is treated as is.
    """
    if not gopoint: return

    pos = goutils.to_gopoint(gopoint)

    if type(pos) != tuple:
        return # FIXME: exception might be more appropriate, though annoying.

    options = {'halign': halign, 'valign': valign, 'rgb': None, 'scale': scale}

    GlobalSignals.GS.addMark.emit(pos, str(label), options)

def ghost(gopoint: tuple or str or dict, color: str, scale: float=1.0) -> None:
    "make a translucent stone at this `gopoint` of color `color``"
    if not gopoint: return

    pos = goutils.to_gopoint(gopoint)
    if type(pos) != tuple:
        return # FIXME: exception might be more appropriate, though annoying.
    options = {'scale': scale}    
    
    GlobalSignals.GS.addGhostStone.emit(color, pos, options)

def hover(gopoint: tuple[int,int] or dict or str, text:str ) -> None:
    "set the hover text over this `gopoint`"
    if not gopoint: return

    p = goutils.to_gopoint(gopoint)
    GlobalSignals.GS.setHoverText.emit(p, str(text))

def heat(gopoint: tuple[int, int] or dict or str, value: float) -> None:
    """
    set the heat value for `gopoint`, from 0 to 1
    """
    if not gopoint: return

    pos = goutils.to_gopoint(gopoint)

    GlobalSignals.GS.heatValueChanged.emit(pos, value)

def log(*args, **kwargs) -> None:
    "like `print()` but to the GUI log"
    s = io.StringIO("")
    kwargs['file'] = s
    print(*args, **kwargs)

    GlobalSignals.GS.CodeGUI_LogPrint.emit(s.getvalue())

def clearGhosts() -> None:
    "clear all ghost stones on the board"
    GlobalSignals.GS.clearAllGhosts.emit()

def clearMarks() -> None:
    """
    clear all labels on the board
    """
    GlobalSignals.GS.clearAllMarks.emit()

def clearHeat() -> None:
    "clear the heatmap"
    GlobalSignals.GS.clearAllHeat.emit()

def clearHovers() -> None:
    "clear all hovertexts for the board"
    GlobalSignals.GS.clearHoverTexts.emit()

def clearStatus() -> None:
    "clear the status line"
    GlobalSignals.GS.statusBarPrint.emit("")

def clearLog() -> None:
    "clear the GUI log"
    GlobalSignals.GS.CodeGUI_LogClear.emit()
    
def clearAll() -> None:
    "clear all markings but not the GUI log"
    GlobalSignals.GS.clearAllMarkup.emit()
    GlobalSignals.GS.clearAllGhosts.emit()
    GlobalSignals.GS.clearHoverTexts.emit()
    clearStatus()

def snooze(seconds: float=0) -> None:
    "sleep for `seconds`, updating graphics"
    t = time.time()
    PyQt5.QtWidgets.QApplication.instance().processEvents()
    while time.time() - t < seconds:
        time.sleep(1/60)
        PyQt5.QtWidgets.QApplication.instance().processEvents()

def bookmark(g: 'Goban', location: str="current") -> None:
    "add a bookmark for the passed Goban `g`, at location 'start', 'end' or 'current'(default)"
    GlobalSignals.GS.addBookmark.emit({'goban': g, 'location': location})

def quickPlay(katainfo: 'kataproxy.KataAnswer', plays: list, visits: int=2) -> 'kataproxy.KataAnswer':
    """
    play a sequence of moves on the provided KataAnswer `katainfo`
    and return a new KataAnswer Analysis.
    
    `plays` is a list of pairs like [["black", "D4"], ["white" "Q16"]].
    Coordinates must be in GTP format (not ints)
    
    This function is ugly! analyze() is preferred
    """
    kata = kataproxy.GlobalKata()
    if kata == None:
        return katainfo
    
    orig = dict(katainfo.answer['original_query'])
    orig['moves'] = orig['moves'] + plays
    orig['id'] = "codeAnalysis_" + str(time.time_ns())
    orig['maxVisits'] = max(visits,2)
    response = kata.analyze(orig)

    return kataproxy.KataAnswer(response)

def analyze(goban: 'Goban', visits: int=2, 
            allowedMoves: list[tuple[int, int]]= None,
            nearby: int=0) -> 'kataproxy.KataAnswer':
    "Analyze a `goban``. If `nearby` > 0, analyze points within specified hop distance of existing stones"
    allowed = None
    if nearby > 0:
        allowed = goban.nearby_stones(nearby)
    else:
        allowed = allowedMoves

    kata = kataproxy.GlobalKata() # if this doesn't succeed it's a KataQuery bug
    
    id = "codeAnalysis" + "_" + str(time.time_ns())
    
    q = kataproxy.goban2query(goban, id, maxVisits=visits, allowedMoves = allowed)
    response = kata.analyze(q)
    return kataproxy.KataAnswer(response)

def rerun(more_visits: int, max_visits: int) -> None:
    """
    Submit a new analysis request adding `more_visits` to the visits,
    immediately bail() so the script can run again.
    
    If `k.visits >= max_visits`, or `k.depth == "quick"`,
    return like a no-op (without bail())
        
    The purpose is to allow interactive analysis updates from a script,
    and to guarantee a number of visits for later code.
    
    NOTE: CAN ONLY BE CALLED FROM USER SCRIPTS, NOT MODULES.
    """
    if __name__ != "__kq_script__":
    	caller = _caller_module()
    	if caller != "__kq_script__":
        	raise RuntimeError(f"rerun() can only be called from the top-level user script, not '{caller}'")
    
    k = _get_k()
    if k.depth == "quick": return
    if k.visits >= max_visits: return
    visits = min(k.visits + more_visits, max_visits)
    
    GlobalSignals.GS.analyzeVisits.emit(visits)
    bail()

def opponent(color: str) -> str:
    "return the opponent color of `color` ('black' or 'white')"
    if color[0].upper() == "W":
        return "black"
    else:
        return "white"

def dist(pos1: tuple[int, int] or str or dict, pos2: tuple[int, int] or str or dict,) -> int:
    "return the manhattan distance between 2 go points, `pos1` and `pos2`"
    p1 = goutils.to_gopoint(pos1)
    p2 = goutils.to_gopoint(pos2)
    return abs(p1[0]-p2[0]) + abs(p1[1] - p2[1])

def set_clipboard(stuff: str or PyQt5.QtGui.QImage) -> None:
    "set the clipboard to `stuff``, which can be text or a QImage"
    
    app = PyQt5.QtWidgets.QApplication.instance()
    if issubclass(stuff.__class__, PyQt5.QtGui.QImage):
        app.clipboard().setImage(stuff)
    else:
        app.clipboard().setText(str(stuff))

def get_clipboard() -> str:
    "get the clipboard as text"
    app = PyQt5.QtWidgets.QApplication.instance()
    return app.clipboard().text()

def msgBox(msg: str, buttons:list[str] or None = None) -> str:
    "Display a message box with text `msg`, and `buttons` if desired. Returns the name of the button clicked."
    tops = PyQt5.QtWidgets.QApplication.instance().topLevelWidgets()
    w = None
    for t in tops:
        if issubclass(t.__class__, PyQt5.QtWidgets.QMainWindow):
            w = t
            break

    mb = PyQt5.QtWidgets.QMessageBox(w)

    buttonDict = {}
    if buttons:
        for b in buttons:
            buttonObject = mb.addButton(b, PyQt5.QtWidgets.QMessageBox.AcceptRole)
            buttonDict[buttonObject] = b

    mb.setText(str(msg))
    mb.exec_()

    if mb.clickedButton() in buttonDict:
        return buttonDict[mb.clickedButton()]
    else:
        return "OK"

def chooseFile(prompt: str or None =None, save: bool=False, default: str="", extension: str="", multi: bool=False) -> str:
    """
    present an open/save file dialog box using `prompt` and return filename(s) (or None if canceled)
    prompt:    show this prompt string (if possible)
    save:      show save file dialog
    default:   the default file/directory to navigate to
    extension: the extension to automatically apply 
    multi:     allow multiple file selection (returns a list)
    """
    from PyQt5.QtWidgets import QFileDialog
    from PyQt5.QtCore import QDir
    from project_globals import getMainWindow

    dialog = QFileDialog(parent=getMainWindow())
    dialog.setViewMode(QFileDialog.Detail)
    dialog.setDefaultSuffix(extension)

    if multi:
        dialog.setFileMode(QFileDialog.ExistingFiles)

    if save:
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptSave)

    if default != "":
        if type(default) == list:
            dialog.selectFile(default[0])
        else:
            dialog.selectFile(default)

    filenames = None
    if dialog.exec_():
        filenames = dialog.selectedFiles()

    if filenames and not multi:
        return filenames[0]
    else:
        return filenames

def playSound(soundfile:str, volume:int=100) -> None:
    "play a sound file at `volume`"
    GlobalSignals.GS.playSound.emit(soundfile, volume)

def notify(title:str, message: str) -> None:
    "show a system-wide notification with a `title` and `message`"
    GlobalSignals.GS.notification.emit(title, message)

def board2image(max_width=1024) -> PyQt5.QtGui.QImage:
    """
    capture the current board image as a QImage
    sized proportionally to fit in `max_width`
    and return it
    """
    
    # FIXME: error checking
    import os
    from PyQt5.QtCore import QStandardPaths
    
    path = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
    os.makedirs(path, exist_ok=True)
    
    fpath = os.path.join(path, "board_capture.png")

    image = None
    def _getResponse(filename: str):
        nonlocal image
        image = PyQt5.QtGui.QImage()
        image.load(filename)

    GlobalSignals.GS.boardImageCaptured.connect(_getResponse)
    GlobalSignals.GS.captureBoardImage.emit(fpath, max_width)

    while image == None:
        PyQt5.QtWidgets.QApplication.instance().processEvents()

    return image

def _get_k() -> 'kataproxy.KataAnswer':
    "total hack"
    import inspect
    frame = inspect.currentframe()
    try:
        while frame:
            if frame.f_globals.get('k') != None:
                return frame.f_globals['k']
            frame = frame.f_back
    finally:
        del frame

def _caller_module() -> str:
    "for error reporting, retrieve the name of the calling module"
    import inspect
    frame = inspect.currentframe()
    try:
        while frame:
            if frame.f_globals.get('__name__') != __name__:
                return frame.f_globals['__name__']
            frame = frame.f_back
    finally:
        del frame

# these will be here until
# I figure out how do deal the with GUI functions'
# runtime context.
# currently GUI functions must run with access to script globals
# and are therefore defined in codeeditor.py
def _guiPing(id: str, title: str) -> None:
    "internal function. ping the gui to enable a gui item by name"
    GlobalSignals.GS.CodeGUI_SetTitle.emit(id, title)
    GlobalSignals.GS.CodeGUI_ShowMe.emit(id)

def _buttonX(id: str, title: str) -> bool:
    "internal function to access a GUI button"
    GlobalSignals.GS.CodeGUI_SetTitle.emit(id, title)
    d = {"clicked": False, "title": title, "default_value": False}
    return d

def _checkX(id: str, title: str, default_value: bool=False) -> dict:
    "internal function to access a GUI checkbox"
    GlobalSignals.GS.CodeGUI_SetTitle.emit(id, title)
    GlobalSignals.GS.CodeGUI_SetChecked.emit(id, default_value)
    d = {"checked": default_value, "title": title, "default_value": default_value}
    return d

def _sliderX(id: str, title: str, default_value: float=0.0, min_value: float=0.0, max_value: float=0.0, value_type:str ='float') -> dict:
    "internal function to access a GUI slider"
    GlobalSignals.GS.CodeGUI_SetTitle.emit(id, title)
    GlobalSignals.GS.CodeGUI_SetSliderType.emit(id, value_type)
    GlobalSignals.GS.CodeGUI_SetSliderRange.emit(id, min_value, max_value)
    GlobalSignals.GS.CodeGUI_SetSliderValue.emit(id, default_value)
    d = {"title": title, "value": default_value, "min_value": min_value, "max_value": max_value, "value_type": value_type, "default_value": default_value}
    return d
