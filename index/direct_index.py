from index.documents import Field, HTMLDocument
from definitions import ROOT_DIR

import os

class DirectIndex:
    class __DirectIndex:
        __DOCIDX = os.path.join(ROOT_DIR, 'data/doc_idx.txt')
        __DOCIDXOFFSET = os.path.join(ROOT_DIR, 'data/doc_idx_offset.txt')

        def __init__(self):
            self.offsets = self.__load_offsets()
            self.field_counts = self.__count_tokens()
            pass

        def __load_offsets(self):
            __offsets = []
            with open(self.__DOCIDXOFFSET) as r:
                for line in r:
                    __offsets.append(int(line))
            return __offsets

        def __count_tokens(self):
            field_counts = dict()
            temp_fields = dict()
            with open(self.__DOCIDX, 'rb') as r:
                # eg: 0:398, 2: 4, 1: 4
                for line in r:
                    cols = line.split(bytes('\t', encoding='utf-8'))
                    lens = cols[2].split(bytes(',', encoding='utf-8'))
                    for __len in lens:
                        x = __len.split(bytes(':', encoding='utf-8'))
                        k = int(x[0])
                        v = int(x[0])
                        if k not in temp_fields:
                            temp_fields[k] = Field(k)
                            field_counts[temp_fields[k].field] = v
                        else:
                            field_counts[temp_fields[k].field] += v
            return field_counts

        def get_num_docs(self):
            return len(self.offsets)

        def get_doc(self, docid):
            offset = self.offsets[docid]
            with open(self.__DOCIDX, 'rb') as r:
                r.seek(offset)
                line = r.readline().decode('utf-8').strip()
                return HTMLDocument(docid, line=line, file=None)

        def __str__(self):
            return repr(self)

    instance = None

    def __init__(self):
        if not DirectIndex.instance:
            DirectIndex.instance = DirectIndex.__DirectIndex()
        else:
            pass

    def __getattr__(self, name):
        return getattr(self.instance, name)

