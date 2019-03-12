from index.documents import HTMLDocument, Fields, Field, Token
from index.pagerank import PageRank
from numpy import random as rnd
from urllib.parse import quote
from operator import attrgetter
from definitions import ROOT_DIR
from bitarray import bitarray
import os
import heapq
import sys
import tarfile
import struct


class Indexer:
    doc_idx = os.path.join(ROOT_DIR, 'data/doc_idx.txt')
    doc_idx_offset = os.path.join(ROOT_DIR, 'data/doc_idx_offset.txt')
    lexicon = os.path.join(ROOT_DIR, 'data/lex.txt')
    runs_prefix = os.path.join(ROOT_DIR, 'data/runs/run')
    idx = os.path.join(ROOT_DIR, 'data/idx.txt')
    idx_term_offset = os.path.join(ROOT_DIR, 'data/idx_term_offset.txt')
    anchor_index = os.path.join(ROOT_DIR, 'data/anc_idx.txt')
    web_graph = os.path.join(ROOT_DIR, 'data/webgraph.txt')

    run_size = 10000
    compress = 'none' #'variablebyte' #'gamma' or 'none'

    def __init__(self):
        self.word_id = 0
        self.doc_id = 1
        self.run_number = 0
        self.run = list()
        self.voc = dict()
        self.docs = dict()

    def index_tarfile(self, tarball):
        with open(Indexer.doc_idx, 'wb+') as doc_writer, open(Indexer.doc_idx_offset, 'w+') as doc_writer_offset, open(Indexer.anchor_index, 'wb+') as anchor_writer, tarfile.open(tarball, 'r') as tar:
            # start the first run
            print('Starting the first index run.')
            run = []
            written = 0
            for file in tar.getmembers():
                print('Indexing document ' + file.name)
                doc = HTMLDocument(self.doc_id, file=file, line=None)
                tokens = doc.parse(self.doc_id, tar.extractfile(file))
                to_remove = list()
                sb = list()
                sb.append(str(doc.get_doc_id()))
                for k,v in doc.resources.items():
                    if str(k).startswith('l'):
                        url = k[1:]
                        if url.startswith('http://'):
                            url = url[7:]
                        if url.startswith('https://'):
                            url = url[8:]
                        if url.endswith('/'):
                            url = url[:-1]
                        sb.append('\t' + quote(url, safe='').replace('~', '%7E'))
                        for tok in v:
                            if tok.term.strip() == '':
                                continue
                            sb.append(':' + tok.term.strip() + ',' + str(tok.field))
                        to_remove.append(k)
                anchor_writer.write(bytes(''.join(sb) + '\n', 'utf-8'))

                for r in to_remove:
                    del doc.get_resources()[r]

                self.index(tokens, doc.get_doc_id())

                s = doc.get_name()
                if s.endswith('%2F'):
                    s = s[0:-3]

                self.docs[s] = self.doc_id

                doc_writer_offset.write(str(written) + '\n')
                # Writing to Direct Index
                idxable = doc.write_to_index()
                doc_writer.write(bytes(idxable, 'utf-8'))
                written += len(idxable.encode('utf-8'))
                self.doc_id += 1

        self.index_incoming_anchor_text()

        # If there is something yet in the last run, sort it and store

        print('Writing file run to disk')
        self.store_run()

        print('Indexing runs complete')

        self.merge_runs()

        # output the vocabulary
        self.output_lexicon()

        print('Indexing Complete')


    def index(self, tokens, doc_id):
        l_voc = dict()
        for tok in tokens:
            self.local_index(tok, doc_id, l_voc)

        for p in l_voc.values():
            if len(self.run) < Indexer.run_size:
                self.run.append(p)
            else:
                print('Current indexing run full, storing to disk')
                self.run.append(p)
                self.store_run()


    def get_run_number(self):
        self.run_number+=1
        return self.run_number-1

    def get_new_id(self):
        self.word_id += 1
        return self.word_id - 1

    def anc_local_index(self, tok, doc_id, l_voc):
        term_id = None
        if tok.term not in self.voc:
            term_id = self.get_new_id()
            self.voc[tok.term] = term_id
        else:
            term_id = self.voc[tok.get_token_string()]

        tok_id_field = (term_id, doc_id)
        if tok_id_field not in l_voc:
            p = DocumentTerm(term_id, doc_id, 1, tok.field)
            l_voc[tok_id_field] = p
        else:
            p = l_voc[tok_id_field]
            p.increase_frequency()
            l_voc[tok_id_field] = p

    def local_index(self, tok, doc_id, l_voc):
        term_id = None
        if tok.term not in self.voc:
            term_id = self.get_new_id()
            self.voc[tok.term] = term_id
        else:
            term_id = self.voc[tok.get_token_string()]

        tok_id_field = (term_id, tok.field)
        if tok_id_field not in l_voc:
            p = DocumentTerm(term_id, doc_id, 1, tok.field)
            l_voc[tok_id_field] = p
        else:
            p = l_voc[tok_id_field]
            p.increase_frequency()
            l_voc[tok_id_field] = p

    def index_incoming_anchor_text(self):
        l_voc = dict()
        with open(Indexer.anchor_index, 'r') as anchor_writer, open(Indexer.web_graph, 'w+') as graph_writer:
            doc_id_len = dict()
            for line in anchor_writer:
                a = line.split('\t')
                doci = int(a[0])
                for i in range(1,len(a)):
                    b = a[i].split(':')
                    url = b[0]
                    if url.endswith('%2F'):
                        url = url[0:-3]
                    toks = list()
                    for j in range(1, len(b)):
                        c = b[j].split(',')
                        s = c[0]
                        if s == '':
                            continue
                        toks.append(Token(s, 1))
                    if url in self.docs:
                        #self.index(toks, self.docs[url])
                        for tok in toks:
                            self.anc_local_index(tok, self.docs[url], l_voc)
                        graph_writer.write(str(doci) + '->' + str(self.docs[url]) + '\n')
                        if self.docs[url] not in doc_id_len:
                            doc_id_len[self.docs[url]] = len(toks)
                        else:
                            doc_id_len[self.docs[url]] = doc_id_len[self.docs[url]] + len(toks)

        for p in l_voc.values():
            if len(self.run) < Indexer.run_size:
                self.run.append(p)
            else:
                print('Current indexing run full, storing to disk')
                self.run.append(p)
                self.store_run()
        size = max(self.docs.values())
        pr = PageRank(Indexer.web_graph, size+1)
        pr.calculate_pagerank()
        self.reindex_documents(doc_id_len, pr)

    def reindex_documents(self, doc_id_len, pr):
        with open(Indexer.doc_idx + 'n', 'wb+') as doc_writer, \
                open(Indexer.doc_idx_offset + 'n', 'w') as doc_writer_offset, \
                open(Indexer.doc_idx, 'rb') as br:

            offset = 0
            for line in br:
                line = line.decode('utf-8').strip()
                l = line.split('\t')
                did = int(l[0])
                leng = l[2]
                if did in doc_id_len:
                    leng = str(leng) + ',' + str(Fields().get_field_id('link')) + ':' + str(doc_id_len[did])
                sb = list()
                sb.append(l[0])
                for i in range(1, len(l)):
                    if i == 2:
                        sb.append('\t')
                        sb.append(leng)
                    else:
                        sb.append('\t')
                        sb.append(l[i])
                sb.append('\t')
                sb.append('PR-#-')
                sb.append(str(pr.graph[did].data))
                sb.append('\n')
                docline = ''.join(sb)
                doc_writer.write(bytes(docline, 'utf-8'))
                doc_writer_offset.write(str(offset) + '\n')
                offset += len(docline.encode('utf-8'))

        # Cleanup disk
        os.remove(Indexer.doc_idx)
        os.remove(Indexer.doc_idx_offset)
        os.rename(Indexer.doc_idx + 'n', Indexer.doc_idx)
        os.rename(Indexer.doc_idx_offset + 'n', Indexer.doc_idx_offset)

    def output_lexicon(self):
        print('Writing lexicon to disk')
        with open(Indexer.lexicon, 'w') as lex_file:
            for k, v in sorted(self.voc.items()):
                lex_file.write(k + '\t' + str(v) + '\n')
        print('Lexicon writing finished')

    def store_run(self):
        run_id = self.get_run_number()
        out_name = Indexer.runs_prefix + str(run_id)
        if os.path.exists(Indexer.runs_prefix):
            print('Run directory already exists... deleting')
            os.removedirs(Indexer.runs_prefix)
        else:
            os.makedirs(Indexer.runs_prefix)

        print('Creating run directory')
        with open(out_name, 'w') as out_file:
            print('Sorting the current run')

            for p in sorted(self.run, key=attrgetter('term', 'doc', 'field')):
                out_file.write(str(p.doc) + '\t' + str(p.term) + '\t' + str(p.field) + '\t' + str(p.frequency) + '\n' )
        self.run = list()


    def merge_runs(self):
        merge_heap = []
        rfv = list()

        for i in range(0, self.run_number):
            filename = Indexer.runs_prefix + str(i)
            rfv.append(RunFile(filename, Indexer.run_size))
            # get the first element and put it in the heap
            occurrence = rfv[i].get_record()
            if occurrence is None:
                print('Error: Record was not found')
                return
            ro = MergeDocumentTerms(occurrence, i)
            heapq.heappush(merge_heap, ro)

        with open(Indexer.idx, 'wb') as out_file, open(Indexer.idx_term_offset, 'w', newline='\n') as tos_file:
            # Encode the fields in the inverted index
            sb = list()
            for k, v in Fields().get_items():
                sb.append(str(k) + ',' + str(v.field))

            line = ';'.join(sb)
            out_file.write(bytes(line + '\n', 'utf8'))

            current_term = 0
            current_term_offset = len(line) + 1

            wid = str(self.word_id) + '\n'
            tos_file.write(wid)

            print('Merging run files...')

            posting = dict()

            for f in Fields().get_fields():
                posting[f.field] = list()

            while len(merge_heap) > 0:
                first = heapq.heappop(merge_heap)

                # Get a new posting from the same run and put it in the heap if possible
                occurrence = rfv[first.run].get_record()
                if occurrence is not None:
                    ro = MergeDocumentTerms(occurrence, first.run)
                    heapq.heappush(merge_heap, ro)

                # Saving to the file

                if Indexer.compress == 'gamma':
                    if first.term > current_term:
                        tos_file.write(str(current_term_offset) + '\n')
                        out_file.write(struct.pack('i', current_term))
                        current_term_offset += 4
                        for f in Fields().get_fields():
                            current_doc = 0
                            out_file.write(struct.pack('c', bytes('#', 'utf8')))
                            out_file.write(struct.pack('B', f.field))
                            out_file.write(struct.pack('i', len(posting[f.field])))
                            current_term_offset += 6
                            outbits = bitarray()
                            for post in posting[f.field]:
                                outbits.extend(self.gamma_encode(post[0]-current_doc))
                                current_doc = post[0]
                                outbits.extend(self.gamma_encode(post[1]))
                            towrite = outbits.tobytes()
                            current_term_offset += len(towrite)
                            out_file.write(towrite)
                        current_term = first.term
                        for f in Fields().get_fields():
                            posting[f.field] = list()
                    elif first.term < current_term:
                        print('Term ids messed up, something went wrong with the sorting')
                elif Indexer.compress == 'variablebyte':
                    if first.term > current_term:
                        tos_file.write(str(current_term_offset) + '\n')
                        out_file.write(struct.pack('i', current_term))
                        current_term_offset += 4
                        for f in Fields().get_fields():
                            current_doc = 0
                            out_file.write(struct.pack('c', bytes('#', 'utf8')))
                            out_file.write(struct.pack('B', f.field))
                            out_file.write(struct.pack('i', len(posting[f.field])))
                            current_term_offset += 6
                            outbits = bitarray()
                            for post in posting[f.field]:
                                outbits.extend(self.variablebyte_encode(post[0]-current_doc))
                                current_doc = post[0]
                                outbits.extend(self.variablebyte_encode(post[1]))
                            towrite = outbits.tobytes()
                            current_term_offset += len(towrite)
                            out_file.write(towrite)
                        current_term = first.term
                        for f in Fields().get_fields():
                            posting[f.field] = list()
                    elif first.term < current_term:
                        print('Term ids messed up, something went wrong with the sorting')
                elif Indexer.compress == 'none':
                    if first.term > current_term:
                        tos_file.write(str(current_term_offset) + '\n')
                        sb = list()
                        for f in Fields().get_fields():
                            sb.append('#' + str(f.field) + ';'.join(posting[f.field]))

                        p = str(current_term) + '\t' + ''.join(sb) + '\n'
                        out_file.write(bytes(p, 'utf8'))
                        current_term_offset += len(p)
                        current_term = first.term
                        for f in Fields().get_fields():
                            posting[f.field] = list()
                    elif first.term < current_term:
                        print('Term ids messed up, something went wrong with the sorting')
                else:
                    raise ValueError('Index compression not defined')

                if Indexer.compress == 'gamma' or Indexer.compress == 'variablebyte':
                    posting[first.field.field].append((first.doc, first.frequency))
                else:
                    posting[first.field.field].append('(' +str(first.doc) + ',' + str(first.frequency) + ')')
        print('Index merging finished')

    def gamma_encode(self, num):
        if num == 0:
            raise ValueError('Number cannot be 0')
        bitlist = [int(x) for x in bin(num)[2:]]
        offset = bitarray()
        collect = False
        for _, v in enumerate(bitlist):
            if collect:
                offset.append(v)
            if v == 1:
                collect = True
        unary = bitarray()
        for i in range(len(offset)):
            unary.append(True)
        unary.append(False)
        gamma = unary
        for _, v in enumerate(offset):
            gamma.append(v)
        return gamma

    def variablebyte_encode(self, num):
        bitlist = [int(x) for x in bin(num)[2:]]
        vbe = list()
        while len(bitlist) > 7:
            bitler = [0] + bitlist[-7:]
            vbe = bitler + vbe
            bitlist = bitlist[:-7]
        vbe = (8 - len(bitlist)) * [0] + bitlist + vbe
        if len(vbe) >= 16:
            for i in range(-16, -len(vbe)-1, -8):
                vbe[i] = 1

        return bytearray(vbe)

class DocumentTerm(object):
    def __init__(self, term_id, doc_id, frequency, field):
        self.term = term_id
        self.doc = doc_id
        self.frequency = frequency
        self.field = field

    def __lt__(self, other):
        if self.term == other.term:
            if self.doc == other.doc:
                if self.field.field == other.field.field:
                    return 0
                return self.field.field < other.field.field
            else:
                return self.doc < other.doc
        else:
            return self.term < other.term

    def increase_frequency(self):
        self.frequency += 1


class MergeDocumentTerms(DocumentTerm):
    def __init__(self, p, r):
        super().__init__(p.term, p.doc, p.frequency, p.field)
        self.run = r


class RunFile(object):
    def __init__(self, file, b_size):
        self.filename = file
        self.buffer_size = b_size
        self.current_pos = 0
        self.buffer = []
        self.length = os.path.getsize(file)

    def fill_buffer(self):
        read_some = False
        with open(self.filename, 'r') as raf:
            raf.seek(self.current_pos)
            buf_size = len(self.buffer)

            while (self.current_pos < self.length) and (buf_size < self.buffer_size):
                read_some = True
                sb = list()
                c = raf.read(1)
                while c != '\t':
                    sb.append(c)
                    c = raf.read(1)
                d = ''.join(sb)

                sb = list()
                c = raf.read(1)
                while c != '\t':
                    sb.append(c)
                    c = raf.read(1)
                t = ''.join(sb)

                sb = list()
                c = raf.read(1)
                while c != '\t':
                    sb.append(c)
                    c = raf.read(1)
                z = Field(int(''.join(sb)))

                sb = list()
                c = raf.read(1)
                while c != '\n':
                    sb.append(c)
                    c = raf.read(1)
                f = ''.join(sb)

                p = DocumentTerm(int(t), int(d), int(f), z)
                heapq.heappush(self.buffer, p)
                self.current_pos = raf.tell()
                buf_size += 1
        return read_some

    def get_record(self):
        if len(self.buffer) > 0:
            return heapq.heappop(self.buffer)
        else:
            if self.fill_buffer():
                return heapq.heappop(self.buffer)
            else:
                return None


if __name__ == "__main__":
    crawl = None
    if len(sys.argv) == 2:
        print('Using user provided parameters')
        crawl = sys.argv[1]
    else:
        crawl = os.path.join(ROOT_DIR, 'data/NDCrawler_result_large.tar')

    indexer = Indexer()
    indexer.index_tarfile(crawl)
