# KataProxyQ is a Qt (gui or command line) proxy
# for KataGo that provides enhanced analysis facilities

import os

_mypath = os.path.abspath(os.path.dirname(__file__)) 

BIN_PATH = os.path.join(_mypath, "katago-bin")
KATACMD =  os.path.join(BIN_PATH, "katago")

KATAMODEL_NBT = os.path.join(BIN_PATH, "kata1-b18c384nbt-s9131461376-d4087399203.bin.gz")
KATAMODEL_B15 = os.path.join(BIN_PATH, "kata1-b15c192-s1672170752-d466197061.txt.gz")
KATAMODEL = KATAMODEL_B15

KATACONFIG = os.path.join(BIN_PATH, "analysis.cfg")
KATATHREADS = "2" # this is for mutli-position processing. Small helps lower latency b/c threads are working hard analyzing current position

import traceback
from PyQt5.QtCore import QProcess, QObject, pyqtSignal, QCoreApplication
from PyQt5 import QtCore
import PyQt5

import time, json, sys
from statistics import median, mean

import pandas as pd
import numpy as np

from goutils import *

class _KataSignals(QObject):
    askForAnalysis = pyqtSignal(dict)
    #answerReady = pyqtSignal(str) # provides the id of the answer that is ready 
    answerFinished = pyqtSignal(dict) # the raw answer as a dictionary
    claimAnswer = pyqtSignal(str) # claim an answer, thus removing it from the cache
    stderrPrinted = pyqtSignal(str) # when stderr prints something

    def __init__(self) -> None:
        super().__init__()

KataSignals = _KataSignals()

# it's quite impossible to ask for analysis in a blocking way
# using signals and slots in a decoupled environment, so we must 
# offer a global katago object to provide this functionality
# this is not necessary if you don't need blocking answer/response in a gui

_globalKata = None
def GlobalKata():
    return _globalKata

def GlobalKataInit(cmd, model, config):
    global _globalKata
    _globalKata = KataProxyQ(cmd, model, config)
    return _globalKata

def eprint(*args, **kwargs):
    "just like print() but to stderr"
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)

def other_color(color: str):
    if color.upper()[0] == "W":
        return "black"
    else:
        return "white"

def same_color(color: str):
    # to make the black/white regular
    if color.upper()[0] == "W":
        return "white"
    elif color.upper()[0] == "B":
        return "black"
    elif color.upper()[0] == "E":
        return "empty"

    raise ValueError("color string must start with W, B or E")

class dotdict(dict):
    "dot notation for dictionary"
    __getattr__ = dict.__getitem__
    __delattr__ = dict.__delitem__
    __setattr__ = dict.__setitem__

class KataAnswer:
    "a class to make using katago analysis data easier"
    from functools import cached_property
    def __init__(self, rawAnswer: dict):
        self.answer = moreKataData(rawAnswer)
        self._buildIntersections()
        self._moves = sorted([m for m in self.intersections if m.isMove], key=lambda m: m['order'], reverse=False)

        self.__dict__.update(self.answer['stats'])
        self.__dict__.update(self.answer['rootInfo'])

        self.__dict__['bestMove'] = self.moves[0]
        
        # FIXME: seems a waste to always do for an occasional convenience
        for i, x in enumerate(self.merged_moves):
            x['mergedOrder'] = i
    
    @property
    def moves(self):
        "intersection data of KataGo suggested moves"
        return self._moves
    
    @cached_property
    def legal_moves(self):
        "intersection data for all legal moves for current player"
        return [i for i in self.intersections if i['policy'] > 0]

    @cached_property
    def illegal_moves(self):
        "intersection data for all illegal moves for current player"
        return [i for i in self.intersections if i['policy'] <= 0]

    @cached_property
    def moves_by_policy(self):
        "legal_moves pre-sorted by policy value"
        return sorted(self.legal_moves, key=lambda p: -p.policy)

    @cached_property
    def merged_moves(self):
        "both moves and unvisited legals combined & sorted by rank"
        return self.moves + [p for p in self.moves_by_policy if p not in self.moves]

    @cached_property
    def white_stones(self):
        "intersection data for each intersection with a white stone on it"
        return [i for i in self.intersections if i.color == "white"]

    @cached_property
    def black_stones(self):
        "intersection data for each intersection with a black stone on it"
        return [i for i in self.intersections if i.color == "black"]

    @cached_property
    def stones(self):
        "intersection data for each intersection with a stone on it"
        return [i for i in self.intersections if i.color != "empty"]

    @cached_property
    def empties(self):
        "intersection data for each empty point on the board"
        return [i for i in self.intersections if i.color == "empty"]

    @cached_property
    def intersections(self):
        "intersection data for every intersection on the board"
        return [i for i in self._intersections if not isPass(i.pos)]
    
    @cached_property
    def allowed_moves(self):
        if self._allowedMoves == None: # means full-board analysis
            return self.legal_moves
        else:
            return [a for a in self.legal_moves if a.pos  in self._allowedMoves]

    @cached_property
    def played_moves(self):
        "list of (color, intersection info) corresponding to the moves made"
        oq = self.answer['originalQuery']
        if 'moves' in oq and len(oq['moves']) > 0:
            return [ ( same_color(m[0]), self.get_point(coordsToPoint(m[1]))) for m in oq['moves']]
        else:
            return []

    @cached_property
    def initial_stones(self):
        "list of stones initially placed on the board before moves were made"
        oq = self.answer['originalQuery']
        if 'initialStones' in oq and len(oq['initialStones']) > 0:
            return [ (same_color(m[0]), self.get_point(coordsToPoint(m[1]))) for m in oq['initialStones']]
        else:
            return []
    
    @cached_property
    def lastMove(self):
        p = self.played_moves
        if len(p):
            return p[-1]
    @property
    def pass_move(self):
        return self.get_point ( (-1,-1,))
    
    def get_point(self, gopoint: tuple) -> dotdict:
        "fetch intersection data by integer tuple, e.g. (3,3)"
        return self._intersections_by_point[gopoint]
    
    def point(self, x:int, y:int) -> dotdict:
        "easier to type in a script"
        return self.get_point((x,y,))
    
    def _buildIntersections(self):
        # OK so most of this junk is to
        # reshape the katago answer into something
        # easy to work with in a python script
        self._intersections = []
        self._intersections_by_point = {}

        xsize = self.answer['originalQuery']['boardXSize']
        ysize = self.answer['originalQuery']['boardYSize']
        toPlay = self.answer['stats']['toPlay']

        self.xsize = xsize
        self.ysize = ysize

        allowedMoves = None

        #FIXME: the allowed moves are assumed to be for color to play and only first move
        if 'allowMoves' in self.answer['originalQuery']:
            # dig into the structure
            allowedMoves = set()
            for m in self.answer['originalQuery']['allowMoves'][0]['moves']:
                allowedMoves.add(coordsToPoint(m))
        
            if len(allowedMoves) == 0: allowedMoves = None

        # note: this is a custom field so can cause probs
        blacks = [] ; whites = []
        if 'black_stones' in self.answer['originalQuery']:
            blacks = self.answer['originalQuery']['black_stones']
        
        if 'white_stones' in self.answer['originalQuery']:
            whites = self.answer['originalQuery']['white_stones']

        intersectionsDict = {}

        # munge for every intersection
        for i in range(xsize*ysize+1): # include pass
            x,y = i % xsize, i // xsize
            y = ysize - y - 1 # unfortunately policy/ownership info is flipped vertically
            notpass = i < xsize*ysize

            info = {}

            # set color
            if (x,y,) in blacks:
                info['color'] = "black"
            elif (x,y,) in whites:
                info['color'] = "white"
            else:
                info['color'] = "empty"

            # policy for this intersection
            info['policy'] = self.answer['policy'][i]
            
            
            # OWNERSHIP INFO
            # provide different perspectives for convenience
            if notpass:
                info['ownership'] = self.answer['ownership'][i]
            else:
                info['ownership'] = 0.0
            
            if info['policy'] < 0:
                info['legal'] = False
            else:
                info['legal'] = True


            if toPlay == "white":
                o = info['ownership']
                info['ownershipWhite'] = o
                info['ownershipBlack'] = -o
                info['ownershipHeat'] = 1 - (o+1)/2
                info['ownershipOpponent'] = info['ownershipBlack']
            else:
                o = info['ownership']
                info['ownershipBlack'] = o
                info['ownershipWhite'] = -o
                info['ownershipHeat'] = (o+1)/2
                info['ownershipOpponent'] = info['ownershipWhite']

            # when isMove == True, there is additional moveInfo 
            info['isMove'] = False

            # position as int tuple
            info['pos'] = (x,y,)

            # coords is a go coordinate string, e.g. 'K10'
            if notpass:
                info['coords'] = pointToCoords((x,y,))
            else:
                info['coords'] = "pass"

            # allow scripts to know if this intersection is "allowed" in analysis
            # FIXME: this should munge the avoid field too
            info['allowedMove'] = False
            if allowedMoves == None or info['pos'] in allowedMoves:
                info['allowedMove'] = True

            # store it in our temporary dictionary of points
            if notpass:
                intersectionsDict[(x,y)] = dotdict(info)
            else:
                info['pos'] = (-1,-1)
                intersectionsDict[(-1,-1)] = dotdict(info)


        # MUNGE MORE INFORMATION FOR SUGGESTED MOVES        
        for m in self.answer['moveInfos']:
            point = coordsToPoint(m['move'])
            d = intersectionsDict[point]
            d['isMove'] = True

            # convert pv coordinates to numerical coords
            d['pvPos'] = []
            for coord in m['pv']:
                d['pvPos'].append(coordsToPoint(coord))

            # grab the moveInfos from Katago and
            # copy verbatim
            for key in m:
                d[key] = m[key]


            # insert more perspectives for convenience
            if toPlay ==  "black": 
                me = "Black" ; other = "White"
            else:
                me = "White" ; other = "Black"

            d['scoreLead' + me] = d['scoreLead']
            d['scoreSelfplay' + me] = d['scoreSelfplay']
            d['winrate' + me] = d['winrate']
            d['scoreMean' + me] = d['scoreMean']

            for who in [other, 'Opponent']:
                d['scoreLead' + who] = -d['scoreLead']
                d['scoreSelfplay' + who] = -d['scoreSelfplay']
                d['winrate' + who] = 1.0 -d['winrate']
                d['scoreMean' + who] = -d['scoreMean']

            # wrap it up in a dict that can be accessed by dot notation
            intersectionsDict[point] = dotdict(d)

        self._allowedMoves = allowedMoves

        # sort so that lower left is first and top right is last
        lst = [p for p in intersectionsDict.values()]

        self._intersections = sorted(lst, key=lambda p: p.pos[1]*1000 + p.pos[0], reverse=False)
        
        # and some random access by gopoint if needed
        self._intersections_by_point = intersectionsDict
    
def moreKataData(kataAnswer: dict):
    "put some extra stats inside the dict for easy access"
    morestuff = {}

    morestuff['toPlay'] = "black" 

    if "originalQuery" in kataAnswer:
        q = kataAnswer['originalQuery']
        if 'komi' in q:
            morestuff['komi'] = q['komi']
        
        #determine color to play
        if 'moves' in q and len(q['moves']) > 0:
            morestuff['toPlay'] = other_color(q['moves'][-1][0])
        elif 'initialPlayer' in q:
            c = q['initialPlayer']
            if c[0].upper() == "B":
                c = "black"
            else:
                c = "white"
            
            morestuff['toPlay'] = c

        morestuff['xsize'] = q['boardXSize']
        morestuff['ysize'] = q['boardYSize']
        
    if "moveInfos" in kataAnswer and len(kataAnswer['moveInfos']) > 0:
        # and... probably put more stats here

        winrates = []
        scoreleads = []
        finalscores = []
        
        for m in kataAnswer['moveInfos']:
            winrates.append(m['winrate'])
            scoreleads.append(m['scoreLead'])
            finalscores.append(m['scoreSelfplay'])


        morestuff['winrateMax'] = max(winrates)
        morestuff['winrateMin'] = min(winrates)
        morestuff['winrateMedian'] = median(winrates)
        morestuff['winrateAvg'] = mean(winrates)

        morestuff['scoreLeadMax'] = max(scoreleads)
        morestuff['scoreLeadMin'] = min(scoreleads)
        morestuff['scoreLeadMedian'] = median(scoreleads)
        morestuff['scoreLeadAvg'] = mean(scoreleads)
        
        morestuff['scoreSelfplayMax'] = max(finalscores)
        morestuff['scoreSelfplayMin'] = min(finalscores)
        morestuff['scoreSelfplayMedian'] = median(finalscores)
        morestuff['scoreSelfplayAvg'] = mean(finalscores)

        #convenience:
        r = kataAnswer['rootInfo']
        # FIXME scoreSelfplay at rootInfo is actually different
        # from at the best move, and I should honor this
        morestuff['scoreSelfplay'] = r['scoreSelfplay']
        morestuff['winrate'] = r['winrate']
        morestuff['scoreLead'] = r['scoreLead']
        morestuff['visits'] = r['visits']


        #construct info from black, white and opponent perspective
        tp = morestuff['toPlay']
        other = "White"
        if tp[0].upper() ==  "B": 
            me = "Black" ; other = "White"
        else:
            me = "White" ; other = "Black"

        
        for tag in ['', 'Max', 'Min', "Median", "Avg"]: 
            morestuff['scoreSelfplay' +  tag + me] = morestuff['scoreSelfplay'+tag]
            morestuff['winrate'+ tag + me] = morestuff['winrate'+tag]
            morestuff['scoreLead' + tag + me] = morestuff['scoreLead'+tag]

            for who in [other, "Opponent"]:
                # "Opponent" is for convenience when you don't care/know who i am
                morestuff['scoreSelfplay' + tag + who] = -morestuff['scoreSelfplay'+tag]
                morestuff['winrate'+ tag + who] = 1.0 - morestuff['winrate'+tag]
                morestuff['scoreLead'+ tag + who] = -morestuff['scoreLead'+tag]

    d = dict(kataAnswer)
    d.update ({"stats": morestuff})
    return d

"""
Board Position:
{
    boardXSize: 9,
    boardYSize: 9,
    initialStones: [["B" "C3"] ["W", "E5"] ...], # can be []
    moves: [["B", "C6"]... ] # can be []
}
"""

class KataProxyQ(QObject):
    "a proxy for katago that uses Qt"
    loginfo = pyqtSignal(str)
    #answerReady = pyqtSignal(str) # provides the id of the answer that is ready 
    def __init__(self, cmd, model, config):
        super().__init__()
        self.buffer = ""
        self.answers = {} # received answers dicts by id
        self.queries = {} # sent queries dicts by id
        
        self.quickVisits = 1
        self.fullVisits = 10

        KataSignals.askForAnalysis.connect(self.ask)
        KataSignals.claimAnswer.connect(self.claimAnswer)
        self._startup(cmd, model, config)

    def _startup(self, cmd, model, config):
        self.cmd = cmd
        self.model = model
        self.config = config

        kataargs = ["analysis", "-model", model, "-config", config, "-analysis-threads", KATATHREADS]

        self.kata = QProcess()
        #self.kata.setProcessChannelMode(QProcess.ForwardedErrorChannel)
        self.kata.setProcessChannelMode(QProcess.SeparateChannels)
        #self.kata.setReadChannel(QProcess.StandardOutput)

        self.kata.readyReadStandardOutput.connect(self._readStdout)
        self.kata.readyReadStandardError.connect(self._readStderr)

        hookQuit = True
        try:
            PyQt5.QtWidgets
        except AttributeError:
            hookQuit = False
    
        if hookQuit: # it's a gui
            PyQt5.QtWidgets.QApplication.instance().aboutToQuit.connect(self.kata.kill) #TODO: "terminate" hangs so i have to kill, why?
        
        self.isGui = hookQuit
        self.kata.start(cmd, kataargs)
        self.kata.waitForStarted()
        
        # block until katago is ready:
        res = self.analyze({"id": "wait for startup", "action": "query_version"})
        #eprint(f"KATAGO STARTED {res}")

    def _kill(self):
        "oddly katago has no means of gracefully quitting"
        if self.kata:
            self.kata.kill()

    def restart(self, cmd=None, model=None, config=None):
        if cmd == None: cmd = self.cmd
        if model == None: model = self.model
        if config == None: config = self.config

        self._kill()
        self._startup(cmd, model, config)

    def ask(self, query: dict, cached=False):
        orig = dict(query)
        orig['proxy_cached'] = cached
        #eprint(f"CACHED IS {orig['proxy_cached']}")

        self.queries[query['id']] = orig
        q = json.dumps(orig) + "\n"
        #eprint("JSON: ", q)
        self.kata.write(q.encode("utf-8"))
        #QCoreApplication.instance().processEvents()

    def _askBlocking(self, query: dict) -> dict:
        self.ask(query, cached=True)
        return self.getAnswer(query['id'])
    
    def haveAnswer(self, id: str) -> bool:
        return id in self.answers

    def getAnswer(self, id: str):
        #eprint(f"ANSWER REQUESTED: {id}, current answer size: {len(self.answers)}, query size: {len(self.queries)}")
        if id not in self.queries:
            raise ValueError(f"KataProxy: Cannot get answer for non-existing query id '{id}'")
        count = 0
        while True:
            if count % 100 == 0:
                pass #eprint(f"Count: {count}")
            
            if id in self.answers:
                result = dict(self.answers[id])
                # add original query to result for later use
                result.update({"originalQuery": dict(self.queries[id])})
                del self.answers[id]
                del self.queries[id]
                return result
            else:
                #self._readStdout()
                #QCoreApplication.instance().processEvents()
                if self.kata.waitForReadyRead(0): #trigger signal without doing recursive processEvent()
                    self._readStdout()
                #self.kata.readyRead.emit()
            count +=1
    def claimAnswer(self, id: str) -> None:
        "remove this answer from my cache"
        if id in self.queries:
            del self.queries[id]
        
        if id in self.answers:
            del self.answers[id]

    def answerToPD(self, answer: str):
        """
        provides a many-columned flat df for all intersections.
        Global stuff (like rules & current move number) are repeated for each intersection
        """
        oq = answer['originalQuery']
        istones = oq['initialStones']
        #eprint(f"Initial stones: {istones}")
        initialStones = {}
        for s in istones:
            initialStones[s[1]] = s[0] # e.g. 'Q4' = "B"

        
        xs = oq['boardXSize']
        ys = oq['boardYSize']

        general = {}
        for k in ['boardXSize', 'boardYSize', 'rules', 'maxVisits']:
            general[k] = [oq[k]] * xs*ys
        
        # TODO: handle all the stuff in anwer['rootInfo'] somehow

        for k in ['symHash', 'thisHash']:
            general[k] = [answer['rootInfo'][k]] * xs*ys


        #eprint("ownership size:", len(answer['ownership']))
        ownershipflat = np.array(answer['ownership'])
        policiesflat =  np.array(answer['policy'][:-1]) # skip the pass policy value for now (should be separate IMO)

        eprint("np ownership size:", len(ownershipflat))

        ownership = ownershipflat.reshape(xs, ys)
        policies = policiesflat.reshape(xs, ys)

        #eprint("BUILD INFO")
        columns = {'x': [], 'y': [], 'coord': []}
        moveSchema ={}
        for c in answer['moveInfos'][0].keys():
            if c != "move": # already covered by "coord"
                columns[c] = []
                moveSchema[c] = True

        columns['ownership'] = []
        columns['policy'] = []


        infosByCoord = {}
        for i in answer['moveInfos']:
            infosByCoord[i['move']] = i

        for x in range (xs):
            for y in range(ys):
                columns['x'].append(x)
                columns['y'].append(y)
                columns['coord'].append(pointToCoords((x,y)))
                move = pointToCoords((x,y))

                if move in infosByCoord:
                    for c,v in infosByCoord[move].items():
                        #eprint(f"Col: {c} Val: {v}")
                        if c != "move": # already covered by "coord"
                            columns[c].append(v)
                else:
                    for c,v in moveSchema.items():
                        #eprint(f"Col: {c} Val: {v}")
                        if c not in ["move", "order"]: # already covered by "coord"
                            columns[c].append(0) #FIXME should be something sensible
                        else:
                            columns['order'].append(float('inf'))
                columns['ownership'].append(ownership[x,y])
                columns['policy'].append(policies[x,y])

        columns.update(general)
        result = pd.DataFrame(columns)
        return result

    def analyzePANDA(self, query: dict):
        return self.answerToPD(self.analyze(query))

    def analyze(self, query: dict):
        return self._askBlocking(dict(query))
    
    def queueDepth(self):
        return len(self.queries) - len(self.answers)
        
    def _readStdout(self):
        # have to make my own line reader because readyRead()/readline() acts irrational
        #eprint("Read STDOUT")
        b = self.kata.bytesAvailable()
        if b > 0:
            self.buffer = self.buffer + str(self.kata.readAllStandardOutput(), "utf-8")
            lines = self.buffer.split('\n')
            #eprint(lines)
            if self.buffer[-1] == '\n':
                self.buffer = ""
                for l in lines:
                    if len(l): self._processLine(l)
            else:
                self.buffer = lines[-1]
                for l in lines[:-1]:
                    if len(l): self._processLine(l)
    def _readStderr(self):
        b = str(self.kata.readAllStandardError(), 'utf-8')
        KataSignals.stderrPrinted.emit(b)
        print(b, end='', file=sys.stderr)

    def _processLine(self, line: str):
        j = json.loads(line)
        #eprint(f"KATAGO RESPONDED: {j['id']}")
        self.answers[j['id']] = j
        orig = self.queries[j['id']]
        j['originalQuery'] = dict(orig)

        if 'proxy_cached' in orig and not orig['proxy_cached']:
            del self.queries[j['id']]
            del self.answers[j['id']]

        #KataSignals.answerReady.emit(j['id'])
        KataSignals.answerFinished.emit(j)



if __name__ == "__main__":
    #print("YOU ARE IN MAIN")
    from statistics import mean
    import traceback
    
    def trap_exc_during_debug(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        traceback.print_tb(exc_traceback)
        eprint(exc_type, exc_value, exc_traceback)

        # when app raises uncaught exception, print info
        #print(args)

    
    sys.excepthook = trap_exc_during_debug

    app = QCoreApplication(sys.argv)
    queryTemplate = {
        "boardXSize": 19,
        "boardYSize": 19,
        "id": "hehe",
        "initialStones": [["B", "Q4"], ["B", "C4"]],
        "moves": [],
        "rules": "Chinese",
        "maxVisits": 10,
        "includeOwnership": True,
        "includePolicy": True,
        "includePVVisits": True
    }

    eprint("CREATE")
    eprint(KATACMD)

    kata = KataProxyQ(KATACMD, KATAMODEL, KATACONFIG)

    try: 
        kata.getAnswer("produceError")
    except ValueError as e:
        eprint("YUP, got ValueError: ", e)


    start = time.perf_counter()
    kata.analyze(queryTemplate)
    first_elapsed = time.perf_counter() - start

    if False:
        eprint("TRYING TO RESTART")
        kata.restart(KATACMD, KATAMODEL, KATACONFIG)

        eprint("RESTARTING AGAIN")
        kata.restart()

    times = []
    for x in range(1):
        query = dict(queryTemplate)
        query['id'] = "trial " + str(x)
        query['maxVisits'] = 10+ x * 10
        #eprint(query['id'])
        start = time.perf_counter()
        kata.analyzePANDA(dict(query))
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    eprint (f"First run time: {first_elapsed}")
    eprint (f"after elapsed: {mean(times)}")


    import random
    # play some moves
    movelist = []
    toPlay = "B"
    for x in range(80):
        query = dict(queryTemplate)
        query['id'] = "play" + str(x)
        query['maxVisits'] = 5
        query['moves'] = movelist
        answer = kata.analyze(dict(query))
        k = KataAnswer(answer)
        theMove = k.moves[0]
        movelist.append([toPlay, theMove.coords])
        if toPlay == "W": toPlay = "B"
        else: toPlay = "W"

    #eprint("MOVES: ", movelist)

    #simulate an async request / answer
    kata.ask(query, cached=True)
    answer = kata.getAnswer(query['id'])

    eprint ("CONVERT TO PD")
    df = kata.answerToPD(answer)

    eprint(df)

    eprint (df.loc[df['x'] == 3])
    eprint (df.loc[df['visits'] == 0][['coord', 'policy', 'visits', 'order']])
    eprint(df.columns)
    eprint(df.dtypes)
    eprint("movelist: ", movelist)
    eprint ("AND... THAT's IT.")

    sgf = "(;GM[1]FF[4]CA[UTF-8]"
    #sgf += f"PL[{k.toPlay[0].upper()}]"

    letters = 'abcdefghijklmnopqrstuvwxyz'
    for m in movelist:
        pos = coordsToPoint(m[1])
        coord = letters[pos[0]] + letters[pos[1]]
        if m[0] == "W":
            sgf += f";W[{coord}]"
        else:
            sgf += f";B[{coord}]"

    sgf += ")"

    print(sgf)
    app.exit()

