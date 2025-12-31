
from PyQt5.QtWidgets import QTextEdit, QPlainTextEdit,  QApplication, QMainWindow, QWidget
from PyQt5.QtCore import QObject, pyqtSignal, QSettings
from PyQt5 import QtGui # for the clipboard
import sys

from GlobalSignals import GS
import sys
import traceback
import time

from goutils import to_gopoint
from kataproxy import KataAnswer, GlobalKata, KataGoQueryError, goban2query
from io import StringIO

# localize the line number to the code editor during error reports.
# Actually it's only useful the day that kataquery internal code never throws, heh
_LOCALIZE_LINE_NUMBER = False

# built in functions for the code editor to use

class Bail(Exception):
    "an excption to allow bailing out of a script"
    pass

def helptext(thing):
    "return the documentation text for a thing"
    import pydoc
    return pydoc.plain(pydoc.render_doc(thing))

def khelp(thing):
    "custom help because builtin help() doesn't work in GUI app"
    import pydoc
    print(helptext(thing))

def bail() -> None:
    "exit the script immediately"
    raise Bail

def snooze(seconds:float =0) -> None:
    "sleep for seconds, updating graphics"
    t = time.time()
    QApplication.instance().processEvents()
    while time.time() - t < seconds:
        time.sleep(1/60)
        QApplication.instance().processEvents()

def bookmark(g: 'Goban', location: str="current") -> None:
    "add a bookmark for the passed Goban, at location 'start', 'end' or 'current'(default)"
    GS.addBookmark.emit({'goban': g, 'location': location})

def status(info: str, **kwargs):
    "change status line to provided text"
    GS.statusBarPrint.emit(str(info))

def mark(gopoint: tuple or str or dict, label="triangle", halign='center', valign='center', scale=1.0) -> None:
    """
    Mark a gopoint [e.g. (3,3)] with a symbol or
    text. Symbol types are 'triangle' 'square' 'circle', 'x', and 'clear'
    all other text is treated as is.
    if 'clear', remove the mark at the provided point.
    """
    global k

    pos = to_gopoint(gopoint)

    if type(pos) != tuple:
        return # FIXME: exception might be more appropriate, though annoying.

    options = {'halign': halign, 'valign': valign, 'rgb': None, 'scale': scale}

    GS.addMark.emit(pos, str(label), options)

def ghost(gopoint: tuple or str or dict, color: str, scale=1.0) -> None:
    "make a translucent stone at this go point"
    pos = to_gopoint(gopoint)
    if type(pos) != tuple:
        return # FIXME: exception might be more appropriate, though annoying.
    options = {'scale': scale}    
    
    GS.addGhostStone.emit(color, pos, options)

def clearGhosts() -> None:
    "clear all ghost stones on the board"
    GS.clearAllGhosts.emit()

def clearMarks() -> None:
    """
    clear all marks on the board
    """
    GS.clearAllMarks.emit()

def clearHeat() -> None:
    "clear the heatmap"
    GS.clearAllHeat.emit()

def clearAll() -> None:
    "clear everything but the stones"
    GS.clearAllMarkup.emit()
    GS.clearAllGhosts.emit()
    GS.clearHoverTexts.emit()
    clearStatus()

def clearStatus() -> None:
    "clear the status line"
    GS.statusBarPrint.emit("")

def heat(gopoint: tuple or str, value: float) -> None:
    """
    set the heat value for gopoint [e.g. (3,3)] from 0 to 1
    """
    pos = to_gopoint(gopoint)

    GS.heatValueChanged.emit(pos, value)

def haveK() -> bool:
    "does k exist? OUTDATED FUNCTION, cuz it always exists"
    return k != None

def quickPlay(katainfo: 'KataAnswer', plays: list, visits=2) -> 'KataAnswer':
    """
    play a sequence of moves on the provided KataAnswer
    and return a new KataAnswer Analysis.
    
    plays is a list of pairs like [["black", "D4"], ["white" "Q16"]].
    Coordinates must be in GTP format (not ints)
    
    This function is ugly and will change
    """
    kata = GlobalKata()
    if kata == None:
        return katainfo
    
    orig = dict(katainfo.answer['original_query'])
    orig['moves'] = orig['moves'] + plays
    orig['id'] = "codeAnalysis_" + str(time.time_ns())
    orig['maxVisits'] = max(visits,2)
    response = kata.analyze(orig)

    return KataAnswer(response)

def analyze(goban: 'Goban', visits=2, allowedMoves: list[tuple[int, int]] =  None, nearby: int=0) -> 'KataAnswer':
    "Analyze a goban. If 'nearby' > 0, analyze points within specified hop distance of existing stones"
    allowed = None
    if nearby > 0:
        allowed = goban.nearby_stones(nearby)
    else:
        allowed = allowedMoves

    kata = GlobalKata() # if this doesn't succeed it's a KataQuery bug
    
    id = "codeAnalysis" + "_" + str(time.time_ns())
    
    q = goban2query(goban, id, maxVisits=visits, allowedMoves = allowed)
    response = kata.analyze(q)
    return KataAnswer(response)

def opponent(color: str) -> str:
    "return the opponent's color"
    if color[0].upper() == "W":
        return "black"
    else:
        return "white"

def dist(pos1: tuple[int, int] or str or dict, pos2: tuple[int, int] or str or dict,) -> int:
    "return the manhattan distance between 2 go points"
    p1 = to_gopoint(pos1)
    p2 = to_gopoint(pos2)
    return abs(p1[0]-p2[0]) + abs(p1[1] - p2[1])

def set_clipboard(stuff: str) -> None:
    "set the clipboard to stuff"
    app = QApplication.instance()
    app.clipboard().setText(str(stuff))

def get_clipboard() -> str:
    "get the clipboard as text"
    app = QApplication.instance()
    return app.clipboard().text()

def log(*args, **kwargs) -> None:
    "like print() but to the GUI log"
    s = StringIO("")
    kwargs['file'] = s
    print(*args, **kwargs)

    GS.CodeGUI_LogPrint.emit(s.getvalue())

def clearLog() -> None:
    "clear the GUI log"
    GS.CodeGUI_LogClear.emit()

def msgBox(msg: str, buttons:list[str] or None = None) -> str:
    "Display a message box with buttons if desired. Returns the name of the button clicked."
    tops = QApplication.instance().topLevelWidgets()
    w = None
    for t in tops:
        if issubclass(t.__class__, QMainWindow):
            w = t
            break

    mb = QtWidgets.QMessageBox(w)

    buttonDict = {}
    if buttons:
        for b in buttons:
            buttonObject = mb.addButton(b, QtWidgets.QMessageBox.AcceptRole)
            buttonDict[buttonObject] = b

    mb.setText(str(msg))
    mb.exec_()

    if mb.clickedButton() in buttonDict:
        return buttonDict[mb.clickedButton()]
    else:
        return "OK"

def chooseFile(prompt:str or None =None, save:bool =False, default:str="", extension:str="", multi=False) -> str:
    """
    present an open/save file dialog box using 'prompt' and return filename(s) (or None if canceled)
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

def hover(gopoint: tuple[int,int], text:str ) -> None:
    p = to_gopoint(gopoint)
    GS.setHoverText.emit(p, str(text))

def clearHovers() -> None:
    GS.clearHoverTexts.emit()

def _guiPing(id: str, title:str) -> None:
    "ping the gui to show me"
    GS.CodeGUI_SetTitle.emit(id, title)
    GS.CodeGUI_ShowMe.emit(id)

def _buttonX(id: str, title: str) -> bool:
    "internal function to access a GUI button"
    GS.CodeGUI_SetTitle.emit(id, title)
    d = {"clicked": False, "title": title, "default_value": False}
    return d

def _checkX(id: str, title: str, default_value: bool = False) -> dict:
    "internal function to access a GUI checkbox"
    GS.CodeGUI_SetTitle.emit(id, title)
    GS.CodeGUI_SetChecked.emit(id, default_value)
    d = {"checked": default_value, "title": title, "default_value": default_value}
    return d

def _sliderX(id: str, title: str, default_value:float = 0.0, min_value:float =0.0, max_value: float=0.0, value_type:str ='float') -> dict:
    "internal function to access a GUI slider"
    GS.CodeGUI_SetTitle.emit(id, title)
    GS.CodeGUI_SetSliderType.emit(id, value_type)
    GS.CodeGUI_SetSliderRange.emit(id, min_value, max_value)
    GS.CodeGUI_SetSliderValue.emit(id, default_value)
    d = {"title": title, "value": default_value, "min_value": min_value, "max_value": max_value, "value_type": value_type, "default_value": default_value}
    return d

extrafuncs = {
    "help": khelp,
    "helptext": helptext,
    "status": status,
    "mark": mark,
    "ghost": ghost,
    "clearMarks": clearMarks,
    "clearHeat": clearHeat,
    "clearStatus": clearStatus,
    "clearGhosts": clearGhosts,
    "hover": hover,
    "clearHovers": clearHovers,
    "clearAll": clearAll,
    "opponent": opponent,
    "heat": heat,
    "havek": haveK,
    "quickPlay": quickPlay,
    "analyze": analyze,
    "set_clipboard": set_clipboard,
    "get_clipboard": get_clipboard,
    "log": log,
    "clearLog": clearLog,
    "msgBox": msgBox,
    "chooseFile": chooseFile,
    "_buttonX": _buttonX,
    "_checkX": _checkX,
    "_sliderX": _sliderX,
    "_guiPing": _guiPing,
    "bail": bail,
    "dist": dist,
    "snooze": snooze,
    "bookmark": bookmark,
    "KataGoQueryError": KataGoQueryError
}

# the GUI functions have to be compiled
# so as to stay within the script context
GUI_FUNCS_SRC = ""
buttonFuncTemplate = """
def button{n}(title:str="button{n}") -> bool:
    "connect to GUI button {n} and return true whenever pressed"
    _guiPing("button{n}", title)
    if 'button{n}' in __GUI__:
        x =  __GUI__['button{n}']['clicked']
        
        # any change to params refreshes the item
        if title != __GUI__['button{n}']['title']:
            d = _buttonX('button{n}', title)
            __GUI__['button{n}'] = d

        __GUI__['button{n}']['clicked'] = False
        return x
    else:
        d = _buttonX('button{n}', title)
        __GUI__['button{n}'] = d
        return __GUI__['button{n}']["clicked"]

"""

checkFuncTemplate = """
def check{n}(title:str="check{n}", default_value:bool =False) -> bool:
    "connect to GUI checkbox {n} and return default value on first run, and its value otherwise"
    _guiPing("check{n}", title)
    changed = False
    if 'check{n}' in __GUI__:
        x = __GUI__['check{n}']['checked']
        # any change to params refershes the item
        if title != __GUI__['check{n}']['title']:
            changed = True
        elif default_value != __GUI__['check{n}']['default_value']:
            print("DEFAULT CHANGED: ", x, default_value)
            changed = True

        if not changed:
            return x

    d = _checkX('check{n}', title, default_value = default_value)
    __GUI__['check{n}'] = d
    return default_value
"""

sliderFuncTemplate = """
def slider{n}(title: str="dial{n}", default_value:float =0.0, min_value:float =0.0, max_value:float =1.0, value_type:float ='float') -> float:
    "connect to GUI checkbox {n} and return default value on first run, and its value otherwise."
    _guiPing("dial{n}", title)
    changed = False
    if 'dial{n}' in __GUI__:
        x = __GUI__['dial{n}']['value']
        if __GUI__['dial{n}']['value_type'] == 'int':
            x = int(round(x))
        d = __GUI__['dial{n}']
        if title != d['title']:
            changed = True
        elif default_value != d['default_value']:
            #print("default changed: ", default_value, d['default_value'])
            changed = True
        elif min_value != d['min_value']:
            #print("min changed", min_value, d['min_value'])
            changed = True
        elif max_value != d['max_value']:
            #print("max changed: ", max_value, d['max_value'])
            changed = True
        elif value_type != d['value_type']:
            changed = True

        if not changed:
            return x

    d = _sliderX('dial{n}', title, default_value=default_value, min_value=min_value, max_value=max_value, value_type=value_type)
    __GUI__['dial{n}'] = d
    if value_type == 'int':
        return int(round(default_value))
    else:
        return default_value

dial{n} = slider{n} # `dial1` becomes alias for `slider1`
"""

# build it
for n in range(8):
    GUI_FUNCS_SRC += buttonFuncTemplate.format(n = str(n+1))
    GUI_FUNCS_SRC += checkFuncTemplate.format(n = str(n+1))
    GUI_FUNCS_SRC += sliderFuncTemplate.format(n = str(n+1))


class CodeRunner(QObject):
    "runs custom python code against a position"
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.context_global = {}
        self.code = None

        # this is needed as text to execute in the same global context
        # as the running script, rather than the context of this very file
        __code_preamble = """
def persist(variable: str, val) -> None: 
    __saved__[variable] = True
    if variable not in globals(): globals()[variable] = val
"""     
        #self.preambleC = code.compile_command(__code_preamble, symbol="exec")
        self.preambleC = compile(__code_preamble + GUI_FUNCS_SRC, "<preamble>", 'exec', optimize=1)
    
    def printit(self, thing):
        # placeholder until gui shows stdout
        print(f"{thing}", end='', file=sys.stderr)


    def setCode(self, sourceCode: str) -> None:

        try:
            #c = code.compile_command(sourceCode, filename="<code editor>", symbol="exec")
            c = compile(sourceCode, "<code editor>", 'exec')

            if (c):
                self.code = c
            else:
                self.code = None

        except Exception as e:
            traceback.print_exc()
            status(type(e).__name__ + ": " + str(e))
            self.code = None


    def run(self, kataResults: dict = None, extraGlobals=None, explicit=False, gui_run=False, query_points=None) -> None:
        if kataResults != None:
            self.createContexts(kataResults, extraGlobals=extraGlobals, manual_run=explicit, gui_run=gui_run, query_points=query_points)

        #print("EXPLICIT IS ", explicit)
        if self.code != None:
            # TODO: set context's __builtins__ to None and rebuild necessary stuff like print
            try:
                exec(self.preambleC, self.context_global, self.context_global)
                GS.CodeGUI_HideAll.emit()
                exec(self.code, self.context_global, self.context_global)
            except Bail as e:
                # don't care
                pass
            
            except Exception as e:
                traceback.print_exc()
                tb_info = traceback.extract_tb(e.__traceback__)

                # focus the line & file on the code editor rather than internal code
                name, line, func, code = tb_info[-1]
                if _LOCALIZE_LINE_NUMBER:
                    for tup in tb_info:
                        n = tup[0]
                        if n == '<code editor>':
                            name, line, func, code = tup


                status(f"{type(e).__name__} : {str(e)}, '{name}' line {line}")

    def getSavedVars(self, glob: dict, loc: dict) -> tuple[dict, dict]:
        if '__saved__' not in glob:
            return {}, {}

        savedNames = glob['__saved__']
        loc_res = {} ; glob_res = {}
        for name in savedNames.keys():
            if name in glob:
                glob_res[name] = glob[name]
            if name in loc:
                loc_res[name] = loc[name]

        return glob_res, loc_res
    
    def getGlobals(self) -> dict:
        return self.context_global
    
    def createContexts(self, kataResults: dict, extraGlobals: dict = None, manual_run=False, gui_run=False, query_points=None) -> None:

        global k
        #print("CREATE CONTEXTS: explicit: ", manual_run)
        moreglobs = extraGlobals

        if extraGlobals == None: moreglobs = {}

        k = KataAnswer(kataResults)

        setattr(k, "depth", kataResults['depth'])
        setattr(k, "manual_run", manual_run)
        setattr(k, "gui_run", gui_run)
        qp = []
        if query_points:
            qp = [k.get_point(q) for q in query_points]
        setattr(k, "query_points", qp)

        saved_globals, saved_locals = self.getSavedVars(self.context_global, self.context_global)

        self.context_global = {'__saved__': {}}

        self.context_global.update(extrafuncs)
        self.context_global.update(moreglobs)
        self.context_global.update(saved_globals)

        # k will always override, sry
        self.context_global["k"] = k

from pyqode.core.api import CodeEdit, ColorScheme
from pyqode.core import modes, panels, api
from pyqode.python import modes as pymodes
import os
import project_globals

class CodeEditor(CodeEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.codeRunner = CodeRunner()
        self.lastAnswer = None
        self.textChanged.connect(self.markDirty)
        self._dirty = True
        self.GUI_Saved = {} # saved gui info by the script
        self.queryPoints = None
        self.disabled = False

        # code completion server with kataquery additions
        if project_globals.appIsFrozen():
            self.backend.start(os.path.join(project_globals.resource_directory, "bin", "completion_server"))
        else:
            self.backend.start(os.path.join(project_globals.resource_directory, "bin", "completion_server.py"))

        self.modes.append(modes.CodeCompletionMode())
        self.panels.append(panels.SearchAndReplacePanel(), api.Panel.Position.BOTTOM)
        
        # determine if environment is dark or light
        # and select an appropriate theme
        pal = QApplication.instance().palette()

        self.setPalette(pal) # needed for background

        col = pal.window().color()
        colorScheme = 'xcode'
        if col.lightness() < 127:
            colorScheme = 'lightbulb'
        

        self.modes.append(modes.SymbolMatcherMode()) # match parens, etc.
        self.panels.append(panels.LineNumberPanel()) # show line numbers

        # TBH this python-specific stuff doesn't add much
        # value from the default as far as I can see

        self.modes.append(pymodes.PythonSH(self.document(), color_scheme = ColorScheme(colorScheme)))
        #self.modes.append(pymodes.PyAutoCompleteMode())        
        self.modes.append(pymodes.PyIndenterMode()) # not sure what this does?

        #patch a bug
        def _handle_indent_in_statement(fullline, lastword, post, pre):
            return post,pre
        m = pymodes.PyAutoIndentMode()
        m._handle_indent_in_statement = _handle_indent_in_statement

        self.modes.append(m) # indent when inside a scope

        self.use_spaces_instead_of_tabs = False
        self.font_size = 12

        self.setTabStopDistance(QtGui.QFontMetricsF(self.font()).horizontalAdvance(' ') * 2)
        
        GS.fullAnalysisReady.connect(self.handleFullAnalysis)
        GS.quickAnalysisReady.connect(self.handleQuickAnalysis) 
        GS.queryPoints.connect(self.handleQueryPoint)
        GS.CodeGUI_Changed.connect(self.newGUIInfo)
        GS.MainWindowReadyAndWilling.connect(self.afterStartup)
        # FIXME: QSettings is not a great choice for persisting the scripts
        # because the user can't easily access them like they could if they
        # were simply files

        settings = QSettings()

        self.slots = []
        self.currentSlot = None # let main window set me up, as it holds the actions
        self.previousSlot = None

    def afterStartup(self) -> None:
        settings = QSettings()
        self.disabled = settings.value("codeeditor/disabled", False, type=bool)
        
        self.nameAllSlots()
        self.activateSlot(settings.value("codeeditor/current_slot", 1, type=int), force=True)

    def saveCurrentSlot(self) -> None:
        settings = QSettings()
        key = f"codeeditor/slot{self.currentSlot}_src"
        settings.setValue(key, self.document().toPlainText())
        self.nameASlot(self.currentSlot)

    def activateSlot(self, slotNum: int, force:bool =False) -> None:
        """
        Activate the current code slot and load the source code.
        If forced is True do it even if the current code slot
        is the same. This will remove undo history, but is
        useful on startup
        """

        # let user repeat the number to alternate
        if slotNum == self.currentSlot and self.previousSlot:
            slotNum = self.previousSlot
        else:
            self.previousSlot = self.currentSlot

        # have to do nothing otherwise undo history is lost
        if not force and self.currentSlot == slotNum: return

        settings = QSettings()
        key = f"codeeditor/slot{slotNum}_src"
        text = settings.value(key, "")
        self.document().setPlainText(text)
        self.moveCursor(QtGui.QTextCursor.Start)

        self.currentSlot = slotNum
        settings.setValue("codeeditor/current_slot", self.currentSlot)
        self.nameAllSlots()
        GS.Code_SlotActivated.emit(slotNum)

    def slotSelected(self) -> None:
        self.saveCurrentSlot()
        self.activateSlot(self.sender().data())
        self.GUI_Saved = {}
        self._dirty = True
        if not self.disabled:
            self.runit(explicit=False)

    def nameASlot(self, slotnum: int) -> None:
        "auto-generate a name for the slot in the menu"
        #print("NAMING SLOT ", slotnum)
        settings = QSettings()
        text = settings.value(f"codeeditor/slot{slotnum}_src", "")
        name = ""
        if text != "":
            for line in text.splitlines():
                stripped = line.strip()
                if len(stripped) > 0 and stripped[0] == "#":
                    stripped = stripped.strip("#")
                    name = stripped.strip()
                    if len(name) > 30:
                        name = name[:29] + "…"
                    #print(f"SLOT {slotnum} name: '{name}'")
                    break
        GS.Code_SetSlotName.emit(slotnum, name)

    def nameAllSlots(self) -> None:
        for s in range(1,21):
            self.nameASlot(s)

    def appWillClose(self) -> None:
        self.saveCurrentSlot()

    def setGUI(self, tabWidget: QWidget) -> None:
        self.codegui = CodeGUISwitchboard(tabWidget)

    def markDirty(self) -> None:
        self._dirty = True

    def runit(self, explicit:bool =False, gui_run=False, query_points=None) -> None:
        "run against the analysis in self.lastAnswer. If explicit is true, treat this as a manual run by user."
        if self.lastAnswer != None:
            if "error" in self.lastAnswer:
                print(f"KATAGO ERROR: {self.lastAnswer['error']}", file=sys.stderr)
                return

            if self._dirty:
                self.codeRunner.setCode(self.document().toPlainText())
                self._dirty = False
                self.saveCurrentSlot()

            self.codeRunner.run(self.lastAnswer, extraGlobals = {"__GUI__": self.GUI_Saved}, explicit=explicit, gui_run=gui_run, query_points=self.queryPoints)
            self.updateGUIVars()
        else:
            GS.statusBarPrint.emit("No KataGo Analysis to run against.")

    def runRequested(self) -> None:
        "User has explicitly run the script via menu or shortcut."
        print("RUN REQUESTED.")
        self.runit(explicit = True)
    
    def handleDisableCode(self, value) -> None:
        "Disable/Enable running the code automatically"
        self.disabled = value
        settings = QSettings()
        settings.setValue("codeeditor/disabled", value)
        
        if not self.disabled:
            self.runit()
        else:
            clearAll()

    def updateGUIVars(self) -> None:
        g = self.codeRunner.getGlobals()
        if "__GUI__" in g:
            self.GUI_Saved.update(g['__GUI__'])

    def handleQuickAnalysis(self, signalData: dict) -> None:
        "Handle an incoming quick analysis from KataProxy"
        self.handleAnalysis(signalData, kind='quick')

    def handleFullAnalysis(self, signalData: dict) -> None:
        "Handle an incoming full analysis from KataProxy"
        self.handleAnalysis(signalData, kind="full")

    def handleAnalysis(self, signalData: dict, kind:str ='full') -> None:
        "Handle an analysis from KataProxy. kind can be 'quick' or 'full'."
        signalData['payload']['depth'] = kind
        self.lastAnswer = signalData['payload']
        if not self.disabled:
            self.runit()

    def handleQueryPoint(self, qpoints: list[tuple[int, int]]) -> None:
        self.queryPoints = qpoints
        self.runit(gui_run=True, query_points=self.queryPoints) # FIXME: not sure if appropriate
        self.queryPoints = None

    def newGUIInfo(self, info: dict) -> None:
        changed = False
        for thing in self.GUI_Saved.keys():
            if thing in info:
                self.GUI_Saved[thing].update(info[thing])
                changed = True
        if changed and not self.disabled:
            self.runit(explicit=False, gui_run=True)

from PyQt5 import QtWidgets
class CodeGUISwitchboard(QObject):
    # There is a strong separation between output from the code
    # and input from the user. This prevents infinite loops in the GUI,
    # with the caveat that blockSignals() prevents any other code
    # from getting code-initiated update signals when a GUI item is changed from the script
    def __init__(self, guiTab, parent=None) -> None:
        super().__init__(parent)
        # connect checkboxes, butttons, sliders, and the log output
        checkboxes = guiTab.findChildren(QtWidgets.QCheckBox)
        buttons = guiTab.findChildren(QtWidgets.QPushButton)
        sliders = guiTab.findChildren(QtWidgets.QDial)

        # holds the state of all controllers, for passing around in signals

        self.GUI_state = {}

        # console log display
        self.logOutput = guiTab.findChild(QtWidgets.QPlainTextEdit)
        self.logOutput.setMaximumBlockCount(1000)
        GS.CodeGUI_LogPrint.connect(self.log)
        GS.CodeGUI_LogClear.connect(self.logOutput.clear)
        conFont = QtGui.QFont("Menlo", 12, QtGui.QFont.Monospace)
        conFont.insertSubstitutions("Menlo", ["Monaco", "Consolas", "Liberation Mono", "Monospace"])
        self.logOutput.setFont(conFont)

        #slider labels, a bit of a hack
        labels = guiTab.findChildren(QtWidgets.QLabel)
        labels = [l for l in labels if l.objectName()[:10] == "label_dial"]

        ui_stuff = checkboxes + buttons + sliders + [self.logOutput]

        self.lookup = {}
        self.lookup_labels = {}

        for x in ui_stuff:
            self.lookup[x.objectName()] = x

        for x in labels:
            self.lookup_labels[x.objectName()] = x

        # shoehorn object names into signals
        for c in checkboxes:
            n = c.objectName()
            c.toggled.connect(lambda v, name=n: self.checkboxClicked(name, v))
            self.GUI_state[n] = {"kind": "checkbox", "checked": c.isChecked(), "title": n} #, "default_value": False}
        
        for b in buttons:
            n = b.objectName()
            b.clicked.connect(lambda v, name=n: self.buttonClicked(name, v))
            self.GUI_state[n] = {"kind": "button", "clicked": False, "title": n} #, "default_value": False}
            
        for s in sliders:
            n = s.objectName()
            s.valueChanged.connect(lambda v, name=n: self.sliderChangedRaw(name, v))
            setattr(s, "maxVal", 1.0)
            setattr(s, "minVal", 0.0)
            setattr(s, "value_type", 'float')
            self.GUI_state[n] = {"kind": "slider", "min_value": 0.0, "max_value": 1.0, "value": 0.0, "value_type": "float", "title": n} #, "default_value": 0.0}

        #for s in [GS.CodeGUI_ButtonClicked, GS.CodeGUI_CheckboxChanged, GS.CodeGUI_SliderChanged]:
        #    s.connect(self.printEvents)            

        GS.CodeGUI_SetTitle.connect(self.setATitle)
        GS.CodeGUI_SetToolTip.connect(self.setAToolTip)
        GS.CodeGUI_SetChecked.connect(self.setChecked)
        GS.CodeGUI_SetSliderType.connect(self.sliderSetType)
        GS.CodeGUI_SetSliderRange.connect(self.sliderSetRange)
        GS.CodeGUI_SetSliderValue.connect(self.sliderSetValue)

        GS.CodeGUI_ShowMe.connect(self.showMe)
        GS.CodeGUI_HideAll.connect(self.hideAll)
        for x in ui_stuff:
            if x != self.logOutput:
                GS.CodeGUI_SetTitle.emit(x.objectName(), f"{x.objectName()}")

        # test
        #GS.CodeGUI_SliderSetRange.emit(sliders[0].objectName(), 0.3, 120.0)
        GS.CodeGUI_Changed.connect(self.codeGUIChangedTest)
        self.checkboxes = checkboxes
        self.buttons = buttons
        self.sliders = sliders

    def codeGUIChangedTest(self, info: dict) -> None:
        #print("CODE GUI CHANGED: ", info, file=sys.stderr)
        pass

    def log(self, stuff:str) -> None:
        self.logOutput.moveCursor(QtGui.QTextCursor.End)
        self.logOutput.insertPlainText(stuff)
        self.logOutput.moveCursor(QtGui.QTextCursor.End)
        
    def setATitle(self, name: str, text: str) -> None:
        if name in self.lookup:
            o = self.lookup[name]
            if hasattr(o, "setText"):
                o.setText(text)
            else: # maybe for dials this helps
                maybe = "label_" + o.objectName()
                if maybe in self.lookup_labels:
                    self.lookup_labels[maybe].setText(text)
            self.GUI_state[name]['title'] = text

    def setAToolTip(self, name: str, text: str) -> None:
        if name in self.lookup:
            self.lookup[name].setToolTip(text)

    def setChecked(self, name: str, onOff:bool) -> None:
        if name in self.lookup:
            o = self.lookup[name]
            o.blockSignals(True)
            o.setChecked(onOff)
            o.blockSignals(False)

    def slider2Float(self, val:int, minV:float, maxV:float) -> float:
        return minV + ((maxV-minV)*val)/100000.0
    
    def float2Slider(self, val:float, minV:float , maxV:float) -> int:
        return int(100000.0*(val-minV)/(maxV-minV))

    def sliderChangedRaw(self, name:str , value:int ) -> None:
        # convert integer crap into ranged value floats
        if name in self.lookup:
            #print("Slider CHANGED: ", self.GUI_state[name])
            s = self.GUI_state[name]
            val = self.slider2Float(value, s['min_value'], s['max_value'])
            self.GUI_state[name]['value'] = val
            #GS.CodeGUI_SliderChanged.emit(name, val)
            self.GUI_Changed()
        else:
            print("DUNNO: ", name)

    def sliderSetValue(self, name:str, value: int) -> None:
        if name in self.lookup:
            state = self.GUI_state[name]
            o = self.lookup[name]
            o.blockSignals(True)
            o.setValue(self.float2Slider(value, state['min_value'], state['max_value']))
            o.blockSignals(False)

    def sliderSetRange(self, name:str , min_val:float, max_val:float) -> None:
        if name in self.lookup:
            o = self.lookup[name]
            s = self.GUI_state[name]
            minV = s['min_value']
            maxV = s['max_value']
            val = self.slider2Float(o.value(), minV, maxV)
            if val > maxV:
                # check for change and address it in gui
                val = maxV
            if val < minV:
                val = minV
            o.blockSignals(True)
            o.setValue(self.float2Slider(val, minV, maxV))
            o.blockSignals(False)
            u = {'value': val, 'min_value': min_val, 'max_value': max_val}

            self.GUI_state[name].update(u)

    def sliderSetType(self, name:str, value_type:str) -> None:
        if name in self.lookup:
            self.GUI_state[name]['value_type'] = value_type
 
    def buttonClicked(self, name:str, value=None) -> None:
        # only handle one button at a time, much easier
        for b in self.buttonNames:
            self.GUI_state[b]['clicked'] = False
        if name in self.buttonNames:
            self.GUI_state[name]['clicked'] = True
            self.GUI_Changed(clear_buttons=False)

    def checkboxClicked(self, name:str, value:bool) -> None:
        if name in self.checkboxNames:
            self.GUI_state[name]['checked'] = value
            self.GUI_Changed()

    def showMe(self, name: str) -> None:
        if name in self.lookup:
            self.lookup[name].setEnabled(True)
            self.lookup[name].show()
        
        n = "label_"+name
        if n in self.lookup_labels:
            self.lookup_labels[n].setEnabled(True)
            self.lookup_labels[n].show()


    def hideAll(self) -> None:
        for name, item in self.lookup.items():
            if item != self.logOutput:
                item.setEnabled(False)
                self.setATitle(name, name)
                #item.hide()
        for name, item in self.lookup_labels.items():
            item.setEnabled(False)
            #item.hide()
            self.setATitle(name, name)
        

    # keep in the code for reference
    @property
    def buttonNames(self) -> list[str]:
        return [o.objectName() for o in self.buttons]
    
    @property
    def dialNames(self) -> list[str]:
        return [o.objectName() for o in self.sliders]

    @property
    def checkboxNames(self) -> list[str]:
        return [o.objectName() for o in self.checkboxes]

    def GUI_Changed(self, clear_buttons:bool = True) -> None:
        # by default clear the buttons to False
        # as I only want buttons true after a click
        if clear_buttons:
            for b in self.buttonNames:
                self.GUI_state[b]['clicked'] = False

        GS.CodeGUI_Changed.emit(self.GUI_state)
