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
            raise NotImplementedError('Not yet implemented')
        elif Indexer.compress == "variablebyte":
            raise NotImplementedError('Not yet implemented')
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
    pl = idx.get_postings(5000)
    print(pl)
