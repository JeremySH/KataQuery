
"""
Manages a QGraphicsView to draw the board & markup
Tracks mouse clicks, accepts markup signals
Talks to Katago, manages an internal goban

In other words, Kitchen sink for the goban display & managment
"""

import kataproxy as KP
from GlobalSignals import GS
from goban import Goban
from goutils import *
import project_globals
import os

from GameSettingsDialog import GameSettingsDialog

from PyQt5.QtCore import QObject, Qt, QSettings, QPoint, QPointF, QSize, QTimer, QRect

from PyQt5.QtWidgets import (

    QGraphicsScene, QGraphicsItemGroup, QGraphicsEllipseItem, QGraphicsRectItem, 
    QGraphicsSimpleTextItem, QGraphicsLineItem, QMessageBox, QApplication, QGraphicsPixmapItem
)
from PyQt5.QtGui import QPen, QBrush, QRadialGradient, QImage, QPixmap, QFont, QFontMetrics
from PyQt5 import QtGui

# Use pools for the graphics items to reduce
# the amount of remove/creates, whch slow down the display

class HeatPool:
    def __init__(self, boardcontroller: 'BoardController') -> None:
        self.bc = boardcontroller
        self.heats = []
    def createHeat(self, value: float, cutoff: float =0.0, fade:bool = False) -> 'QGraphicsRectItem':
        "create a heat graphic and return it."
        if len(self.heats):
            h = self.heats.pop(-1)
            if value > cutoff:
                c = h.brush().color()
                newC = QtGui.QColor.fromRgb(max(int(min(255*(1.0-value), 255)),0), 127,max(int(min(value*255, 255)),0),127)
                if c != newC:
                    h.setBrush(QBrush(newC))
            else:
                h.setBrush(QBrush(Qt.NoBrush))
                #h.setBrush(Qt.NoBrush)
            h.show()
            return h
        else:
            h = self._createNewHeat(value, cutoff, fade)
            return h

    def remove(self, heatGraphicItem) -> None:
        "hide this item and put it back in the pool"
        heatGraphicItem.hide()
        if heatGraphicItem not in self.heats:
            self.heats.append(heatGraphicItem)
        
    def _createNewHeat(self, value: float, cutoff: float =0.0, fade:bool = False) -> 'QGraphicsRectItem':
        "raw method that actually creates the new graphics item when needed"
        pen = QPen(Qt.NoPen)
        if value > cutoff:
            c = QtGui.QColor.fromRgb(max(int(min(255*(1.0-value), 255)),0), 127,max(int(min(value*255, 255)),0),127)
            if fade:
                grad = QRadialGradient(QPoint(self.bc.increment/2, self.bc.increment/2), self.bc.increment/2)
                c.setAlpha(127)
                grad.setColorAt(0, c)
                c.setAlpha(0)
                grad.setColorAt(0.75, c)
                c = grad
            brush = QBrush(c)
            #brush = QtGui.QBrush(QtGui.QColor.fromRgb(255,200,0, value*255))
        else:
            brush = QBrush(Qt.NoBrush)

        heatThing = QGraphicsRectItem(0,0, self.bc.increment, self.bc.increment)
        heatThing.setBrush(brush)
        heatThing.setPen(pen)
        heatThing.setTransformOriginPoint(self.bc.increment/2, self.bc.increment/2)
        heatThing.setZValue(-9)
        if fade:
            heatThing.setScale(3)
        self.bc.scene.addItem(heatThing)
        return heatThing

    def destroyAll(self) -> None:
        "remove all cached items from the scene and forget them"
        for h in self.heats:
            self.bc.scene.removeItem(h)

        self.heats = []

class MarkPool:
    def __init__(self, boardcontroller: 'BoardController') -> None:
        self.bc = boardcontroller
        self.marks = []
        
        self.brushes = {
        "white": QBrush(self.color2qcolor("white")[0]),
        "black": QBrush(self.color2qcolor("black")[0]),
        "empty": QBrush(self.color2qcolor("empty")[0])
        }
        self.noPen = QPen(Qt.NoPen)

    def color2qcolor(self, color: str):
        # color is the color of the board beneath the mark
        if color == "empty":
            mycolor = QtGui.QColor.fromRgb(179,29,29, 255)
            mycolor = QtGui.QColor.fromRgb(0,0,220, 255)
            
            myoutline = mycolor
        elif color == "white":
            mycolor = QtGui.QColor.fromRgb(25,25,25,255)
            myoutline = mycolor
        else:
            mycolor = QtGui.QColor.fromRgb(230,230,230,255)
            myoutline = mycolor 
        
        # uniform red, which is really hard to read
        #mycolor = QtGui.QColor.fromRgb(179,29,29, 230) # red

        return mycolor, myoutline
    
    def createMark(self, text: str, color: str = "empty", scale: float =1.0) -> 'QGraphicsSimpleTextItem':
        if len(self.marks) > 0:
            m = self.marks.pop()
            f = m.font()
            ps = m.font().pointSize()
            newPS = max(int(self.bc.markFont.pointSize()*scale),1)
            if ps != newPS:
                f.setPointSize(newPS)
                m.setFont(f)
            if text != m.text():
                m.setText(text)

            m.setBrush(self.brushes[color])

            m.show()
            return m
        else:
            m =  self._createNewMark(text, color, scale)
            self.bc.scene.addItem(m)
            return m

    def _createNewMark(self, text: str, color: str = "empty", scale: float =1.0) -> 'QGraphicsSimpleTextItem':
        from PyQt5.QtGui import QFont
        
        mycolor, _ = self.color2qcolor(color)
        brush = QBrush(mycolor)

        t = QGraphicsSimpleTextItem(text)
        
        if scale == 1.0:
            t.setFont(self.bc.markFont)
        else:
            newF = QFont(self.bc.markFont)
            newF.setPointSize(max(int(newF.pointSize()*scale),1))
            t.setFont(newF)

        t.setPen(self.noPen)
        t.setBrush(self.brushes[color])
        #t.setTransformOriginPoint(self.bc.increment/2 -t.boundingRect().width()/2, -t.boundingRect().height()/2)
        t.setZValue(2)
        return t
    
    def remove(self, graphicsItem) -> None:
        "hide this graphics item and put it back in the pool"
        graphicsItem.hide()
        if graphicsItem not in self.marks:
            self.marks.append(graphicsItem)
    
    def destroyAll(self) -> None:
        "remove all cached items from the scene and forget them"
        for h in self.marks:
            self.bc.scene.removeItem(h)

        self.marks = []

class StonePool:
    def __init__(self, boardcontroller: 'BoardController') -> None:
        self.bc = boardcontroller
        self.stones = {"black": [], "white": []}
        
        # TODO: these are placeholders until themes are created
        d = os.path.join(project_globals.resource_directory, "images")
        self.black_image = QImage(os.path.join(d, "black_stone.png"))
        self.white_image = QImage(os.path.join(d, "white_stone.png"))
        self.shadow_image = QImage(os.path.join(d, "shadow.png"))

        self.black_pixmap = QPixmap.fromImage(self.black_image)
        self.white_pixmap = QPixmap.fromImage(self.white_image)
        self.shadow_pixmap = QPixmap.fromImage(self.shadow_image)

    def _setStoneData(self, s, color: str, gopoint: tuple[int,int]) -> 'QGraphicsItem':
        setattr(s, "stoneColor", color)
        x,y = self.bc.goPointToMouse(gopoint)
        s.setPos(x,y)

    def createStone(self, color: str, gopoint: tuple[int,int]) -> 'QGraphicsItem':
        "create a stone graphic and return it, use a cached one if possible"
        if len(self.stones[color]) > 0:
            s = self.stones[color].pop()
            s.show()
            self._setStoneData(s, color, gopoint)
            return s
        else:
            s = self._createNewStone(color, gopoint)
            self._setStoneData(s, color, gopoint)
            self.bc.scene.addItem(s)
            return s    

    def _createNewStoneBasic(self, color: str, gopoint: tuple[int,int]) -> 'QGraphicsItem':
        "actually create a real graphics item and return it"
        pen = QPen(Qt.black)
        if color == "white":
            brush = QBrush(Qt.white)
        else:
            brush = QBrush(Qt.black)
        
        stone = QGraphicsEllipseItem(0,0, self.bc.increment,self.bc.increment)
        stone.setPen(pen)
        stone.setBrush(brush)
        stone.setTransformOriginPoint(self.bc.increment/2, self.bc.increment/2)
        return stone

    def _createNewStone(self, color: str, gopoint: tuple[int,int]) -> 'QGraphicsItem':
        if color == "black":
            stone = QGraphicsPixmapItem(self.black_pixmap)
            #stone = self.bc.scene.addPixmap(self.black_pixmap)
        else:
            stone = QGraphicsPixmapItem(self.white_pixmap)
            #stone = self.bc.scene.addPixmap(self.white_pixmap)
        
        stone.setZValue(0)
        shadow =  QGraphicsPixmapItem(self.shadow_pixmap)
        shadow.setZValue(-1)

        #self.bc.scene.addPixmap(self.shadow_pixmap)

        brect = stone.boundingRect()
        #stone.setOffset(-0.5 * QPointF(brect.width(), brect.height()))
        stone.setScale(self.bc.increment/brect.width())

        brect = shadow.boundingRect()
        shadow.setTransformOriginPoint(-self.bc.increment/2, -self.bc.increment/2)
        shadow.setOffset(QPointF(brect.width()*-0.03, brect.height()*-0.02))
        shadow.setScale(2.03*self.bc.increment/brect.width())
        
        group = QGraphicsItemGroup()
        group.addToGroup(shadow)
        group.addToGroup(stone)
        if color == "white":
            group.setScale(0.96)

        return group

    def remove(self, graphicsItem) -> None:
        "hide this graphics item and return it to the pool"
        graphicsItem.hide()

        self.stones[graphicsItem.stoneColor].append(graphicsItem)

    def destroyAll(self) -> None:
        "remove all cached items from the scene and forget them"
        for key in self.stones.keys():
            for s in self.stones[key]:
                self.bc.scene.removeItem(s)
        self.stones = {'black': [], 'white': []}

class GhostStonePool(StonePool):
    def __init__(self, boardcontroller: 'BoardController') -> None:
        super().__init__(boardcontroller)

        for image in [self.black_image, self.white_image]:
            #FIXME there has got to be a better way
            for x in range(image.width()):
                for y in range(image.height()):
                    pix = image.pixelColor(x,y)
                    pix.setAlpha(int(pix.alpha() * 0.6))
                    image.setPixelColor(x,y, pix)

        self.black_pixmap = QPixmap.fromImage(self.black_image)
        self.white_pixmap = QPixmap.fromImage(self.white_image)

    def _createNewStone(self, color: str, gopoint: tuple[int,int]) -> 'QGraphicsItem':
        # no shadow
        if color == "black":
            stone = QGraphicsPixmapItem(self.black_pixmap)
            #stone = self.bc.scene.addPixmap(self.black_pixmap)
        else:
            stone = QGraphicsPixmapItem(self.white_pixmap)
            #stone = self.bc.scene.addPixmap(self.white_pixmap)
        
        stone.setZValue(0)
        brect = stone.boundingRect()
        #stone.setTransformOriginPoint(-self.bc.increment/2, -self.bc.increment/2)
        #shadow.setOffset(QPointF(brect.width(), brect.height()))
        stone.setScale(self.bc.increment/brect.width())

        return stone        

class HoverText(QObject):
    "Manage the hover text above the board."
    def __init__(self, boardcontroller: 'BoardController') -> None:
        super().__init__(parent=None)
        self.bc = boardcontroller
        self.hoverGroup = None
        self.recreate()

    def setHover(self, gopoint: tuple[int,int], text:str) -> None:
        "Set hover text for specified go point"
        self.hoverTexts[gopoint] = str(text)

    def clearHovers(self) -> None:
        "Clear all hover texts."
        self.hoverTexts = {}
        self.hoverGroup.hide()

    def mouseMove(self, eventpos: QPoint) -> None:
        "the mouse has moves, manage displaying the hover text, if any."
        if not self.bc.boardView.underMouse(): return
        
        gopoint = self.bc.mouseToGoPoint2(eventpos)
        
        if gopoint in self.hoverTexts and len(self.hoverTexts[gopoint]):
            text = self.hoverTexts[gopoint]

            # because QT is silly I have to calculate the box myself
            lines = text.splitlines()
            maxline = ""
            for l in lines:
                if len(l) > len(maxline):
                    maxline = l
            
            fm = QFontMetrics(self.hoverFont)
            rect = fm.boundingRect(maxline)
            rect.setHeight(fm.lineSpacing()*(len(lines)+1))
            
            self.hoverRectItem.setRect(-5,-5, rect.width()+10, rect.height())
            self.hoverTextItem.setText(text)
            
            x,y =  self.bc.goPointToMouse(gopoint)
            x += self.bc.increment/2 + 10
            y += self.bc.increment/2 + 10
            
            self.hoverGroup.setPos(QPoint(x,y))
            self.hoverGroup.show()
        else:
            self.hoverGroup.hide()
    
    def recreate(self) -> None:
        "destroy and rebuild, useful when board resized"
        if self.hoverGroup and self.hoverGroup in self.bc.scene.items():
            self.bc.scene.removeItem(self.hoverGroup)

        self.hoverTexts = {}
        self.hoverTextItem = QGraphicsSimpleTextItem()
        self.hoverTextItem.setPen(QPen(Qt.NoPen))
        self.hoverTextItem.setBrush(QBrush(Qt.black))
        
        self.hoverFont = QFont(self.bc.markFont)
        size = int(self.bc.markFont.pointSize()*0.75)
        if size <= 0:
            size = 1
        self.hoverFont.setPointSize(size)

        self.hoverTextItem.setFont(self.hoverFont)

        self.hoverRectItem = QGraphicsRectItem()
        p = QPen(Qt.black)
        p.setColor(QtGui.QColor.fromRgb(0,0,0,200))
        self.hoverRectItem.setPen(p)
        
        b = QBrush(Qt.white)
        b.setColor(QtGui.QColor.fromRgb(255,255,255,153))
        self.hoverRectItem.setBrush(QBrush(b))

        self.hoverGroup = QGraphicsItemGroup()
        self.hoverGroup.addToGroup(self.hoverRectItem)
        self.hoverGroup.addToGroup(self.hoverTextItem)
        
        self.bc.scene.addItem(self.hoverGroup)
        self.hoverGroup.setZValue(100)
        self.hoverGroup.hide()

import time,sys
class QueueSubmitter(QObject):
    "Class that submits quick analyses to KataProxy and rate-limts to avoid update lag"
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.queue = None # not much of a 'queue' as it only holds latest query
        self.delay = 1/30 # 30 fps-ish to start
        self.submissions = [] # backlog, for calculating rate limit

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.processQueue)
        self.timer.setInterval(self.delay*500)

        KP.KataSignals.answerFinished.connect(self.adjustRate)

    def processQueue(self):
        "timer is triggered, submit the latest query if available"
        if not self.queue: return

        self.submissions.append((time.time(), self.queue))

        KP.KataSignals.askForAnalysis.emit(self.queue)
        
        self.queue = None # drop outdated

    def addToQueue(self, query: dict):
        "Add a query but wait for a delay before sumbitting, so that fast future queries can supplant this one"
        self.queue = query
        self.timer.start()

    def adjustRate(self, finishedQuery: dict) -> None:
        """
        Called after an answer is ready.
        Try to guess the rate at which answers are being stalled and match the delay
        """

        if len(self.submissions) > 0:
            t, _ = self.submissions.pop(0)

            gap = time.time() - t

            self.delay = (self.delay + gap)/2
            self.delay = min(self.delay, 1.0)

            #print("delay: ", self.delay)

            self.timer.setInterval(self.delay*500) # 1/2 to keep it snappy

class GobanSnapshots:
    "Class to manage position snapshots"
    # about the only thing different betweeen this and a list
    # is that it copies on insert and keeps track of the insertion point
    def __init__(self):
        self.snaps = []
        self.cursor = 0

    def insertSnap(self, board: 'Goban') -> None:
        "insert this snapshot at current cursor"
        b = board.copy()
        self.snaps.insert(self.cursor, b)
        self.cursor += 1

    def getCurrentSnap(self) -> 'Goban':
        i = min(self.cursor, len(self.snaps) -1 )
        return self.snaps[i]

    def goBack(self, count:int = 1) -> 'Goban':
        "go back a snapshot and return it"
        more = 0
        if self.atEnd():
            more = 1
        self.cursor -= (count + more)
        if self.cursor < 0: self.cursor = 0
        return self.snaps[self.cursor]

    def goForward(self, count:int = 1) -> 'Goban':
        "go forward and return the snapshot found"
        self.cursor += count
        if self.cursor > len(self.snaps):
            self.cursor = len(self.snaps)
        
        i = min(self.cursor, len(self.snaps) -1 )
        
        return self.snaps[i]

    def goToBeginning(self) -> 'Goban':
        "go to the beginning of snapshots and return the position there"
        self.cursor = 0
        return self.getCurrentSnap()

    def goToEnd(self) -> 'Goban':
        "go to the end and return the position there"
        self.cursor = len(self.snaps)
        return self.getCurrentSnap()

    def atEnd(self) -> bool:
        "is cursor at the end?"
        return self.cursor >= len(self.snaps)

    def atBeginning(self) -> bool:
        "is cursor at beginning?"
        return self.cursor == 0

    def deleteCurrent(self) -> None:
        "delete the current snapshot"
        if len(self.snaps) == 0: return
        i = min(self.cursor, len(self.snaps) -1 )        
        del self.snaps[i]

    def deleteAll(self) -> None:
        if len(self.snaps) == 0: return
        self.snaps = []
        self.cursor = 0

class BoardController(QObject):
    "Control the graphics view widget. Constructs the board graphics scene and manages mouse clicks & events"
    ## Z layers:
    # -10 : the board
    # -5 : the heatmap
    # -1 : stone shadows
    # 0: stones
    # [0,1]: markings
    # 1: stoneInHand
    def __init__ (self, viewWidget):
        super().__init__()
        settings = QSettings()
        GS.addMark.connect(self.makeMark)
        GS.clearMark.connect(self.clearMark)
        GS.clearAllMarks.connect(self.clearMarks)
        GS.clearAllHeat.connect(self.clearHeats)
        GS.clearAllMarkup.connect(self.clearMarkup)
        
        GS.addGhostStone.connect(self.addGhostStone)
        GS.clearGhostStone.connect(self.removeGhostStone)
        GS.clearAllGhosts.connect(self.removeAllGhostStones)

        GS.heatValueChanged.connect(self.setHeatValue)

        GS.boardSizeChanged.connect(self.boardResized)
        GS.komiChanged.connect(self.komiChanged)

        GS.SetNeuralNetSettings.connect(self.nnSettingsChanged)

        self.analysisQueue = QueueSubmitter() # only for quick analysis, rate limit

        #FIXME these should be in settings or maybe not in this class at all
        self.neural_net = settings.value("nn/active_network", "B15") 
        settings.setValue("nn/active_network", self.neural_net)

        x = settings.value("GameSettings/board/xsize", 19)
        y = settings.value("GameSettings/board/ysize", 19)
        self.boardsize = (x,y)

        self.boardView = viewWidget


        # goban is a board that keeps track of caps, moves etc.
        # activeGoban is the current position while stone-dragging
        # and should be treated as a temporary IMMUTABLE
        self.goban = Goban(19,19)
        self.activeGoban = self.goban.copy()

        # snapshots are a list of "saved" goban positions
        # which can be reverted to and navigated to
        self.gobanSnapshots = GobanSnapshots()
        
        # Navigation timer is used to delay full analysis
        # during snapshot navigation
        self.navigationTimer = QTimer()
        self.navigationTimer.setSingleShot(True)
        self.navigationTimer.setInterval(0.5)
        self.navigationTimer.timeout.connect(self.analyzeAfterNavigate)

        self.setupGraphics()

        # pools for graphic items to reduce removes
        self.heatPool = HeatPool(self)
        self.markPool = MarkPool(self)
        self.stonePool = StonePool(self)
        self.ghostPool = GhostStonePool(self)


        # connect events to me
        self.boardView.resizeEvent = self.handleReshow
        self.boardView.mousePressEvent = self.handleMouseDown
        self.boardView.mouseMoveEvent = self.handleMouseMove
        self.boardView.mouseReleaseEvent = self.handleMouseUp
        self.boardView.wheelEvent = self.handleMouseWheel

        self.boardView.setMouseTracking(True)
        self.hoverThing = HoverText(self)

        GS.setHoverText.connect(self.hoverThing.setHover)
        GS.clearHoverTexts.connect(self.hoverThing.clearHovers)

        # variables for dragging stones with mouse
        self.mouseButtons = None
        self.mouseMode = "play" # "play", "paint"
        self.mouseState = None # "Dragging" "Painting" 
        self.mouseLastEvents = []
        self.paintColor = "black" # "black" "white" "empty"
        self.stoneInHand = None


        self._toplay = "black"

        self.komi = settings.value("GameSettings/komi", 6.5)

        # visits and analysis settings
        self.moreVisits = 0 # currently added visits via AnalyzeMore command
        self.incremental_updates = False # analyze in chunks for slower but more active board look
        self.restrictToDist = 0 # restrict analysis to this far away from stones (<=0 means no restriction)

        self.lastAnswerTime = None # for ordering kata answers correctly

        GS.MainWindowReadyAndWilling.connect(self.afterStartup)

    def relaunchKataGo(self, cmd, model, config):
        "Display a 'Launching KataGo' message and restart KataGo"
        prog = QMessageBox(project_globals.getMainWindow())
        prog.setText("Launching KataGo...")
        prog.setStandardButtons(QMessageBox.NoButton)
        prog.setModal(False)
        prog.show()
        # seems to only show if I spam these (shrug)
        QApplication.instance().processEvents()
        QApplication.instance().processEvents()
        QApplication.instance().processEvents()
        QApplication.instance().processEvents()

        try:
            if KP.GlobalKata() != None:
                self.kata = KP.GlobalKata()
                if self.kata.model != model:
                    prog.setText("Re-launching KataGo...")
                    self.kata.restart(KP.KATACMD, model, KP.KATACONFIG)

            else:
                self.kata = KP.GlobalKataInit(KP.KATACMD, model, KP.KATACONFIG)
            prog.hide()
            prog.close()
        except OSError as e:
            prog.setText(str(e))
            prog.setStandardButtons(QMessageBox.Abort)
            prog.setModal(True)
            prog.exec_()
            sys.exit()
        finally:
            prog.hide()
            prog.close() # doesn't really act like it's supposed to but here's hoping

    def afterStartup(self) -> None:
        "main app window is ready, so now do stuff that may depend upon it"
        # FIXME: kataproxy settings/management needs its own place
        import sys
        settings = QSettings()
        network = settings.value("nn/active_network", "B15")
        if network != "B15":
            network = "NBT"

        if network == "B15":
            model = KP.KATAMODEL_B15
        else:
            model = KP.KATAMODEL_NBT


        self.quickVisits = settings.value(f"nn/{network}/quick_visits", 2)
        self.defaultVisits = settings.value(f"nn/{network}/full_visits", 100)
        self.moreVisitsIncrement= settings.value(f"nn/{network}/step_visits", 500)

        self.relaunchKataGo(KP.KATACMD, model, KP.KATACONFIG)

        KP.KataSignals.answerFinished.connect(self.handleAnswerFinished)
        self.boardChanged() # trigger analysis on empty board

    def setupGraphics(self) -> None:
        "setup all the base graphics and calculate metrics"
        #setup graphics scene (the board)
        # and some variables for sizing the grid and placing stones
        self.scene = QGraphicsScene(0,0, 26*self.boardsize[0], 26*self.boardsize[1])

        if self.boardsize[0] > self.boardsize[1]:
            self.increment = (self.scene.height()/(self.boardsize[1]+1))
        else:
            self.increment = (self.scene.width()/(self.boardsize[0]+1))
        
        hPixels = self.increment*(self.boardsize[0]+1)
        vPixels = self.increment*(self.boardsize[1]+1)
        self.scene.setSceneRect(0, 0, hPixels, vPixels)

        self.margin = self.increment

        # the board content as graphic items
        self.stones = {} # the stone graphics for managing stones on the board.
        self.heat = {} # heat map values from 0.0 - 1.0 to display on board, and their graphics item graphicsitem.heat == the value
        self.marks = {} # textual marks on the board and whatnot
        self.ghost_stones = {}

        # create the base board graphics
        # TODO: this will eventually be moved to themes
        self.board_image = QImage(os.path.join(project_globals.resource_directory, "images", "board.png"))
        self.board_pixmap = QPixmap(self.board_image)
        
        if hPixels > vPixels:
            scaleSize = QSize(self.board_pixmap.rect().width(), self.board_pixmap.rect().height()*vPixels/hPixels)
        else:
            scaleSize = QSize(self.board_pixmap.rect().width()*hPixels/vPixels, self.board_pixmap.rect().height())
        
        pg = QGraphicsPixmapItem(self.board_pixmap.scaled(scaleSize, transformMode=Qt.SmoothTransformation))

        brect = self.board_pixmap.rect()
        pg.setScale(max(hPixels,vPixels)/min(brect.width(), brect.height()))
        pg.setZValue(-11)

        self.scene.addItem(pg)

        self.addGrid()
        self.boardView.setScene(self.scene)
        self.boardView.setSceneRect(self.scene.sceneRect()) # needed for auto alignment inside parent to work


        from PyQt5.QtGui import QFont, QFontMetrics

        default = QFont();  default.setPointSize(10)
        w = QFontMetrics(default).boundingRect("M").width()
        pointPerPix = 10/w
        pointSize = (self.increment * pointPerPix)/2.5 # generally fits 3 characters
        default.setPointSize(int(pointSize))
        default.setBold(True)
        self.markFont = default

    def boardResized(self, size: tuple[int, int]) -> None:
        "the goban is a different size/shape so destroy everything and create the new one"
        # could be shortened TBH
        self.boardsize = size
        settings = QSettings()
        settings.setValue("GameSettings/board/xsize", size[0])
        settings.setValue("GameSettings/board/ysize", size[1])

        self.clearAllBookmarks()
        self.goban = Goban(size[0], size[1])
        self.clearMarks()
        self.clearHeats()
        self.heatPool.destroyAll()
        self.markPool.destroyAll()      
        self.stonePool.destroyAll()
        self.ghostPool.destroyAll()
        self.scene.clear()
        self.setupGraphics()
        self.hoverThing.recreate()
        self.handleClearBoard()
        self.handleReshow(None)

    def komiChanged(self, komi: float) -> None:
        self.komi = komi
        settings = QSettings()
        settings.setValue("GameSettings/komi", komi)
        self.boardChanged()

    def doGameSettings(self) -> None:
        "present the game settings dialog box"
        dlg = GameSettingsDialog(settings = (self.boardsize[0], self.boardsize[1], self.komi))
        #dlg.setWindowTitle("Game Settings")
        #print(dir(dlg))
        if dlg.exec():
            if dlg.xsize != self.boardsize[0] or dlg.ysize != self.boardsize[1]:
                GS.boardSizeChanged.emit( (dlg.xsize, dlg.ysize,))
            
            if dlg.komi != self.komi:
                GS.komiChanged.emit(dlg.komi)
            
        else:
            pass #cancel

    def nnSettingsChanged(self, info: dict) -> None:
        "Neural net settings changed, so restart KataGo if necessary"
        restart = False
        if self.neural_net != info['network']:
            restart = True
        
        self.neural_net = info['network']
        self.quickVisits = info['quick_visits']
        self.defaultVisits = info['full_visits']
        self.moreVisitsIncrement = info['step_visits']

        if restart:
            if self.neural_net == "NBT":
                self.relaunchKataGo(KP.KATACMD, KP.KATAMODEL_NBT, KP.KATACONFIG)
            else:
                self.relaunchKataGo(KP.KATACMD, KP.KATAMODEL_B15, KP.KATACONFIG)

    def addGrid(self) -> None:
        "build the grid and hoshi"
        pen = QPen(Qt.black)
        pen.setColor(QtGui.QColor.fromRgb(51,39,7, 255))
        pen.setColor(QtGui.QColor.fromRgb(64,49,9, 255))
        pen.setWidth(0) # weirdly this still draws hairlines, which is what I want

        #pen.setColor(QtGui.QColor.fromRgb(0,0,0, 127))
        brush = QtGui.QBrush(QtGui.QColor.fromRgb(255,200,0))
        brush = QtGui.QBrush(QtGui.QColor.fromRgb(240,192,63))
        # the board background
        #r = self.scene.addRect(0, 0, self.scene.width(), self.scene.height(), pen, brush)
        #r.setZValue(-10)

        #print("SCENE WIDTH: ", self.scene.width())
        #print("MARGIN: ", self.margin)

        # the grid
        for x in range(self.boardsize[0]):
            x1 = self.margin + x*self.increment #math.floor(self.margin + x * self.increment)
            x2 = x1
            y1 = self.margin #math.floor(self.margin)
            y2 = self.scene.height()-self.margin #math.floor(self.scene.height() - self.margin)
            l = self.scene.addLine(x1, y1, x2, y2, pen)
            l.setZValue(-5)

        for y in range(self.boardsize[1]):
            y1 = self.margin + y * self.increment # math.floor(self.margin + y * self.increment)
            y2 = y1
            x1 = self.margin # math.floor(self.margin)
            x2 = self.scene.width() - self.margin # math.floor(self.scene.width() - self.margin)
            l = self.scene.addLine(x1,y1,x2,y2, pen)
            l.setZValue(-5)

        #border
        pen.setWidth(1)
        r = self.scene.addRect(self.margin, self.margin, self.scene.width()-self.margin*2, self.scene.height()-self.margin*2, pen)
        r.setZValue(-5)
        self.addHoshi()

    def addHoshi(self) -> None:
        "create the hoshi depending on board size and add to scene"
        pen = QPen()
        pen.setWidth(0)
        brush = QtGui.QBrush(Qt.black)
        brush.setColor(QtGui.QColor.fromRgb(64,49,9, 255))

        size = 3
        if min(self.boardsize[0], self.boardsize[1]) > 12:
            h = 3
        else:
            h = 2

        points = [(h,h), (self.boardsize[0]-(h+1), h), (h, self.boardsize[1]-(h+1)), (self.boardsize[0]-(h+1), self.boardsize[1]-(h+1))]

        if self.boardsize[0] % 2 == 1:
            points.append ((self.boardsize[0]//2, h))
            points.append ((self.boardsize[0]//2, self.boardsize[1] -h-1))
            points.append ((h, self.boardsize[1]//2))
            points.append ((self.boardsize[0]-h-1, self.boardsize[1]//2))
            points.append ((self.boardsize[0]//2, self.boardsize[1]//2))

        for p in points:
            e = QGraphicsEllipseItem(0,0, size, size)
            e.setPen(pen)
            e.setBrush(brush)
            e.setTransformOriginPoint(size/2, size/2)
            e.setPos(self.margin + p[0]*self.increment - size/2, self.margin + p[1]*self.increment - size/2)
            e.setZValue(-5)
            self.scene.addItem(e)


    def createHeat_overgrid(self, value: float, cutoff: float =0.0) -> 'QGraphicsItemGroup':
        "unused ATM"
        cross = QGraphicsItemGroup()
        pen = QPen(QtGui.QColor.fromRgb(max(min(255*(1.0-value), 255),0), 127,max(min(value*255, 255),0)))
        pen = QPen(QtGui.QColor.fromRgb(255,200, 0, max(min(value*127,255),0)))
        pen.setWidth(3)

        line = QGraphicsLineItem(self.increment/2, 0, self.increment/2, self.increment)
        line.setPen(pen)
        cross.addToGroup(line)

        line = QGraphicsLineItem(0, self.increment/2, self.increment, self.increment/2)
        line.setPen(pen)
        cross.addToGroup(line)

        heatThing = cross
        heatThing.setTransformOriginPoint(self.increment/2, self.increment/2)
        return heatThing

    def handleReshow(self, dummy) -> None:
        "adjust the view on resize/show so board is always centered at max size."
        self.boardView.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def handleClearBoard(self) -> None:
        "remove stones from the board, sync the activeGoban, send a boardChanged signal"
        for point in list(self.stones.keys()):
            self.stonePool.remove(self.stones[point])
        
        self.stones = {}
        self.goban.clear()
        self.activeGoban = self.goban.copy()

        self.boardChanged()

    @property
    def toplay(self) -> str:
        return self._toplay

    @toplay.setter
    def toplay(self, color: str) -> None:
        if (self._toplay != color):
            self._toplay = color
            GS.toPlayChanged.emit(self._toplay)

    def handleFlipPlayer(self) -> None:
        "user chose to flip player"
        self._toplay = opponent(self._toplay)
        self.askForFullAnalysis(visits = self.moreVisits)

    def handleAnalyzeMore(self) -> None:
        "user chose analyze more command"
        self.moreVisits = self.moreVisits + self.moreVisitsIncrement
        self.askForFullAnalysis(visits = self.moreVisits)

    def handleToggleDraw(self, onOff: bool) -> None:
        "user chose to toggle paint mode"
        if onOff:
            self.mouseMode = "paint"
        else:
            self.mouseMode = "play"

    def handleBookmark(self) -> None:
        self.gobanSnapshots.insertSnap(self.goban)

    def clearBookmark(self) -> None:
        self.gobanSnapshots.deleteCurrent()

    def clearAllBookmarks(self) -> None:
        self.gobanSnapshots.deleteAll()

    def paintStone(self, point: tuple[int,int], color: str) -> None:
        "place a stone of this color at this go point"
        changed = False
        if not isOnBoard(point, self.boardsize[0], self.boardsize[1]):
            return
        
        if point in self.stones:
            if self.stones[point].stoneColor == color:
                return;                

            self.stonePool.remove(self.stones[point])
            del self.stones[point]
            self.goban.remove(point)
            changed = True

        if color != "empty":
            s = self.stonePool.createStone(color, point)
            self.stones[point] = s
            self.goban.place(color, point)
            changed = True

        if changed: 
            self.activeGoban = self.goban.copy()
            self.boardQuickChanged()

    def snapPoint(self, mousepoint) -> tuple[int,int]:
        "given a mouse location, return a location snapped to nearest go point"
        pos = self.mouseToGoPoint(self.boardView.mapToScene(mousepoint))
        return self.goPointToMouse(pos)

    def tryMove(self, color: str, destPoint: tuple[int,int], origPoint=None) -> None:
        "try the stoneInHand move and trigger a quick analysis"
        #print("QUEUE DEPTH: ", self.kata.queueDepth())
        if not isOnBoard(destPoint, self.boardsize[0], self.boardsize[1]):
            return

        g = self.goban.copy()
        if origPoint != None:
            g.relocate(origPoint, destPoint)
        else:
            g.play(color, destPoint)

        self.activeGoban = g
        self.boardQuickChanged()

    def clearStoneInHand(self) -> None:
        "clean up the stone in hand, probably after a drag"
        if self.stoneInHand:
            self.scene.removeItem(self.stoneInHand)
            self.stoneInHand = None

    def startDrag(self, event, gopoint: tuple[int,int]) -> None:
        "user starts dragging, set up state and create a stone in hand if necessary"
        if self.mouseState == "Dragging Copy" or self.mouseState == "Dragging Play":
            self.clearStoneInHand()
            if self.mouseState == "Dragging Play":
                self.stoneInHand = self.stonePool.createStone(self.toplay, gopoint)
            else:
                self.stoneInHand = self.stonePool.createStone(self.stones[gopoint].stoneColor, gopoint)

            setattr(self.stoneInHand, "origPoint", None)
            setattr(self.stoneInHand, "location", gopoint)
            self.activeGoban = self.goban.copy()
        elif self.mouseState == "Dragging":
            self.clearStoneInHand()
            self.stoneInHand = self.stonePool.createStone(self.stones[gopoint].stoneColor, gopoint)
            self.stones[gopoint].hide()
            setattr(self.stoneInHand, "origPoint", gopoint)
            setattr(self.stoneInHand, "location", gopoint)
            self.activeGoban = self.goban.copy()
            #self.activeGoban.remove(gopoint)

    def capture_capturable(self, color:str) -> None:
        """
        capture all groups with no liberties, assuming color caps first.
        should only call after a paint/copy event, not an actual move
        """
        b, w = self.goban.cap_all_stones(color)
        stones = b+w
        if len(stones):
            for s in stones:
                if s in self.stones:
                    self.scene.removeItem(self.stones[s])
                    del self.stones[s]

    def endDrag(self, event) -> None:
        "the drag has ended, do the magic of setting the board, etc."
        gopoint = self.mouseToGoPoint2(event.pos())
        trashIt = False
        #print("GOPOINT, ENDDRAG: ", gopoint)
        if not isOnBoard(gopoint, self.boardsize[0], self.boardsize[1]):
            trashIt = True

        if trashIt:
            #print("TRASH IT")
            if self.mouseState == "Dragging":
                self.goban.remove(self.stoneInHand.origPoint)
                self.scene.removeItem(self.stones[self.stoneInHand.origPoint])
                del self.stones[self.stoneInHand.origPoint]
            self.clearStoneInHand()
            self.activeGoban = self.goban.copy()
        else:
            if self.stoneInHand.location == self.stoneInHand.origPoint:
                self.stones[self.stoneInHand.origPoint].show()
                self.clearStoneInHand()
            else:
                if gopoint in self.stones:
                    # stone is above existing stone so
                    # treat it as a place always
                    self.goban.remove(gopoint)
                    self.goban.place(self.stoneInHand.stoneColor, gopoint)
                    self.activeGoban = self.goban.copy()
                    self.scene.removeItem(self.stones[gopoint])
                    self.stones[gopoint] = self.stoneInHand
                    self.capture_capturable(self.stoneInHand.stoneColor)
                    self.stoneInHand = None
                else:
                    if self.mouseState == "Dragging Copy":
                        self.goban.place(self.stoneInHand.stoneColor, gopoint)
                        self.capture_capturable(self.stoneInHand.stoneColor)
                    elif self.mouseState == "Dragging Play":
                        caps = self.goban.play(self.stoneInHand.stoneColor, gopoint)
                        for c in caps:
                            if c in self.stones:
                                self.scene.removeItem(self.stones[c])
                                del self.stones[c]
                        if self.toplay == self.stoneInHand.stoneColor:
                            self.toplay = opponent(self.stoneInHand.stoneColor)
                    elif self.mouseState == "Dragging":
                        self.goban.relocate(self.stoneInHand.origPoint, self.stoneInHand.location)
                        del self.stones[self.stoneInHand.origPoint]
                        self.capture_capturable(self.stoneInHand.stoneColor)                        

                    self.stones[gopoint] = self.stoneInHand
                    self.stoneInHand = None

        self.activeGoban = self.goban.copy()
        self.boardChanged()

    def handleMouseDown(self, event) -> None:
        "detect the current mouse operation mode and begin drag/paint if necessary"
        self.mouseButtons = event.buttons()
        point = self.mouseToGoPoint(self.boardView.mapToScene(event.pos()))
        if self.mouseMode == "play":
            if self.mouseButtons and self.mouseButtons & Qt.LeftButton:
                if point in self.stones:
                    if event.modifiers() & Qt.AltModifier:
                        self.mouseState = "Dragging Copy"
                    else:
                        self.mouseState = "Dragging"
                else:
                    self.mouseState = "Dragging Play"

            elif self.mouseButtons and self.mouseButtons & Qt.RightButton:
                self.mouseState = "Painting"
                self.paintColor = "empty"

            self.startDrag(event, point)
            self.handleMouseMove(event, firstClick=True)

        elif self.mouseMode == "paint":
            self.mouseState = "Painting"

            if self.mouseButtons and self.mouseButtons & Qt.RightButton:
                self.paintColor = "empty"
            elif self.mouseButtons and self.mouseButtons & Qt.LeftButton:
                if event.modifiers() & Qt.ShiftModifier:
                    self.paintColor = "white"
                else:
                    self.paintColor = "black"
            self.handleMouseMove(event, firstClick=True) # trigger for first process

    def handleMouseMove(self, event, firstClick: bool =False) -> None:
        "drag the stone, paint, etc."
        import time
        self.mouseLastEvents.append({"x": event.x(), "y": event.y(), "t": time.time()})
        self.hoverThing.mouseMove(event.pos())

        if self.mouseState in ["Dragging", "Dragging Copy", "Dragging Play"]:
            gopoint = self.mouseToGoPoint2(event.pos())
            
            if not firstClick and self.stoneInHand.location == gopoint:
                return

            x,y = self.snapPoint(event.pos())
            self.stoneInHand.setPos(x,y)
            self.stoneInHand.location = gopoint
            
            #FIXME: try to rate limit these quick analyses as it can lag quite a bit
            self.tryMove(self.stoneInHand.stoneColor, self.stoneInHand.location, self.stoneInHand.origPoint)

        elif self.mouseState == "Painting":
            gopoint = self.mouseToGoPoint2(event.pos())
            self.paintStone(gopoint, self.paintColor)
        else:
            # if intersection info is on, show information about that point in
            # a pop-up
            pass


    def handleMouseUp(self, event) -> None:
        "end the drag state if any and update the board/analysis"
        if self.mouseState in ["Dragging", "Dragging Copy", "Dragging Play"]:
            self.endDrag(event)
        elif self.mouseState == "Painting":
            self.capture_capturable(self.paintColor)
            self.activeGoban = self.goban.copy()
            self.boardChanged()

        self.mouseState = None
        self.stoneInHand = None
        self.mouseLastEvents = []

    def historyBack(self) -> None:
        if not self.gobanSnapshots.atBeginning():
            newGoban = self.gobanSnapshots.goBack()
            self.changeGoban(newGoban)
            self.navigationTimer.start()

    def historyForward(self) -> None:
        if not self.gobanSnapshots.atEnd():
            newGoban = self.gobanSnapshots.goForward()
            self.changeGoban(newGoban)
            self.navigationTimer.start()

    def handleMouseWheel(self, event) -> None:
        # have to be careful, ignore if inside a drag or paint
        if self.mouseState != None: return
        newGoban = None
        if len(self.gobanSnapshots.snaps):
            if event.angleDelta().y() < 0:
                self.historyBack()
            else:
                self.historyForward()

    def analyzeAfterNavigate(self) -> None:
        "Called through a timer signal so as not to lag during history navigation"
        self.askForFullAnalysis()

    def changeGoban(self, newGoban: 'Goban') -> None:
        "when user navigates through history"
        diffs = self.goban.diff(newGoban)
        for intersection in diffs:
            if intersection in self.stones:
                self.stonePool.remove(self.stones[intersection])
                del self.stones[intersection]

            col  = newGoban.get(intersection)
            if col != "empty":
                s = self.stonePool.createStone(col, intersection)
                self.stones[intersection] = s

        self.goban = newGoban.copy()
        self.activeGoban = newGoban.copy()
        self.askForQuickAnalysis()

    def mouseSpeed(self) -> tuple[float, float]:
        "calculate mouse speed, unused ATM"
        e = self.mouseLastEvents
        if len(e) < 2: return 0,0
        a = e[-2]
        b = e[-1]
        dist = math.sqrt(pow(b["x"] -a["x"], 2) + pow(b["y"] - a["y"], 2))
        t = b["t"] - a["t"]
        velocity = dist/t
        return velocity, dist

    def mouseFlicked(self) -> bool:
        "unused ATM. Was kind of cool but not very useful"
        s, dist = self.mouseSpeed()
        return dist > 8 and s > 500

    def mouseToGoPoint(self, qpoint) -> tuple[int,int]:
        "local mouse point to go coordinates"
        x = int((qpoint.x() - self.margin/2)/self.increment) # margin/2 to create clicable area around the intersection
        y = int((qpoint.y() - self.margin/2)/self.increment)
        y = self.boardsize[1] - y -1 # vert is flipped

        return (x,y)

    def mouseToGoPoint2(self, qpoint) -> tuple[int,int]:
        "like moustToGoPoint but automatically map to scene"
        p = self.boardView.mapToScene(qpoint)
        x = int((p.x() - self.margin/2)/self.increment) # margin/2 to create clicable area around the intersection
        y = int((p.y() - self.margin/2)/self.increment)
        y = self.boardsize[1] - y -1 # vert is flipped

        return (x,y)

    def goPointToMouse(self, point: tuple[int, int]) -> tuple[int, int]:
        "go point to local x,y"
        x = (point[0])*self.increment + self.margin/2
        y = (self.boardsize[1] - point[1] -1)*self.increment + self.margin/2
        return(x,y)
    
    def positionToStoneList(self) -> tuple:
        "convenience method to get position in a format KataGo likes"
        initial, moves = self.activeGoban.stones_n_moves_coords()
        return initial, moves

    def setRestrictDist(self, dist: int) -> None:
        "Set the distance away from stones that the analysis is restricted to"
        if dist != self.restrictToDist:
            self.restrictToDist = dist
            self.askForFullAnalysis()

    def restrictedPoints(self) -> list[tuple[int,int]]:
        "retrieve a list of points at which the analysis is restricted to"
        if self.restrictToDist <= 0: 
            return None
        
        return list(self.activeGoban.nearby_stones(self.restrictToDist))
    
    def boardQuickChanged(self) -> None:
        "typically during a drag, request a quick analysis for the changed board"
        self.askForQuickAnalysis()

    def boardChanged(self, save_snap:bool = False) -> None:
        "usually on mouse up, ask for a deeper full analysis"
        if save_snap:
            self.gobanSnapshots.insertSnap(self.goban)
        self.askForFullAnalysis()

    def getBoardToPlay(self) -> str:
        """
        determine which perspective we should show the analysis from,
        given the intent of the user
        """
        # only show opponent responses if new stone
        if self.stoneInHand != None and self.mouseState == "Dragging Play":
            return opponent(self.stoneInHand.stoneColor)
        else:
            return self.toplay

    def clearMarks(self) -> None:
        "clear all textual markings"
        for k,m in self.marks.items():
            self.markPool.remove(m)

        self.marks = {}

    def clearHeats(self) -> None:
        "clear the heat map"
        for key, val in self.heat.items():
            self.heatPool.remove(val)

        self.heat = {}

    def clearMarkup(self) -> None:
        "clear heat map and text markings"
        self.clearMarks()
        self.clearHeats()

    def clearMark(self, gopoint: tuple[int, int]) -> None:
        "clear a single mark"
        if gopoint in self.marks:
            self.markPool.remove(self.marks[gopoint])
            del self.marks[gopoint]

    def makeMark(self, gopoint: tuple[int, int], symType: str, options: dict):
        "construct a mark and put it in the scene, reacts to a signal request"
        halign = 'center'
        valign = 'center'
        rgb = None
        scale = 1.0

        if 'halign' in options:
            halign = options['halign']
        if 'valign' in options:
            valign = options['valign']
        if 'scale' in options:
            scale = options['scale']
        
        #print(f"Gopoint is {gopoint}")
        if symType == "triangle":
            self.makeMarkText(gopoint, "△", rgb=None, halign=halign, valign=valign, scale=scale)
        elif symType == "circle":
            self.makeMarkText(gopoint, "◯", rgb=None, halign=halign, valign=valign, scale=scale)
        elif symType == "square":
            self.makeMarkText(gopoint, "□", rgb=None, halign=halign, valign=valign, scale=scale)
        elif symType == "x":
            self.makeMarkText(gopoint, "✕", rgb=None, halign=halign, valign=valign, scale=scale)
        else: # assume text
            self.makeMarkText(gopoint, symType, rgb=None, halign=halign, valign=valign, scale=scale) 

    def makeMarkText(self, gopoint, text:str, rgb=None, halign='center', valign='center', scale=1.0):
        "all marks are text ATM. Make a text item and put it in the scene"
        col = "empty"
        if gopoint in self.stones:
            col = self.stones[gopoint].stoneColor
        if self.stoneInHand and self.stoneInHand.location == gopoint:
            col = self.stoneInHand.stoneColor

        item = self.markPool.createMark(text, color=col, scale=scale)

        x,y = self.goPointToMouse(gopoint)

        plusX, plusY = (self.increment/2, self.increment/2)
        w = item.boundingRect().width()
        h = item.boundingRect().height()

        if halign == 'center':
            plusX -= w/2
        elif halign == 'right':
            plusX -= w
        else:
            plusX = plusX

        if valign == 'center':
            plusY -= h/2
        elif valign == 'bottom':
            plusY -= h
        else:
            plusY = plusY

        item.setPos(x+plusX, y+plusY)

        if gopoint in self.marks:
            self.markPool.remove(self.marks[gopoint])
            del self.marks[gopoint]
        self.marks[gopoint] = item
        #self.scene.addItem(item)

    def setHeatValue(self, gopoint: tuple[int, int], value: float) -> None:
        "Set the heatmap value at gopoint"
        if gopoint in self.heat:
            self.heatPool.remove(self.heat[gopoint])
            del self.heat[gopoint]
        newheat = self.heatPool.createHeat(value, 0.001)
        newheat.value = value
        #newheat.setZValue(-9)
        x,y = self.goPointToMouse(gopoint)
        newheat.setPos(x,y)
        #self.scene.addItem(newheat)
        self.heat[gopoint] = newheat
        
    def addGhostStone(self, color:str, gopoint: tuple[int,int], options: dict) -> None:
        "place a translucent stone at this gopoint"
        scale = 1.0

        if 'scale' in options:
            pass # FIXME: all stones need to be offset on creation & all code adjusted :-(
            #scale = options['scale']

        self.removeGhostStone(gopoint)
        item = self.ghostPool.createStone(color, gopoint)

        item.setScale(item.scale()*scale)
        self.ghost_stones[gopoint] = item

    def removeGhostStone(self, gopoint):
        if gopoint in self.ghost_stones:
            self.ghostPool.remove(self.ghost_stones[gopoint])
            del self.ghost_stones[gopoint]

    def removeAllGhostStones(self):
        for s in self.ghost_stones:
            self.ghostPool.remove(self.ghost_stones[s])

        self.ghost_stones = {}

    def prepQuery(self, idname: str, maxVisits:int =2, flipPlayer:bool =False) -> dict:
        "given the activeGoban, prepare a query for sending to KataGo"
        import time
        #print("PREPPING QUERY ", idname)
        id = idname + "_" + str(time.time_ns())

        initial, moves = self.positionToStoneList()
        restricted = self.restrictedPoints()
        #print("RESTRICTED ", restricted)

        if len(moves) == 0:
            if len(initial) > 0:
                moves = [initial[-1]]
                initial = initial[:-1]

        white_stones = self.activeGoban.white_stones()
        black_stones = self.activeGoban.black_stones()
        
        query = {
            "id": id,
            "boardXSize": self.boardsize[0],
            "boardYSize": self.boardsize[1],
            "initialStones": initial,
            "rules": "Chinese",
            "maxVisits": maxVisits,
            "moves": moves,
            "black_stones": black_stones,
            "white_stones": white_stones,
            "komi": self.komi
            #"includeOwnership": True,
            #"includePolicy": True,
            #"includePVVisits": True
        }

        toplay = self.getBoardToPlay()[0].upper()
        if flipPlayer: toplay = opponent(toplay)

        if restricted:
            theMoves= [pointToCoords(p) for p in restricted]
            #print("ALLOW MOVES: ", theMoves)
            theDict = {
                    'player': toplay,
                    'moves' : theMoves,
                    'untilDepth': 1,
                    }

            query['allowMoves'] = [theDict]

        if len(moves) == 0:
            query["initialPlayer"] = toplay
        else:
            # KataGo tries to "guess" which perspective I want (black or white's).
            # This leads to nonsense results when moves[] available. So, force a pass
            # if needed to keep the side to play correct
            #print(toplay, opponent(toplay))
            if toplay[0].upper() == (moves[-1][0])[0].upper():
                moves.append([opponent(toplay)[0].upper(), "pass"])
            #print(f"MOVES: {moves}")
        #print(f"TO PLAY: {self.getBoardToPlay()}")
        return query

    def handleAnswerFinished(self, ans: dict) -> None:
        "KataGo has finished an analysis, process it. Called by KataProxy via KataSignal"
        id = ans['id']
        if id == "wait for startup": return # FIXME: total hack for when user changes networks

        #print(f"ANSWER FINISHED {id}")
        #id is name of asker_timeinnanos
        parsed = id.split("_")
        name, t = parsed[0], int(parsed[1])

        out_of_date = False
        if self.lastAnswerTime and self.lastAnswerTime > t:
            out_of_date = True
            #print("OUT OF DATE: ", id, file=sys.stderr)

        self.lastAnswerTime = t

        #print(f"NAME IS {name}")
        if name == "policyHeat":
            self.kata.claimAnswer(id)
            self.showPolicies(answer=ans)
            #print("GOT POLICY ANSWER")
        elif name == "fullAnalysis":
            #print("emitting full analysis")
            self.kata.claimAnswer(id)
            if not out_of_date:
                GS.fullAnalysisReady.emit({"t": t, "payload": ans})
            self.moreVisits = ans['originalQuery']['maxVisits']

        elif name == "quickAnalysis":
            self.kata.claimAnswer(id)
            if not out_of_date:
                GS.quickAnalysisReady.emit({"t": t, "payload": ans})

    def handleFullAnalysis(self, signalData: dict) -> None:
        "process the full analysis info. UNUSED"
        print("HANDLING fullAnalysis", signalData['t'])
        pass #kataResults = signalData["payload"]

    def askForFullAnalysis(self, visits=None) -> None:
        "Construct a query of the current position and submit it to Katago"
        if visits == None:
            visits = max(self.defaultVisits, 2)
        else:
            visits = max(visits, 2)

        visitChunk = visits

        if self.incremental_updates:
            visitChunk = 20

        maxV = 0

        while maxV < visits:
            maxV += visitChunk
            if maxV > visits: maxV = visits

            q = self.prepQuery("fullAnalysis", maxVisits=maxV)
            more = {
                "includeOwnership": True,
                "includePolicy": True,
                "includePVVisits": True
            }
            q.update(more)
            #self.analysisQueue.addToQueue(q) # because takes longer we don't want it mucking with rate limiting
            KP.KataSignals.askForAnalysis.emit(q)

        #self.kata.ask(q)

    def askForQuickAnalysis(self) -> None:
        "prep a short, low visit query for the current position and submit to Katago "
        q = self.prepQuery("quickAnalysis", maxVisits=max(self.quickVisits, 2))
        more = {
            "includeOwnership": True,
            "includePolicy": True,
            "includePVVisits": True
        }
        q.update(more)
        self.analysisQueue.addToQueue(q)
        #KP.KataSignals.askForAnalysis.emit(q)


