from PyQt5.QtCore import pyqtSignal, QObject

# Global Signals send out dicts for enough information to do something.
# the dict looks like {"t": timeStamp, "payload": whatever}
# for analysis functions, timestamp is the time the analysis was requested,
# NOT when it completed. This is so slots can ignore out-of-order analyses,
# and simply render/recalculate the latest one.
class _GS(QObject):
    currentBoardChanged = pyqtSignal(dict)
    boardSizeChanged = pyqtSignal(tuple)
    komiChanged = pyqtSignal(float)
    toPlayChanged = pyqtSignal(str)

    fullAnalysisReady = pyqtSignal(dict)
    quickAnalysisReady = pyqtSignal(dict)

    statusBarPrint = pyqtSignal(str)    
    addMark = pyqtSignal(tuple, str, dict)
    clearMark = pyqtSignal(tuple)
    clearAllMarks = pyqtSignal()
    clearAllHeat = pyqtSignal()

    clearAllMarkup = pyqtSignal()
    
    heatValueChanged = pyqtSignal(tuple, float)

    addGhostStone = pyqtSignal(str, tuple, dict) # color, gopoint, options
    clearGhostStone = pyqtSignal(tuple) # gopoint
    clearAllGhosts = pyqtSignal()

    stdoutPrinted = pyqtSignal(str)
    stderrPrinted = pyqtSignal(str)

    Code_SetSlotName = pyqtSignal(int, str) # int, text
    Code_SlotActivated = pyqtSignal(int)

    # code gui buttons and stuff
    # setters from the code runner:
    CodeGUI_LogPrint = pyqtSignal(str) # text
    CodeGUI_LogClear = pyqtSignal() 
    CodeGUI_SetTitle = pyqtSignal(str, str) # objectName of element, title
    CodeGUI_SetToolTip = pyqtSignal(str, str) # objectName, tooltip text
    CodeGUI_SetChecked = pyqtSignal(str, bool) # objectName, whether it's to be checked
    #CodeGUI_SetValueInt = pyqtSignal(str, int) # objectName, int value
    CodeGUI_SetSliderValue = pyqtSignal(str, float) # objectName, float value
    CodeGUI_SetSliderType = pyqtSignal(str, str) # objectName, "int" or "float"
    CodeGUI_SetSliderRange = pyqtSignal(str, float, float)
    CodeGUI_MessageBox = pyqtSignal(str)
    
    # triggers from the GUI
    CodeGUI_CheckboxChanged = pyqtSignal(str, bool) # objectName, value 
    CodeGUI_SliderChanged = pyqtSignal(str, float) # objectName, value
    CodeGUI_SliderChangedRaw = pyqtSignal(str, int) # objectName, value
    CodeGUI_ButtonClicked = pyqtSignal(str, bool) # objectName, value (always true)

    # general trigger when GUI is changed, it's time for the code editor
    # to rerun the script
    CodeGUI_Changed = pyqtSignal(dict) # gui state dict

    SetNeuralNetSettings = pyqtSignal(dict) # state with network settings

    MainWindowReadyAndWilling = pyqtSignal() # emitted when main window is fully shown, approx 1 event loop after startup

    def __init__(self):
        super().__init__()
    
GS = _GS()