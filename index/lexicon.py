from definitions import ROOT_DIR

import os

class Lexicon:
    class __Lexicon:
        __LEXICON = os.path.join(ROOT_DIR, 'data/lex.txt')
        def __init__(self):
            self.lex = open(self.__LEXICON, 'r')
            self.lex.seek(0,2)
            self.length = self.lex.tell()

    instance = None

    def __init__(self):
        if not Lexicon.instance:
            Lexicon.instance = Lexicon.__Lexicon()
        else:
            pass

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def get_term_id(self, term):
        low = 0
        high = self.length
        cur = high
        x = -3
        while x < 0:
            if high - low < 200:
                return self.scan_to_find(low, high, term)
            if x == -3:
                cur = low + (high - low) / 2
            elif x == -1:
                cur = low + (high - low) / 2
            x = self.compare_to(cur, term)
            if x >= 0:
                return x
            elif x == -3:
                low = cur
            else:
                high = cur

        return -1

    def scan_to_find(self, pos, high, term):
        if pos < 200:
            pos = 0
        self.lex.seek(pos)
        l = self.lex.readline()

        l = self.lex.readline()
        while l is not None :
            line = l.split('\t')
            if line[0] == term:
                return int(line[1])
            if self.lex.tell() > high:
                return -1
            l = self.lex.readline()

    def compare_to(self, pos, term):
        self.lex.seek(pos)
        self.lex.readline() #go to the end of the line
        line = self.lex.readline().split('\t')
        if line[0] == term:
            return int(line[1])
        else:
            if line[0] < term:
                return -3
            else:
                return -1


if __name__ == "__main__":
    lex = Lexicon()
    print(lex.get_term_id('Web'))
