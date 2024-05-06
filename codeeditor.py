
from PyQt5.QtWidgets import QTextEdit, QPlainTextEdit,  QApplication, QMainWindow
from PyQt5.QtCore import QObject, pyqtSignal, QSettings
from PyQt5 import QtGui # for the clipboard
import sys

from GlobalSignals import GS
import sys
import traceback
import time

from goutils import pointToCoords, coordsToPoint
from kataproxy import KataAnswer, GlobalKata


# built in functions for the code editor to use

class Bail(Exception):
    "an excption to allow bailing out of a script"
    pass

def bail() -> None:
    raise Bail

def snooze(seconds:float =0) -> None:
    t = time.time()
    QApplication.instance().processEvents()
    while time.time() - t < seconds:
        time.sleep(1/60)
        QApplication.instance().processEvents()

def status(info: str, **kwargs):
    "change status line to provided text"
    GS.statusBarPrint.emit(str(info))

def _getGoPoint(gopoint):
    pos = gopoint

    if type(gopoint) == str:
        if k.answer != None:
            pos = coordsToPoint(gopoint)
    elif hasattr(gopoint, 'pos'): # accomodate move info object
        pos = gopoint.pos

    return pos

def mark(gopoint: tuple or str or dict, label="triangle", halign='center', valign='center', scale=1.0):
    """
    Mark a gopoint [e.g. (3,3)] with a symbol or
    text. Symbol types are 'triangle' 'square' 'circle', 'x', and 'clear'
    all other text is treated as is.
    if 'clear', remove the mark at the provided point.
    """
    global k

    pos = _getGoPoint(gopoint)

    if type(pos) != tuple:
        return # FIXME: exception might be more appropriate, though annoying.

    options = {'halign': halign, 'valign': valign, 'rgb': None, 'scale': scale}

    GS.addMark.emit(pos, str(label), options)

def ghost(gopoint: tuple or str or dict, color: str, scale=1.0) -> None:
    "make a translucent stone at this go point"
    pos = _getGoPoint(gopoint)
    if type(pos) != tuple:
        return # FIXME: exception might be more appropriate, though annoying.
    options = {'scale': scale}    
    
    GS.addGhostStone.emit(color, pos, options)

def clearGhosts():
    GS.clearAllGhosts.emit()

def clearMarks():
    """
    clear all marks on the board
    """
    GS.clearAllMarks.emit()

def clearHeat():
    GS.clearAllHeat.emit()

def clearAll():
    "clear everything but the stones"
    GS.clearAllMarkup.emit()
    GS.clearAllGhosts.emit()
    clearStatus()

def clearStatus():
    GS.statusBarPrint.emit("")

def heat(gopoint: tuple or str, value: float):
    """
    set the heat value for gopoint [e.g. (3,3)] from 0 to 1
    """
    pos = _getGoPoint(gopoint)

    GS.heatValueChanged.emit(pos, value)

def haveK():
    return k != None

def quickPlay(katainfo, plays: list):
    kata = GlobalKata()
    if kata == None:
        return katainfo
    
    orig = dict(katainfo.answer['originalQuery'])
    orig['moves'] = orig['moves'] + plays
    orig['id'] = "codeAnalysis_" + str(time.time_ns())
    orig['maxVisits'] = 2
    response = kata.analyze(orig)

    return KataAnswer(response)

def opponent(color: str) -> str:
    if color[0].upper() == "W":
        return "black"
    else:
        return "white"

def dist(pos1, pos2) -> int:
    "return the manhattan distance between 2 go points"
    p1 = _getGoPoint(pos1)
    p2 = _getGoPoint(pos2)
    return abs(p1[0]-p2[0]) + abs(p1[1] - p2[1])

def set_clipboard(stuff: str) -> None:
    app = QApplication.instance()
    app.clipboard().setText(str(stuff))

def get_clipboard() -> str:
    app = QApplication.instance()
    return app.clipboard().text()

def log(stuff: str) -> None:
    GS.CodeGUI_LogPrint.emit(str(stuff)+"\n")

def clearLog() -> None:
    GS.CodeGUI_LogClear.emit()

def msgBox(msg: str, buttons:list[str] or None = None) -> str:
    "Display a message box with buttons if desired. returns the name of the button clicked."
    tops = QApplication.instance().topLevelWidgets()
    w = None
    for t in tops:
        if issubclass(t.__class__, QMainWindow):
            w = t
            break

    mb = QtWidgets.QMessageBox(w)

    buttonDict = {}
    for b in buttons:
        buttonObject = mb.addButton(b, QtWidgets.QMessageBox.AcceptRole)
        buttonDict[buttonObject] = b

    mb.setText(msg)
    mb.exec_()

    if mb.clickedButton() in buttonDict:
        return buttonDict[mb.clickedButton()]
    else:
        return "OK"

def _buttonX(id: str, title: str) -> bool:
    GS.CodeGUI_SetTitle.emit(id, title)
    d = {"clicked": False, "title": title, "default_value": False}
    return d

def _checkX(id: str, title: str, default_value: bool = False) -> bool:
    GS.CodeGUI_SetTitle.emit(id, title)
    GS.CodeGUI_SetChecked.emit(id, default_value)
    d = {"checked": default_value, "title": title, "default_value": default_value}
    return d

def _sliderX(id: str, title: str, default_value = 0.0, min_value=0.0, max_value=0.0, value_type='float'):
    GS.CodeGUI_SetTitle.emit(id, title)
    GS.CodeGUI_SetSliderType.emit(id, value_type)
    GS.CodeGUI_SetSliderRange.emit(id, min_value, max_value)
    GS.CodeGUI_SetSliderValue.emit(id, default_value)
    d = {"title": title, "value": default_value, "min_value": min_value, "max_value": max_value, "value_type": value_type, "default_value": default_value}
    return d

extrafuncs = {
    "status": status,
    "mark": mark,
    "ghost": ghost,
    "clearMarks": clearMarks,
    "clearHeat": clearHeat,
    "clearStatus": clearStatus,
    "clearGhosts": clearGhosts,
    "clearAll": clearAll,
    "opponent": opponent,
    "heat": heat,
    "havek": haveK,
    "quickPlay": quickPlay,
    "set_clipboard": set_clipboard,
    "get_clipboard": get_clipboard,
    "log": log,
    "clearLog": clearLog,
    "msgBox": msgBox,
    "_buttonX": _buttonX,
    "_checkX": _checkX,
    "_sliderX": _sliderX,
    "bail": bail,
    "dist": dist,
    "snooze": snooze
}

# the GUI functions have to be compiled
# so as to stay within the script context
GUI_FUNCS_SRC = ""
buttonFuncTemplate = """
def button{n}(title:str="button{n}") -> bool:
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
def check{n}(title:str="check{n}", default_value=False):
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
def slider{n}(title: str="dial{n}", default_value=0.0, min_value=0.0, max_value=1.0, value_type='float'):
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
"""

# build it
for n in range(8):
    GUI_FUNCS_SRC += buttonFuncTemplate.format(n = str(n+1))
    GUI_FUNCS_SRC += checkFuncTemplate.format(n = str(n+1))
    GUI_FUNCS_SRC += sliderFuncTemplate.format(n = str(n+1))


class CodeRunner(QObject):
    "runs custom python code against a position"
    def __init__(self, parent=None):
        super().__init__(parent)
        self.context_global = {}
        self.context_local = {}
        self.code = None

        # this is needed as text to execute in the same global context
        # as the running script, rather than the context of this very file
        __code_preamble = """
def persist(variable: str, val) -> None: 
    __saved__[variable] = True
    if variable not in globals(): globals()[variable] = val
"""     
        #self.preambleC = code.compile_command(__code_preamble, symbol="exec")
        self.preambleC = compile(__code_preamble + GUI_FUNCS_SRC, "<preamble>", 'exec', optimize=2)
    
    def printit(self, thing):
        # placeholder until gui shows stdout
        print(f"{thing}", end='', file=sys.stderr)


    def setCode(self, sourceCode: str):

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


    def run(self, kataResults: dict = None, extraGlobals=None, explicit=False):
        if kataResults != None:
            self.createContexts(kataResults, extraGlobals=extraGlobals, manual_run=explicit)

        #print("EXPLICIT IS ", explicit)
        if self.code != None:
            # TODO: set context's __builtins__ to None and rebuild necessary stuff like print
            try:
                exec(self.preambleC, self.context_global, self.context_local)
                exec(self.code, self.context_global, self.context_local)
            except Bail as e:
                # don't care
                pass
            
            except Exception as e:
                traceback.print_exc()
                tb_info = traceback.extract_tb(e.__traceback__)
                name, line, func, code = tb_info[-1]
                status(f"{type(e).__name__} : {str(e)}, '{name}' line {line}")

    def getSavedVars(self, glob, loc):
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
    
    def getGlobals(self):
        return self.context_global
    
    def createContexts(self, kataResults: dict, extraGlobals: dict = None, kind='full', manual_run=False):
        from goban import Goban

        global k
        #print("CREATE CONTEXTS: explicit: ", manual_run)
        moreglobs = extraGlobals

        if extraGlobals == None: moreglobs = {}

        k = KataAnswer(kataResults)
        g = Goban(k.xsize, k.ysize)
        g.komi = k.komi
        g.toplay = k.toPlay
        if 'initialStones' in k.answer['originalQuery']:
            for color, stone in k.answer['originalQuery']['initialStones']:
                g.place(color, coordsToPoint(stone))
        if 'moves' in k.answer['originalQuery']:
            for color, stone in k.answer['originalQuery']['moves']:
                p = coordsToPoint(stone)
                g.play(color, p)

        setattr(k, "depth", kind)
        setattr(k, "manual_run", manual_run)

        saved_globals, saved_locals = self.getSavedVars(self.context_global, self.context_local)

        self.context_global = {'__saved__': {}}
        self.context_local = {'__saved__': {}}

        self.context_global.update(extrafuncs)
        self.context_global.update(moreglobs)
        self.context_global.update(saved_globals)
        self.context_local.update(saved_locals)

        # k will always override, sry
        self.context_global["k"] = k
        self.context_global['goban'] = g

from pyqode.core.api import CodeEdit, ColorScheme
from pyqode.core import modes, panels
from pyqode.python import modes as pymodes
from pyqode.python.backend import server as pyserver
class CodeEditor(CodeEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.codeRunner = CodeRunner()
        self.lastAnswer = None
        self.textChanged.connect(self.markDirty)
        self._dirty = True
        self.GUI_Saved = {} # saved gui info by the script

        # code completion is pretty basic and annoying
        # so don't use it. 
        
        # self.backend.start(pyserver.__file__)
        # self.modes.append(modes.CodeCompletionMode())
        
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
        
        GS.fullAnalysisReady.connect(self.rerun)
        GS.quickAnalysisReady.connect(self.rerunQuick) #FIXME Code should support quick & in-depth views
        GS.CodeGUI_Changed.connect(self.newGUIInfo)
        GS.MainWindowReadyAndWilling.connect(self.afterStartup)
        
        # FIXME: QSettings is not a great choice for persisting the scripts
        # because the user can't easily access them like they could if they
        # were simply files

        settings = QSettings()

        self.slots = []
        self.currentSlot = None # let main window set me up, as it holds the actions

    def afterStartup(self):
        settings = QSettings()

        self.nameAllSlots()
        self.activateSlot(settings.value("codeeditor/current_slot", 1), force=True)

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

    def slotSelected(self):
        self.saveCurrentSlot()
        self.activateSlot(self.sender().data())
        self.GUI_Saved = {}
        self._dirty = True
        self.runRequested()

    def nameASlot(self, slotnum: int) -> None:
        "auto-generate a name for the slot in the menu"
        #print("NAMING SLOT ", slotnum)
        settings = QSettings()
        text = settings.value(f"codeeditor/slot{slotnum}_src", "")
        if text != "":
            for line in text.splitlines():
                stripped = line.strip()
                if len(stripped) > 0 and stripped[0] == "#":
                    stripped = stripped.strip("#")
                    name = stripped.strip()
                    if len(name) > 30:
                        name = name[:29] + "…"
                    #print(f"SLOT {slotnum} name: '{name}'")
                    GS.Code_SetSlotName.emit(slotnum, name)
                    break

    def nameAllSlots(self) -> None:
        for s in range(1,11):
            self.nameASlot(s)

    def appWillClose(self):
        self.saveCurrentSlot()

    def setGUI(self, tabWidget):
        self.codegui = CodeGUISwitchboard(tabWidget)

    def markDirty(self):
        self._dirty = True

    def runRequested(self):
        print("RUN REQUESTED.")
        if self.lastAnswer != None:
            if self._dirty:
                self.codeRunner.setCode(self.document().toPlainText())
                self._dirty = False
                self.saveCurrentSlot()
            self.codeRunner.run(self.lastAnswer, extraGlobals = {"__GUI__": self.GUI_Saved}, explicit=True)
            self.updateGUIVars()
        else:
            GS.statusBarPrint.emit("No KataGo Analysis to run against.")
    
    def updateGUIVars(self):
        g = self.codeRunner.getGlobals()
        if "__GUI__" in g:
            self.GUI_Saved.update(g['__GUI__'])
    
    def runAfterGUI(self):
        if self.lastAnswer != None:
            if self._dirty:
                self.codeRunner.setCode(self.document().toPlainText())
                self._dirty = False
                self.saveCurrentSlot()
            self.codeRunner.run(self.lastAnswer, extraGlobals = {"__GUI__": self.GUI_Saved}, explicit=False)
            self.updateGUIVars()

        else:
            GS.statusBarPrint.emit("No KataGo Analysis to run against.")

    def rerunQuick(self, signalData: dict):
        return self.rerun(signalData, kind='quick')


    def rerun(self, signalData: dict, kind='full'):
        signalData['payload']['depth'] = kind
        self.lastAnswer = signalData['payload']
        if "error" in self.lastAnswer:
            print(f"KATAGO ERROR: {self.lastAnswer['error']}", file=sys.stderr)
            return
        if self._dirty:
            self.codeRunner.setCode(self.document().toPlainText())
            self._dirty = False
            self.saveCurrentSlot()
        self.codeRunner.createContexts(signalData["payload"], extraGlobals={"__GUI__": self.GUI_Saved}, kind=kind)
        self.codeRunner.run()
        self.updateGUIVars()

    def newGUIInfo(self, info: dict) -> None:
        changed = False
        for thing in self.GUI_Saved.keys():
            if thing in info:
                self.GUI_Saved[thing].update(info[thing])
                changed = True
        if changed:
            self.runAfterGUI()

class CodeEditorBasic(QPlainTextEdit):
    "older version, but kept in case pyqode goes wacky"
    def __init__(self, parent=None):
        super().__init__(parent)
        self.codeRunner = CodeRunner()
        self.lastAnswer = None
        self.textChanged.connect(self.markDirty)
        self._dirty = True
        
        GS.fullAnalysisReady.connect(self.rerun)
        GS.quickAnalysisReady.connect(self.rerunQuick) #FIXME Code should support quick & in-depth views

    def markDirty(self):
        self._dirty = True

    def runRequested(self):
        print("RUN REQUESTED.")
        if self.lastAnswer != None:
            if self._dirty:
                self.codeRunner.setCode(self.document().toPlainText())
                self._dirty = False
            self.codeRunner.run(self.lastAnswer, explicit=True)
        else:
            GS.statusBarPrint.emit("No Kata Analysis to run against.")
    def rerunQuick(self, signalData: dict):
        return self.rerun(signalData, kind='quick')

    def rerun(self, signalData: dict, kind='full'):
        signalData['payload']['depth'] = kind
        self.lastAnswer = signalData['payload']
        if "error" in self.lastAnswer:
            print(f"KATAGO ERROR: {self.lastAnswer['error']}", file=sys.stderr)
            return
        if self._dirty:
            self.codeRunner.setCode(self.document().toPlainText())
            self._dirty = False
        self.codeRunner.createContexts(signalData["payload"], kind)
        self.codeRunner.run()


from PyQt5 import QtWidgets
class CodeGUISwitchboard(QObject):
    # There is a strong separation between output from the code
    # and input from the user. This prevents infinite loops in the GUI,
    # with the caveat that blockSignals() prevents any other code
    # from getting code-initiated update signals when a GUI item is changed from the script
    def __init__(self, guiTab, parent=None):
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
        
    def setATitle(self, name: str, text: str):
        if name in self.lookup:
            o = self.lookup[name]
            if hasattr(o, "setText"):
                o.setText(text)
            else: # maybe for dials this helps
                maybe = "label_" + o.objectName()
                if maybe in self.lookup_labels:
                    self.lookup_labels[maybe].setText(text)
            self.GUI_state[name]['title'] = text

    def setAToolTip(self, name, text):
        if name in self.lookup:
            self.lookup[name].setToolTip(text)

    def setChecked(self, name: str, onOff:bool) -> None:
        if name in self.lookup:
            o = self.lookup[name]
            o.blockSignals(True)
            o.setChecked(onOff)
            o.blockSignals(False)

    def slider2Float(self, val:int, minV, maxV):
        return minV + ((maxV-minV)*val)/100000.0
    
    def float2Slider(self, val:float, minV, maxV):
        return int(100000.0*(val-minV)/(maxV-minV))

    def sliderChangedRaw(self, name, value):
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

    def sliderSetValue(self, name, value):
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

    def sliderSetType(self, name:str, value_type:str):
        if name in self.lookup:
            self.GUI_state[name]['value_type'] = value_type
 
    def buttonClicked(self, name, value=None):
        # only handle one button at a time, much easier
        for b in self.buttonNames:
            self.GUI_state[b]['clicked'] = False
        if name in self.buttonNames:
            self.GUI_state[name]['clicked'] = True
            self.GUI_Changed()

    def checkboxClicked(self, name, value):
        if name in self.checkboxNames:
            self.GUI_state[name]['checked'] = value
            self.GUI_Changed()

    # keep in the code for reference
    @property
    def buttonNames(self):
        return [o.objectName() for o in self.buttons]
    
    @property
    def dialNames(self):
        return [o.objectName() for o in self.sliders]

    @property
    def checkboxNames(self):
        return [o.objectName() for o in self.checkboxes]

   


    def GUI_Changed(self):
        GS.CodeGUI_Changed.emit(self.GUI_state)
