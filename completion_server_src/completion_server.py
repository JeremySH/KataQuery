# -*- coding: utf-8 -*-
"""
Main server script for a pyqode.python backend. You can directly use this
script in your application if it fits your needs or use it as a starting point
for writing your own server.

::

    usage: server.py [-h] [-s [SYSPATH [SYSPATH ...]]] port

    positional arguments:
      port                  the local tcp port to use to run the server

    optional arguments:
      -h, --help            show this help message and exit
      -s [SYSPATH [SYSPATH ...]], --syspath [SYSPATH [SYSPATH ...]]

"""

from pyqode.core import backend
import pyqode.python.backend.workers

# patch a bug, where in some cases ICON_TYPE is "unimplemented" and ejects
# a zillion warnings that I don't care about
pyqode.python.backend.workers.icon_from_typename = lambda x,y: None
from pyqode.python.backend.workers import JediCompletionProvider

class MultiProvider(object):
    "completion providers that are additive instead of replacing"
    def __init__(self):
        self.providers = [JediCompletionProvider(), backend.DocumentWordsProvider(), KataQueryProvider()]

    def complete(self, code, line, column, path, encoding, prefix, wtf):
        result = []
        for p in self.providers:
            l = p.complete(code, line, column, path, encoding, prefix, wtf)
            if l:
                result.extend(l)

        yup = set()
        done = []
        for r in result:
            if len(r['name']) < 4:
                continue

            if r['name'] not in yup:
                if 'icon' in r:
                    del r['icon'] # icons are so 1990s
                yup.add(r['name'])
                done.append(r)
        return done

_kataqueryWords_k =[
"all",
"allowed_moves",
"answer",
"avg",
"bestMove",
"black_stones",
"cached_property",
"currentPlayer",
"dataframe",
"depth",
"empties",
"filter",
"filterv",
"get_point",
"goban",
"gui_run",
"illegal_moves",
"initial_stones",
"intersections",
"komi",
"last_move",
"legal_moves",
"manual_run",
"map",
"max",
"max_policy",
"merged_moves",
"min",
"min_policy",
"moves",
"moves_by_policy",
"pass_move",
"played_moves",
"player",
"point",
"policy_range",
"query_points",
"rawStScoreError",
"rawStWrError",
"rawVarTimeLeft",
"reduce",
"rootInfo_dataframe",
"scoreLead",
"scoreLeadAvg",
"scoreLeadAvgBlack",
"scoreLeadAvgOpponent",
"scoreLeadAvgWhite",
"scoreLeadBlack",
"scoreLeadMax",
"scoreLeadMaxBlack",
"scoreLeadMaxOpponent",
"scoreLeadMaxWhite",
"scoreLeadMedian",
"scoreLeadMedianBlack",
"scoreLeadMedianOpponent",
"scoreLeadMedianWhite",
"scoreLeadMin",
"scoreLeadMinBlack",
"scoreLeadMinOpponent",
"scoreLeadMinWhite",
"scoreLeadOpponent",
"scoreLeadWhite",
"scoreSelfplay",
"scoreSelfplayAvg",
"scoreSelfplayAvgBlack",
"scoreSelfplayAvgOpponent",
"scoreSelfplayAvgWhite",
"scoreSelfplayBlack",
"scoreSelfplayMax",
"scoreSelfplayMaxBlack",
"scoreSelfplayMaxOpponent",
"scoreSelfplayMaxWhite",
"scoreSelfplayMedian",
"scoreSelfplayMedianBlack",
"scoreSelfplayMedianOpponent",
"scoreSelfplayMedianWhite",
"scoreSelfplayMin",
"scoreSelfplayMinBlack",
"scoreSelfplayMinOpponent",
"scoreSelfplayMinWhite",
"scoreSelfplayOpponent",
"scoreSelfplayWhite",
"scoreStdev",
"sorted",
"stones",
"sum",
"symHash",
"takeuntil",
"takewhile",
"thisHash",
"toPlay",
"utility",
"visits",
"weight",
"white_stones",
"winrate",
"winrateAvg",
"winrateAvgBlack",
"winrateAvgOpponent",
"winrateAvgWhite",
"winrateBlack",
"winrateMax",
"winrateMaxBlack",
"winrateMaxOpponent",
"winrateMaxWhite",
"winrateMedian",
"winrateMedianBlack",
"winrateMedianOpponent",
"winrateMedianWhite",
"winrateMin",
"winrateMinBlack",
"winrateMinOpponent",
"winrateMinWhite",
"winrateOpponent",
"winrateWhite",
"xsize",
"ysize",

]

_kataqueryWords = [
    "help",
    "helptext",
    "status",
    "mark",
    "ghost",
    "clearMarks",
    "clearHeat",
    "clearStatus",
    "clearGhosts",
    "hover",
    "clearHovers",
    "clearAll",
    "opponent",
    "heat",
    "havek",
    "quickPlay",
    "analyze",
    "rerun",
    "set_clipboard",
    "get_clipboard",
    "log",
    "clearLog",
    "msgBox",
    "chooseFile",
    "bail",
    "dist",
    "snooze",
    "bookmark",
    "KataGoQueryError",

    "color",
    "policy",
    "ownership",
    "legal",
    "ownershipWhite",
    "ownershipBlack",
    "ownershipHeat",
    "ownershipOpponent",
    "isMove",
    "pos",
    "coords",
    "allowedMove",
    "pvPos",
    "lcb",
    "move",
    "order",
    "prior",
    "pv",
    "pvEdgeVisits",
    "pvVisits",
    "scoreLead",
    "scoreMean",
    "scoreSelfplay",
    "scoreStdev",
    "utility",
    "utilityLcb",
    "visits",
    "weight",
    "winrate",
    "scoreLeadWhite",
    "scoreSelfplayWhite",
    "winrateWhite",
    "scoreMeanWhite",
    "scoreLeadBlack",
    "scoreSelfplayBlack",
    "winrateBlack",
    "scoreMeanBlack",
    "scoreLeadOpponent",
    "scoreSelfplayOpponent",
    "winrateOpponent",
    "scoreMeanOpponent",
    "mergedOrder",
]

class KataQueryProvider(object):
    "provide code completion for kataquery-specific words"
    def __init__(self):
        self.word2word = {}
        self.word2word_k = {}

        for w in _kataqueryWords:
            self.addWord(w, self.word2word)

        for w in _kataqueryWords_k:
            self.addWord(w, self.word2word_k)

    def addWord(self, word, dictionary):
        # build a rudimentary tree of partial words
        for x in range(1, len(word)+1):
            prefix = word[:x].lower()
            if prefix in dictionary:
                dictionary[prefix].append({"name": word})
            else:
                dictionary[prefix] = [{"name": word}]

    def complete(self, code, line, column, path, encoding, prefix, wtf):

        # sigh...
        lines = code.splitlines()
        myline = lines[line]

        lowerc = prefix.lower()

        # treat "k." specially to provide k related terms
        if column > 1 and myline[column-2:column] == "k.":
            if lowerc in self.word2word_k:
                return self.word2word_k[lowerc]

        if lowerc in self.word2word:
            return self.word2word[lowerc]
        return []

if __name__ == '__main__':
    """
    Server process' entry point
    """
    import argparse
    import logging
    import sys    

    logging.basicConfig()
    # setup argument parser and parse command line args
    parser = argparse.ArgumentParser()
    parser.add_argument("port", help="the local tcp port to use to run "
                        "the server")
    parser.add_argument('-s', '--syspath', nargs='*')
    args = parser.parse_args()

    #print("PATH", sys.path, file=sys.stderr)
    # add user paths to sys.path
    if args.syspath:
        for path in args.syspath:
            print('append path %s to sys.path' % path)
            sys.path.append(path)


    # setup completion providers
    # not useful as one module's completions will override another
    #backend.CodeCompletionWorker.providers.append(KataQueryProvider())
    #backend.CodeCompletionWorker.providers.append(JediCompletionProvider())
    #backend.CodeCompletionWorker.providers.append(backend.DocumentWordsProvider())

    # get all possible completions from all providers:
    backend.CodeCompletionWorker.providers.append(MultiProvider())
    
    # starts the server
    backend.serve_forever(args)
