import sys, math, time

from kataproxy import KataProxyQ, KataSignals, GlobalKata, GlobalKataInit
from goutils import coordsToPoint, pointToCoords, opponent
from goban import Goban
from GlobalSignals import GS
from SgfParser import SgfParser

from BoardController import BoardController

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtGui import QGuiApplication

from PyQt5.QtCore import Qt, QPoint, QObject, QStandardPaths, QSettings, QTimer

from PyQt5.QtWidgets import (

    QApplication, QMainWindow, QMessageBox, QPlainTextEdit, QWidget, QFormLayout,
    QFileDialog,
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

        # panic startup for runaway scripts
        mods = QGuiApplication.queryKeyboardModifiers()
        if mods & Qt.ShiftModifier == Qt.ShiftModifier:
            self.actionDisable_Code.setChecked(True)
        else:
            settings = QSettings()
            dis = settings.value("codeeditor/disabled", False)
            self.actionDisable_Code.setChecked(dis)


    def connectSignalsSlots(self) -> None:
        self.actionQuit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.about)
        self.actionRun.triggered.connect(self.codeEdit.runRequested)
        self.actionDisable_Code.toggled.connect(self.codeEdit.handleDisableCode)

        self.actionFlip_Player.triggered.connect(self.board.handleFlipPlayer)
        self.actionAnalyze_More.triggered.connect(self.board.handleAnalyzeMore)
        self.actionClearBoard.triggered.connect(self.board.handleClearBoard)
        self.actionToggleDraw.triggered.connect(self.board.handleToggleDraw)
        GS.statusBarPrint.connect(self.statusbar.showMessage)
        self.actionAbout_2.triggered.connect(self.about)

        self.actionGame_Settings.triggered.connect(self.board.doGameSettings)        
        self.actionNeural_Nets.triggered.connect(self.doNeuralNetSettings)

        self.actionBookmark.triggered.connect(self.board.handleBookmark)
        self.actionClear_All_Bookmarks.triggered.connect(self.board.clearAllBookmarks)
        self.actionClear_Current_Bookmark.triggered.connect(self.board.clearBookmark)
        
        self.actionClear_Cache.triggered.connect(self.board.clearKataGoCache)
        
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
            titleset = lambda v, s, o=a: o.setText(f"{v} {s}") if o.data() == v else None
            selectset = lambda v, o=a: o.setChecked(True) if o.data() == v else None
            GS.Code_SetSlotName.connect(titleset)
            GS.Code_SlotActivated.connect(selectset)

        self.actionImport_SGF.triggered.connect(self.doImportSGF)

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

        ui.B15_QuickVisits.setValue(settings.value("nn/B15/quick_visits", 2))
        ui.B15_FullVisits.setValue(settings.value("nn/B15/full_visits", 100))
        ui.B15_StepVisits.setValue(settings.value("nn/B15/step_visits", 500))

        ui.NBT_QuickVisits.setValue(settings.value(f"nn/NBT/quick_visits", 2))
        ui.NBT_FullVisits.setValue(settings.value(f"nn/NBT/full_visits", 50))
        ui.NBT_StepVisits.setValue(settings.value(f"nn/NBT/step_visits", 100))

        ui.pure.setChecked(settings.value(f"nn/pure", False))

        if network == "B15":
            ui.groupBox_B15.setChecked(True)
            ui.groupBox_NBT.setChecked(False)
        else:
            ui.groupBox_B15.setChecked(False)
            ui.groupBox_NBT.setChecked(True)

        ui.groupBox_NBT.clicked.connect(clickedNBT)
        ui.groupBox_B15.clicked.connect(clickedB15)
        

        accepted = dlg.exec_() != 0
        d = {}
        if accepted:
            if ui.groupBox_B15.isChecked():
                net = "B15"
                settings.setValue("nn/active_network", "B15")
                d['quick_visits'] = ui.B15_QuickVisits.value()
                d['full_visits'] = ui.B15_FullVisits.value()
                d['step_visits'] = ui.B15_StepVisits.value()
            else:
                net = "NBT"
                settings.setValue("nn/active_network", "NBT")
                d['quick_visits'] = ui.NBT_QuickVisits.value()
                d['full_visits'] = ui.NBT_FullVisits.value()
                d['step_visits'] = ui.NBT_StepVisits.value()


            for key, val in d.items():
                settings.setValue(f"nn/{net}/{key}", val)

            d['network'] = net
            d['pure'] = ui.pure.isChecked()
            settings.setValue(f"nn/pure", d['pure'])

            GS.SetNeuralNetSettings.emit(d)


    def doImportSGF(self):
        "import an SGF file and emit a signal for it"
        def whoops(exception):
            "generic parsing error presented to user"
            QMessageBox.critical(self, 
                        "Couldn't Parse SGF", 
                        f"Sorry, I couldn't parse the sgf file '{fileName}':\n\n{exception}")

        mb = QtWidgets.QMessageBox(self)
        mb.setText("This will replace all positions and bookmarks.")
        mb.setInformativeText("Do you want to continue?")
        mb.setIcon(QMessageBox.Warning)
        mb.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        b = mb.exec_()


        if b == QMessageBox.Ok:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","SGF Files (*.sgf)", options=options)
            if fileName:
                try:
                    sgf = SgfParser.fromFile(fileName)
                except Exception as e:
                    whoops(e) ; return

                try:
                    gobans = sgf.root.toGobanList()
                except Exception as e:
                    whoops(e) ; return

                if len(gobans) == 0:
                    whoops("no positions found.") ; return

                komi, size = (gobans[0].komi, (gobans[0].xsize, gobans[0].ysize,))

                for g in gobans:
                    if g.komi != komi:
                        whoops("Inconsistent Komi") ; return
                    if (g.xsize, g.ysize) != size:
                        whoops("Inconsistent board sizes") ; return

                d = {
                "xsize": gobans[0].xsize, 
                "ysize": gobans[0].ysize, 
                "komi": gobans[0].komi, 
                "gobans": gobans
                }

                GS.loadBoard.emit(d)

    def showEvent(self, whatever):
        if not self.firstShow:return
        self.firstShow = False
        
        # try to keep the splitter tight around the goban
        splitHeight = self.splitter.size().height()
        settings = QSettings()

        # first widget is goban, make it square
        extra_space = 10 # meh, have to guess the splitter pixels
        sizes = [splitHeight+extra_space, self.splitter.size().width()-splitHeight-extra_space]
        self.splitter.setSizes(sizes)

        sing = lambda : GS.MainWindowReadyAndWilling.emit()
        QTimer.singleShot(10, sing)

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
        GS.MainWindowReadyAndWilling.connect(self.afterStartup)

    def addMore(self, stuff: str):
        self.consoleTextEdit.moveCursor(QtGui.QTextCursor.End)
        self.consoleTextEdit.insertPlainText(stuff)
        self.consoleTextEdit.moveCursor(QtGui.QTextCursor.End)
    
    def afterStartup(self):
        #self.show()
        pass

class DupeStd(QObject):
    "a pseudo file object that duplicates std outputs to signal emission"
    def __init__(self, which):
        super().__init__()
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
    
    from project_globals import *
    global app_directory
    global resource_directory
    
    app_directory = os.path.abspath(os.path.dirname(__file__))
    resource_directory = os.path.join(app_directory, "resources")

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
        
        #print(f"DATA LOCATION: {QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)}")

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
