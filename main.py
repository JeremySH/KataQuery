import sys, math, time

from kataproxy import KataProxyQ, KataSignals, GlobalKata, GlobalKataInit
from goutils import coordsToPoint, pointToCoords, opponent
from goban import Goban
from GlobalSignals import GS

from BoardController import BoardController

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt, QPoint, QObject, QStandardPaths

from PyQt5.QtWidgets import (

    QApplication, QMainWindow, QMessageBox, QPlainTextEdit, QWidget, QFormLayout,
    QGraphicsScene, QGraphicsItemGroup, QGraphicsEllipseItem, QGraphicsRectItem, 
    QGraphicsSimpleTextItem, QGraphicsLineItem,
    QGraphicsView, QActionGroup, QAction

)

from mainwindow_ui import Ui_MainWindow

class Window(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("KataQuery")
        self.board = BoardController(self.graphicsView)
        self.codeEdit.setGUI(self.tabWidget.widget(1))
        self.firstShow = True
        self.connectSignalsSlots()

    def connectSignalsSlots(self) -> None:
        self.actionQuit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.about)
        self.actionRun.triggered.connect(self.codeEdit.runRequested)
        self.actionFlip_Player.triggered.connect(self.board.handleFlipPlayer)
        self.actionAnalyze_More.triggered.connect(self.board.handleAnalyzeMore)
        self.actionClearBoard.triggered.connect(self.board.handleClearBoard)
        self.actionToggleDraw.triggered.connect(self.board.handleToggleDraw)
        GS.statusBarPrint.connect(self.statusbar.showMessage)
        self.actionAbout_2.triggered.connect(self.about)

        self.actionGame_Settings.triggered.connect(self.board.doGameSettings)        
        self.actionNeural_Nets.triggered.connect(self.doNeuralNetSettings)

        # have to build the submenu, meh

        localizeGroup = QActionGroup(self.menuLocalize)
        for i in range(5):
            a = QAction(self)
            a.setData(i)
            a.setCheckable(True)
            a.setObjectName("actionLocalize")
            if i == 0: a.setChecked(True)
            if i == 0:
                a.setText(f"None")
            else:
                if i == 1: 
                    sText = "point"
                else: 
                    sText = "points"
                a.setText(f"{i} {sText} away")

            a.triggered.connect(self._BounceMenu)
            localizeGroup.addAction(a)
            self.menuLocalize.addAction(a)


        codeSlotGroup = QActionGroup(self.menuCodeSlot)
        for i in range(10):
            a = QAction(self)
            a.setData(i+1)
            a.setCheckable(True)
            a.setObjectName("actionLocalize")
            a.setText(f"{i+1}")
            if i == 0: a.setChecked(True)
            codeSlotGroup.addAction(a)
            self.menuCodeSlot.addAction(a)

            a.triggered.connect(self.codeEdit.slotSelected)
            if i == 9:
                a.setShortcut(QtGui.QKeySequence(f"Ctrl+0"))
            else:
                a.setShortcut(QtGui.QKeySequence(f"Ctrl+{i+1}"))

    def _BounceMenu(self):
        self.board.setRestrictDist(self.sender().data())

    def closeEvent(self, event):
        self.codeEdit.appWillClose()

    def about(self):
        QMessageBox.about(
            self,
            "About KataQuery",
            "<p>KataQuery is a way to explore go.</p>"
            "<p>Implemented using Katago and PyQt5</p>",

        )
    
    def doNeuralNetSettings(self):
        from NeuralNetSettingsDialog_ui import Ui_Dialog as nnDialogUI
        settings = QtCore.QSettings()

        dlg = QtWidgets.QDialog()
        ui = nnDialogUI()
        ui.setupUi(dlg)
        #print(dir(ui))
        #print(dir(dlg))
        clickedB15 = lambda v, o=ui.groupBox_NBT: o.setChecked(not v)
        clickedNBT = lambda v, o=ui.groupBox_B15: o.setChecked(not v)
        
        network = settings.value("nn/active_network", "B15")
        if network == "B15":
            ui.groupBox_B15.setChecked(True)
            ui.groupBox_NBT.setChecked(False)
            ui.B15_QuickVisits.setValue(settings.value("nn/B15/quick_visits", 2))
            ui.B15_FullVisits.setValue(settings.value("nn/B15/full_visits", 100))
            ui.B15_StepVisits.setValue(settings.value("nn/B15/step_visits", 500))
        else:
            ui.groupBox_B15.setChecked(False)
            ui.groupBox_NBT.setChecked(True)
            ui.NBT_QuickVisits.setValue(settings.value(f"nn/NBT/quick_visits", 2))
            ui.NBT_FullVisits.setValue(settings.value(f"nn/NBT/full_visits", 50))
            ui.NBT_StepVisits.setValue(settings.value(f"nn/NBT/step_visits", 100))

        ui.groupBox_NBT.clicked.connect(clickedNBT)
        ui.groupBox_B15.clicked.connect(clickedB15)
        

        accepted = dlg.exec_() != 0
        d = {}
        if accepted:
            if ui.groupBox_B15.isChecked():
                settings.setValue("nn/active_network", "B15")
                d['network'] = "B15"
                d['quick_visits'] = ui.B15_QuickVisits.value()
                d['full_visits'] = ui.B15_FullVisits.value()
                d['step_visits'] = ui.B15_StepVisits.value()
            else:
                settings.setValue("nn/active_network", "NBT")
                d['network'] = "NBT"
                d['quick_visits'] = ui.NBT_QuickVisits.value()
                d['full_visits'] = ui.NBT_FullVisits.value()
                d['step_visits'] = ui.NBT_StepVisits.value()


            for key, val in d.items():
                settings.setValue(f"nn/{d['network']}/{key}", val)

            GS.SetNeuralNetSettings.emit(d)


    def showEvent(self, whatever):
        if not self.firstShow:return
        self.firstShow = False
        
        # try to keep the splitter tight around the goban
        #sizes = self.splitter.sizes() # BROKEN, always gives 0's, prob because they're not shown yet?
        splitHeight = self.splitter.size().height()

        # first widget is goban, make it square
        extra_space = 10 # meh, have to guess the splitter pixels
        sizes = [splitHeight+extra_space, self.splitter.size().width()-splitHeight-extra_space]
        #sizes = [2, 1]
        print("SIZES: ", sizes, splitHeight)
        self.splitter.setSizes(sizes)
        #self.splitter.setStretchFactor(200,1)
        #self.actionLocalize.triggered.connect(self.bounceMenu)
        self.board.boardChanged() # trigger analysis on empty board

        pass # self.resizeGraphics(whatever)



class ConsoleWindow(QWidget):
    def __init__(self, parent=None):
        from PyQt5.QtGui import QFont, QFontMetrics
        super().__init__(parent)
        self.setObjectName("ConsoleWindow")
        self.setWindowTitle("Console Output")
        self.setObjectName("ConsoleWindow")

        conFont = QFont("Menlo", 12, QFont.Monospace)
        conFont.insertSubstitutions("Menlo", ["Monaco", "Consolas", "Liberation Mono", "Monospace"])
        
        m = QFontMetrics(conFont).boundingRect("M")

        self.resize(132*m.width(), 25*m.height()) # total guess

        layout = QFormLayout()
        self.setLayout(layout)

        self.consoleTextEdit = QPlainTextEdit(self)
        self.consoleTextEdit.setReadOnly(True)
        self.consoleTextEdit.setMaximumBlockCount(1000)
        self.consoleTextEdit.setFont(conFont)
        
        self.clearButton = QtWidgets.QPushButton(self)
        self.clearButton.setText("Clear")
        self.clearButton.clicked.connect(self.consoleTextEdit.clear)

        layout.addRow(self.consoleTextEdit)
        layout.addRow(self.clearButton)

        QtCore.QMetaObject.connectSlotsByName(self)
        GS.stderrPrinted.connect(self.addMore)
        GS.stdoutPrinted.connect(self.addMore)

    def addMore(self, stuff: str):
        self.consoleTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.consoleTextEdit.insertPlainText(stuff)
        self.consoleTextEdit.moveCursor(QtGui.QTextCursor.End)

class DupeStd(QObject):
    "a pseudo file object that duplicates std outputs to signal emission"
    def __init__(self, which):
        if which == 'stdout':
            self.orig = sys.stdout
            self.sig = GS.stdoutPrinted
        else:
            self.orig = sys.stderr
            self.sig = GS.stderrPrinted
    def write(self, stuff: str):
        self.sig.emit(stuff)
        self.orig.write(stuff)
    
    def flush(self):
        self.orig.flush()

if __name__ == "__main__":
    REDIRECT_OUTPUT = True 
    from contextlib import redirect_stderr, redirect_stdout

    def main():
        app = QApplication(sys.argv)

        console = ConsoleWindow()
        console.hide()
        
        app.setApplicationName("KataQuery")
        app.setOrganizationName("KataQuery.org")
        
        win = Window()
        win.actionShow_Console.triggered.connect(console.show)
        win.actionShow_Console.triggered.connect(console.raise_)
        #KataSignals.stderrPrinted.connect(GS.stderrPrinted)
        win.show()
        
        print(f"DATA LOCATION: {QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)}")

        return app.exec_()



    if REDIRECT_OUTPUT:
        # helps with displaying weird qt exceptions that silently abort
        import traceback
        sys.excepthook = traceback.print_exception
        
        # "with" screws up exceptions for some reason
        with redirect_stdout(DupeStd('stdout')):
            with redirect_stderr(DupeStd('stderr')):
                sys.exit(main())
    else:
        sys.exit(main())
