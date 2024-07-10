
from GameSettingsDialog_ui import Ui_GameSettingsDialog
from PyQt5.QtWidgets import  QDialog

class GameSettingsDialog(QDialog, Ui_GameSettingsDialog):
    def __init__(self, parent=None, settings= (19, 19, 6.5)):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Game Settings")
        self.connectSignalsSlots()
        self.xsize, self.ysize, self.komi = settings
        
        if self.xsize != self.ysize:
            self.lockSizeCheckbox.setChecked(True)

        self.xSizeBox.setValue(self.xsize)
        self.ySizeBox.setValue(self.ysize)

        self.komiBox.setValue(self.komi)

    def connectSignalsSlots(self):
        self.lockSizeCheckbox.stateChanged.connect(self.ySizeBox.setEnabled)
        self.lockSizeCheckbox.stateChanged.connect(self.checkChanged)

        #self.xSize.valueChanged.connect(self.ySize.setValue)
        self.xSizeBox.valueChanged.connect(self.setX)
        self.ySizeBox.valueChanged.connect(self.setY)
        self.komiBox.valueChanged.connect(self.setKomi)
        #self.rejected.connect(self.close)
        #self.accepted.connect(self.close)

    def setX(self, val: int): 
        self.xsize = val
        if not self.lockSizeCheckbox.isChecked():
            self.ysize = val
            self.ySizeBox.setValue(val)

    def setY(self, val: int) -> None: 
        self.ysize = val
    
    def setKomi(self, val: float) -> None:
        import math
        newval = math.floor(val*2)/2.0
        
        self.komi = newval        
        
        if newval != val:
            self.komiBox.setValue(newval)

    def checkChanged(self, value: bool ) -> None:
        if not value:
            self.ySizeBox.setValue(self.xsize)

