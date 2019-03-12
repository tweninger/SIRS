from index.documents import Fields, Field
from index.indexer import Indexer
from definitions import ROOT_DIR
from bitarray import bitarray
import os, struct


class InvertedIndex:
    class __InvertedIndex:
        __IDX = os.path.join(ROOT_DIR, 'data/idx.txt')
        __IDXTERMOFFSET = os.path.join(ROOT_DIR, 'data/idx_term_offset.txt')

        def __init__(self):
            self.offsets = self.__load_offsets()
            self.__load_fields()
            self.idx = self.__IDX
            pass

        def __load_offsets(self):
            __offsets = []
            with open(self.__IDXTERMOFFSET) as r:
                r.readline() #throw away first line
                for line in r:
                    __offsets.append(int(line))
            return __offsets

        def __load_fields(self):
            with open(self.__IDX, 'rb') as idx:
                field_string = idx.readline().decode('utf8').strip()
                Fields.load_from_inverted_index(field_string)

        def __str__(self):
            return repr(self)

    instance = None

    def __init__(self):
        if not InvertedIndex.instance:
            InvertedIndex.instance = InvertedIndex.__InvertedIndex()
        else:
            pass

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def get_postings(self, term_id):
        """

        :param term_id:
        :return:
        """
        offset = self.offsets[term_id]
        postinglist = None
        if Indexer.compress == 'gamma':
            postinglist = PostingList()
            with open(self.idx, 'rb') as idx:
                idx.seek(offset)
                term_id, = struct.unpack('i', idx.read(4))
                postinglist.term_id = term_id
                for fi in range(3):
                    doc = -1
                    freq = -1
                    cur_doc = 0
                    hash, = struct.unpack('s', idx.read(1))
                    if hash.decode('utf8') != '#':
                        raise ValueError('Weve done something wrong')
                    field, = struct.unpack('b', idx.read(1))
                    postinglist.postings[field] = list()
                    leng, = struct.unpack('i', idx.read(4))
                    i=0
                    unary=True
                    unary_leng = 0
                    offset = list()
                    while i < leng:
                        bite, = struct.unpack('B', idx.read(1))
                        bitlist = [int(x) for x in bin(bite)[2:]]
                        bitlist = (8 - len(bitlist)) * [0] + bitlist
                        #give me gamma
                        for _, bit in enumerate(bitlist):

                            if (not unary) or (unary and unary_leng == 0 and bit == 0):

                                if unary_leng > 0:
                                    offset.append(bit)
                                    unary_leng -= 1

                                if unary_leng == 0:
                                    offset = [1] + offset
                                    out = 0
                                    for b in offset:
                                        out = (out << 1) | b
                                    if doc == -1:
                                        doc = cur_doc + out
                                        offset = list()
                                        unary = True
                                    else:
                                        freq = out
                                        post = Posting(term_id, doc, freq)
                                        postinglist.postings[field].append(post)
                                        cur_doc = doc
                                        offset = list()
                                        doc = -1
                                        freq = -1
                                        i += 1
                                        if i >= leng:
                                            break

                                        unary = True
                            else:
                                # count till 0
                                if bit == 0:
                                    unary = False
                                else:
                                    unary_leng += 1
        elif Indexer.compress == "variablebyte":
            postinglist = PostingList()
            with open(self.idx, 'rb') as idx:
                idx.seek(offset)
                term_id, = struct.unpack('i', idx.read(4))
                postinglist.term_id = term_id
                for fi in range(3):
                    doc = -1
                    freq = -1
                    cur_doc = 0
                    hash, = struct.unpack('s', idx.read(1))
                    if hash.decode('utf8') != '#':
                        raise ValueError('Weve done something wrong')
                    field, = struct.unpack('b', idx.read(1))
                    postinglist.postings[field] = list()
                    leng, = struct.unpack('i', idx.read(4))
                    i = 0
                    for i in range(0,leng):
                        bite, = struct.unpack('B', idx.read(1))
                        bitlist = [int(x) for x in bin(bite)[2:]]
                        bitlist = (8 - len(bitlist)) * [0] + bitlist
                        bites = list()
                        bites.extend(bitlist[1:])
                        while bitlist[0] == 1:
                            # more to get
                            bite, = struct.unpack('B', idx.read(1))
                            bitlist = [int(x) for x in bin(bite)[2:]]
                            bitlist = (8 - len(bitlist)) * [0] + bitlist

                            bites.extend(bitlist[1:])
                        out = 0
                        for b in bites:
                            out = (out << 1) | b
                        doc = out + cur_doc
                        cur_doc = doc

                        bite, = struct.unpack('B', idx.read(1))
                        bitlist = [int(x) for x in bin(bite)[2:]]
                        bitlist = (8 - len(bitlist)) * [0] + bitlist
                        bites = list()
                        bites.extend(bitlist[1:])
                        while bitlist[0] == 1:
                            # more to get
                            bite, = struct.unpack('B', idx.read(1))
                            bitlist = [int(x) for x in bin(bite)[2:]]
                            bitlist = (8 - len(bitlist)) * [0] + bitlist

                            bites.extend(bitlist[1:])
                        out = 0
                        for b in bites:
                            out = (out << 1) | b
                        freq = out
                        post = Posting(term_id, doc, freq)
                        postinglist.postings[field].append(post)
        elif Indexer.compress == "none":
            with open(self.idx, 'r', newline='\n') as idx:
                idx.seek(offset)
                line = idx.readline().strip()
                if line is None or len(line) == 0:
                    raise Exception('Something wrong reading posting')
                postinglist = PostingList(line)
                if term_id != postinglist.term_id:
                    raise Exception('Cannot read termid in postings list')
        return postinglist


class PostingList:
    def __init__(self, postings_line=''):
        self.postings = dict()
        self.term_id = -1
        if postings_line == '':
            return

        s = postings_line.split('\t')
        self.term_id = int(s[0])

        fields = s[1].split('#')
        for f in fields:
            if len(f.strip()) == 0: continue
            posts = list()
            if '(' not in f:
                self.postings[int(f)] = posts
            else:
                idx = str(f).index('(')
                field = Field(int(f[:idx]))
                pl = f[idx:].split(';')
                for p in pl:
                    p = p[1:-1]
                    x = p.split(',')
                    doc = int(x[0])
                    frequency = int(x[1])
                    post = Posting(self.term_id, doc, frequency)
                    posts.append(post)
                self.postings[field.field] = posts

    def __str__(self):
        return '(' + str(self.term_id) + ')'

    def size(self, field):
        return len(self.postings[field])


class Posting:
    def __init__(self, term_id, doc, frequency):
        self.term_id = term_id
        self.doc = doc
        self.frequency = frequency


if __name__ == "__main__":
    idx = InvertedIndex()
    pl = idx.get_postings(1)
    print(pl)
