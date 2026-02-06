
from PyQt5.QtWidgets import QTextEdit, QPlainTextEdit,  QApplication, QMainWindow, QWidget
from PyQt5.QtGui import QImage

from PyQt5.QtCore import QObject, pyqtSignal, QSettings
import PyQt5.QtCore as QtCore
from PyQt5 import QtGui # for the clipboard
import sys

from GlobalSignals import GS
import sys
import traceback
import time

from goutils import to_gopoint
from kataproxy import KataAnswer, GlobalKata, KataGoQueryError, goban2query
from io import StringIO

import json

# localize the line number to the code editor during error reports.
# Actually it's only useful the day that kataquery internal code never throws, heh
_LOCALIZE_LINE_NUMBER = False

# built in functions for the code editor to use
# these act like they're imported via `from kq import *`
import kq
sys.modules['kq'] = kq

# By default, imports are cached by python.
# But we have to reload any module the user imports.
# Otherwise, she cannot change her module code and expect changes

# FIXME: these should be explicit

# preserved the cached imports
_DEFAULT_IMPORTS = [name for name in sys.modules]

# the GUI functions have to be compiled
# so as to stay within the script context,
# as they access a script-only global __GUI__

# note that they use kq.py functions
GUI_FUNCS_SRC = ""
buttonFuncTemplate = """
def button{n}(title: str="button{n}") -> bool:
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
def check{n}(title: str="check{n}", default_value: bool=False) -> bool:
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
def slider{n}(title: str="dial{n}", default_value: float=0.0, min_value: float=0.0, max_value: float=1.0, value_type: str='float') -> float:
    "connect to GUI slider {n} and return default value on first run, and its value otherwise."
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
        self.lock = False

        # this is needed as text to execute in the same global context
        # as the running script, rather than the context of this very file
        __code_preamble = """
def persist(variable: str, val) -> None: 
    __saved__[variable] = True
    if variable not in globals(): globals()[variable] = val
"""     
        #self.preambleC = code.compile_command(__code_preamble, symbol="exec")
        self.preambleC = compile(__code_preamble + GUI_FUNCS_SRC, "<preamble>", 'exec', optimize=1)

    def setCode(self, sourceCode: str) -> None:
        "compile the code, print exception on status line when error"

        try:
            #c = code.compile_command(sourceCode, filename="<code editor>", symbol="exec")
            c = compile(sourceCode, "<code editor>", 'exec')

            if (c):
                self.code = c
            else:
                self.code = None

        except Exception as e:
            traceback.print_exc()
            kq.status(type(e).__name__ + ": " + str(e))
            self.code = None

    def _clearImports(self):
        "total hack so that user can update her module code"
        mods = [name for name in sys.modules]
        for name in mods:
            if name not in _DEFAULT_IMPORTS:
                pass
                # FIXME: not until segfaults are debugged
                #del sys.modules[name]

    def run(self, kataResults: dict=None, extraGlobals: dict=None, explicit: bool=False, 
            gui_run: bool=False, query_points: list[tuple[int, int]]=None) -> None:
        "run the script"
        # FIXME: QtCore.Qt.QueuedConnection should have fixed
        # the issue of analisysFinished signals being handled while the
        # code is still running (and thus triggering another code run while running)
        
        # however, let's keep track of sync problems anyway,
        # even though this is cosmetic
        if self.lock:
            print("SYNC ERROR: RUN LOCKED", file=sys.stderr)

        self.lock = True
        if kataResults != None:
            self.createContexts(kataResults, extraGlobals=extraGlobals, manual_run=explicit, gui_run=gui_run, query_points=query_points)

        #print("EXPLICIT IS ", explicit)
        if self.code != None:
            # TODO: set context's __builtins__ to None and rebuild necessary stuff like print
            try:
                exec(self.preambleC, self.context_global, self.context_global)
                GS.CodeGUI_HideAll.emit()
                self._clearImports()
                exec(self.code, self.context_global, self.context_global)
            except kq.Bail as e:
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


                kq.status(f"{type(e).__name__} : {str(e)}, '{name}' line {line}")
            finally:
                self.lock = False
        
        self.lock = False

    def getSavedVars(self, glob: dict, loc: dict) -> tuple[dict, dict]:
        "return script persistent variables as (global, local)"
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
        "get the script's global context"
        return self.context_global
    
    def createContexts(self, kataResults: dict, extraGlobals: dict=None, manual_run: bool=False, 
                       gui_run: bool=False, query_points: list[tuple[int, int]]=None) -> None:
        "create local and global variables/functions provided to the script"
        global k
        #print("CREATE CONTEXTS: explicit: ", manual_run)
        moreglobs = extraGlobals

        if extraGlobals == None: moreglobs = {}

        k = KataAnswer(kataResults)

        k._depth = kataResults['depth']
        k._manual_run = manual_run
        k._gui_run = gui_run

        if query_points:
            qp = [k.get_point(q) for q in query_points]

            k._query_points = qp

        saved_globals, saved_locals = self.getSavedVars(self.context_global, self.context_global)

        self.context_global = {'__saved__': {}}
        
        self.context_global.update(kq.__dict__) # like 'from kq import *'
        self.context_global.update(moreglobs)
        self.context_global.update(saved_globals)
        self.context_global['__name__'] = "__kq_script__"
        # k will always override, sry
        self.context_global["k"] = k

from pyqode.core.api import CodeEdit, ColorScheme
from pyqode.core import modes, panels, api
from pyqode.python import modes as pymodes
import os
import project_globals

class CodeEditor(CodeEdit):
    "Edit those KataQuery scripts"
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.codeRunner = CodeRunner()
        self.lastAnswer = None
        self.textChanged.connect(self.markDirty)
        self._dirty = True # FIXME, there's a diff between "needs to rerun" and "text changed", but i use this for both
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
        
        # patch another bug (bad extra indent on blank line insertion)
        def _get_indent(self, cursor):
            from pyqode.core.api import TextHelper
            if cursor.atBlockStart(): # <--- this is the fix
                return "", ""
            indent = TextHelper(self.editor).line_indent() * self._indent_char
            return "", indent

        modes.AutoIndentMode._get_indent = _get_indent
    
        m = pymodes.PyAutoIndentMode()
        m._handle_indent_in_statement = _handle_indent_in_statement

        self.modes.append(m) # indent when inside a scope

        self.use_spaces_instead_of_tabs = False
        self.font_size = 12

        self.setTabStopDistance(QtGui.QFontMetricsF(self.font()).horizontalAdvance(' ') * 2)
        
        GS.fullAnalysisReady.connect(self.handleFullAnalysis, QtCore.Qt.QueuedConnection)
        GS.quickAnalysisReady.connect(self.handleQuickAnalysis, QtCore.Qt.QueuedConnection) 
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
        "Called after the main GUI is ready. Restore saved slots, prefs, etc."
        settings = QSettings()
        self.disabled = settings.value("codeeditor/disabled", False, type=bool)
        
        self.nameAllSlots()
        self.loadSlot(settings.value("codeeditor/current_slot", 1, type=int))
        
    def saveCurrentSlot(self) -> None:
        "save the active slot along with the current gui state"
        #print("SAVE SLOT:", self.currentSlot)
        
        if self.currentSlot == None:
            return

        settings = QSettings()
        key = f"codeeditor/slot{self.currentSlot}_src"
        settings.setValue(key, self.document().toPlainText())
        
        key = f"codeeditor/slot{self.currentSlot}_guistate"
        value = self.codegui.asJSON()
        settings.setValue(key, value)
        #print("GUISTATE", self.currentSlot, value)
        
        key = f"codeeditor/slot{self.currentSlot}_guisaved"
        value =  json.dumps(self.GUI_Saved)
        settings.setValue(key,value)
        #print("GUI SAVED", self.currentSlot, value)

        key = f"codeeditor/slot{self.currentSlot}_cursorpos"
        settings.setValue(key, self.textCursor().position())
        
        # FIXME: persisted variables should save
        
        self.nameASlot(self.currentSlot)

    def loadSlot(self, slotNum: int) -> None:
        "load a slot and restore its saved gui (if any)"
        #print("LOAD SLOT", slotNum)
        
        settings = QSettings()
        key = f"codeeditor/slot{slotNum}_src"
        text = settings.value(key, "")
        self.document().setPlainText(text)
        
        key = f"codeeditor/slot{slotNum}_cursorpos"
        pos = settings.value(key, 0, type=int)
        
        key = f"codeeditor/slot{slotNum}_guistate"
        gstate = settings.value(key, "")
        #print("GSTATE", gstate)
        
        key = f"codeeditor/slot{slotNum}_guisaved"
        gsaved = settings.value(key, "")
        #print("GUI JSON", slotNum, gsaved)
        
        if gsaved != "":
            self.GUI_Saved = json.loads(gsaved)
        else:
            self.GUI_Saved = {}

        # restore GUI
        if gstate != "":
            self.codegui.restoreState(gstate)
            self.loadGUIInfo(self.codegui.GUI_state)
        
        #print("RESTORE GUI SAVED", slotNum, self.GUI_Saved)
        #print("RESTORE GUI STATE", slotNum, self.codegui.GUI_state)
        
        for key, v in self.GUI_Saved.items():
            if v['kind'] == 'button':
                v['clicked'] = False

        #restore cursor
        c = self.textCursor()
        c.setPosition(pos)
        self.setTextCursor(c)
        
        self.currentSlot = slotNum
        settings.setValue("codeeditor/current_slot", self.currentSlot)
        self.nameAllSlots()
        
        self._dirty = True
        
        GS.Code_SlotActivated.emit(slotNum)

    def slotSelected(self) -> None:
        "Slot was selected by the user, load it, or toggle if number double-pressed"
        slotNum = self.sender().data()

        # user can alternate between scripts by repeating the slot number
        if slotNum == self.currentSlot:
            if self.previousSlot and self.previousSlot != slotNum:
                self.saveCurrentSlot()
                p = self.currentSlot
                self.loadSlot(self.previousSlot)
                self.previousSlot = p
            else:
                return
        else: # switch slot
            self.saveCurrentSlot()
            self.previousSlot = self.currentSlot
            self.loadSlot(slotNum)

        #self.GUI_Saved = {}
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

    def runit(self, explicit: bool=False, gui_run: bool=False, 
              query_points: list[tuple[int, int]]=None) -> None:
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
            if explicit: # we need to save code-changed GUI info if any
                self.saveCurrentSlot()
        else:
            GS.statusBarPrint.emit("No KataGo Analysis to run against.")

    def runRequested(self) -> None:
        "User has explicitly run the script via menu or shortcut."
        print("RUN REQUESTED.")
        self.runit(explicit = True)
    
    def handleDisableCode(self, value: bool) -> None:
        "Disable/Enable automatic running of the code"
        self.disabled = value
        settings = QSettings()
        settings.setValue("codeeditor/disabled", value)
        
        if not self.disabled:
            self.runit()
        else:
            clearAll()

    def updateGUIVars(self) -> None:
        "update the GUI variables possibly set by the script"
        g = self.codeRunner.getGlobals()
        if "__GUI__" in g:
            self.GUI_Saved.update(g['__GUI__'])

    def handleQuickAnalysis(self, signalData: dict) -> None:
        "Handle an incoming quick analysis from KataProxy"
        self.handleAnalysis(signalData, kind='quick')

    def handleFullAnalysis(self, signalData: dict) -> None:
        "Handle an incoming full analysis from KataProxy"
        self.handleAnalysis(signalData, kind="full")

    def handleAnalysis(self, signalData: dict, kind: str='full') -> None:
        "Handle an analysis from KataProxy. kind can be 'quick' or 'full'."
        signalData['payload']['depth'] = kind
        self.lastAnswer = signalData['payload']
        if not self.disabled:
            self.runit()

    def handleQueryPoint(self, qpoints: list[tuple[int, int]]) -> None:
        "User clicked a query point(s), set them and run script"
        self.queryPoints = qpoints
        self.runit(gui_run=True, query_points=self.queryPoints) # FIXME: not sure if appropriate
        self.queryPoints = None

    def loadGUIInfo(self, info: dict) -> bool:
        "load GUI info into GUI_Saved, return if something changed"
        changed = False
        for thing in self.GUI_Saved.keys():
            if thing in info:
                self.GUI_Saved[thing].update(info[thing])
                changed = True
        return changed
        
    def newGUIInfo(self, info: dict) -> None:
        "Something changed in the GUI dials/etc. Handle that."
        if self.loadGUIInfo(info) and not self.disabled:
            self.runit(explicit=False, gui_run=True)

from PyQt5 import QtWidgets
class CodeGUISwitchboard(QObject):
    "a controller for the GUI dials/etc."
    # There is a strong separation between output from the code
    # and input from the user. This prevents infinite loops in the GUI,
    # with the caveat that blockSignals() prevents any other code
    # from getting code-initiated update signals when a GUI item is changed from the script
    def __init__(self, guiTab: QtWidgets.QTabWidget, parent=None) -> None:
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
        self.checkboxes = checkboxes
        self.buttons = buttons
        self.sliders = sliders

    def log(self, stuff:str) -> None:
        "respond to a signal to print to the log"
        self.logOutput.moveCursor(QtGui.QTextCursor.End)
        self.logOutput.insertPlainText(stuff)
        self.logOutput.moveCursor(QtGui.QTextCursor.End)
        
    def setATitle(self, name: str, text: str) -> None:
        "respond to a signal changing the title of a gui item"
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
        "respond to a signal changing the tooltip for a gui item"
        if name in self.lookup:
            self.lookup[name].setToolTip(text)

    def setChecked(self, name: str, onOff: bool) -> None:
        "set a checkbox by `name` (e.g. 'check1')"
        if name in self.lookup:
            o = self.lookup[name]
            o.blockSignals(True)
            o.setChecked(onOff)
            o.blockSignals(False)
            self.GUI_state[name]['checked'] = onOff

    def slider2Float(self, val: int, minV: float, maxV: float) -> float:
        "convert dial integer data to a float"
        # 1000000 is what the dials are internally set at
        return minV + ((maxV-minV)*val)/100000.0
    
    def float2Slider(self, val: float, minV: float , maxV: float) -> int:
        "convert a float input to dial-compatible integer"
        return int(100000.0*(val-minV)/(maxV-minV))

    def sliderChangedRaw(self, name: str, value: int ) -> None:
        "The dial changed, handle converting the integer value provided"
        if name in self.lookup:
            #print("Slider CHANGED: ", self.GUI_state[name])
            s = self.GUI_state[name]
            val = self.slider2Float(value, s['min_value'], s['max_value'])
            self.GUI_state[name]['value'] = val
            #GS.CodeGUI_SliderChanged.emit(name, val)
            self.GUI_Changed()
        else:
            print("DUNNO: ", name)

    def sliderSetValue(self, name: str, value: float) -> None:
        "set the dial value, respecting its range settings"
        if name in self.lookup:
            state = self.GUI_state[name]
            o = self.lookup[name]
            o.blockSignals(True)
            o.setValue(self.float2Slider(value, state['min_value'], state['max_value']))
            o.blockSignals(False)
            self.GUI_state[name]['value'] = value

    def sliderSetRange(self, name: str, min_val: float, max_val: float) -> None:
        "set the minimum and maximum for the dial"
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

    def sliderSetType(self, name: str, value_type: str) -> None:
        "Set the type of slider, either 'int' or 'float' "
        if name in self.lookup:
            self.GUI_state[name]['value_type'] = value_type
 
    def buttonClicked(self, name: str, value: bool=None) -> None:
        "a button was clicked, set it to true, rerun script"
        # only handle one button at a time, much easier
        for b in self.buttonNames:
            self.GUI_state[b]['clicked'] = False
        if name in self.buttonNames:
            self.GUI_state[name]['clicked'] = True
            self.GUI_Changed(clear_buttons=False)

    def checkboxClicked(self, name: str, value: bool) -> None:
        "checkbox clicked, set it, rerun script"
        if name in self.checkboxNames:
            self.GUI_state[name]['checked'] = value
            self.GUI_Changed()

    def showMe(self, name: str) -> None:
        "enable element `name` (e.g. 'check1')"
        if name in self.lookup:
            self.lookup[name].setEnabled(True)
            self.lookup[name].show()
        
        n = "label_"+name
        if n in self.lookup_labels:
            self.lookup_labels[n].setEnabled(True)
            self.lookup_labels[n].show()


    def hideAll(self) -> None:
        "disable all gui elements, for further showMe()s to enable"
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

    def asJSON(self) -> str:
        "return my state as a json string"
        return json.dumps(self.GUI_state)
    
    def restoreState(self, json_text: str) -> None:
        "restore the GUI state from a json string"
        state = json.loads(json_text)
        
        # update dials, etc
        for d in self.dialNames:
            if d in state:
                self.setATitle(d, state[d]['title'])
                self.sliderSetType(d, state[d]['value_type'])
                self.sliderSetRange(d, state[d]['min_value'], state[d]['max_value'])
                self.sliderSetValue(d, state[d]['value'])
                self.GUI_state[d].update(state[d])
        
        for c in self.checkboxNames:
            if c in state:
                self.setATitle(c, state[c]['title'])
                self.setChecked(c, state[c]['checked'])
                self.GUI_state[c].update(state[c])
        
        # buttons always false unless clicked
        for b in self.buttonNames:
            if b in state:
                self.setATitle(b, state[b]['title'])
                self.GUI_state[b]['title'] = state[b]['title']
                self.GUI_state[b]['clicked'] = False

    def GUI_Changed(self, clear_buttons: bool=True) -> None:
        """
        The GUI changed in some way, send the signal. By default, buttons
        are set to false unless told not to  (via button click handler) 
        This guarantees that when a button == True, it's just
        been clicked (and not "held down")
        """
        # by default clear the buttons to False
        # as I only want buttons true after a click
        if clear_buttons:
            for b in self.buttonNames:
                self.GUI_state[b]['clicked'] = False

        GS.CodeGUI_Changed.emit(self.GUI_state)
