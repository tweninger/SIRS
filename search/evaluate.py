from definitions import ROOT_DIR
from os import listdir, mkdir
from os.path import isfile, join, exists
import math, sys


class Evaluate:
    QRELS_FLDR = join(ROOT_DIR, 'qrels/')
    REL_THRESH = 2

    def __init__(self, qrels=None):
        if qrels is None:
            self.qrels = Evaluate.QRELS_FLDR
        else:
            self.qrels = qrels

        self.rels = dict()
        self.sum_prec = 0.0
        self.sum_recall = 0.0
        self.sum_f1 = 0.0
        self.sum_avg_prec = 0.0
        self.sum_rr = 0.0
        self.sum_ndcg = 0.0

        self.missing = 0

        if not exists(self.qrels):
            print('Creating qrels directory')
            mkdir(self.qrels)

        files = [f for f in listdir(self.qrels) if isfile(join(self.qrels, f))]
        self.parse(files)

    def parse(self, files):
        for qrel in files:
            for q, docid, rel in self.parse_file(qrel):
                self.rels[q][docid] = rel


    def parse_file(self, file):
        with open(join(Evaluate.QRELS_FLDR, file)) as r:
            q = ''
            for line in r:
                if line.startswith('query:'):
                    q = line[7:].strip()
                    if q not in self.rels:
                        self.rels[q] = {}
                else:
                    rel = line.strip().split()
                    if len(rel) != 2:
                        raise Exception('invalid qrels file: ' + str(file))
                    yield q, int(rel[0]), int(rel[1])

    def self_assess(self, qrel_files):
        for qrel in qrel_files:
            num_queries = 0
            tbl = None
            query=''
            with open(join(Evaluate.QRELS_FLDR, qrel)) as qrel_file:
                for line in qrel_file:
                    if line.startswith('query:'):
                        if tbl is not None:
                            self.run(tbl, query)
                        query = line[7:].strip()
                        tbl = list()
                        num_queries += 1
                    else:
                        rel = line.split(' ')
                        if len(rel) != 2:
                            print('invalid qrels file: ' + qrel)
                            return
                        tbl.append(int(rel[0]))
                if tbl is not None:
                    self.run(tbl, query)

                print('Evaluation results queries in: ' + qrel)
                if self.missing > 0:
                    print('MISSING some judgements! Results are incomplete')
                print('Mean Precision: ' + str(self.sum_prec/num_queries))
                print('Mean Recall: ' + str(self.sum_recall/num_queries))
                print('Mean F1: ' + str(self.sum_f1/num_queries))
                print('Mean Average Precision: ' + str(self.sum_avg_prec/num_queries))
                print('Mean Reciporal Rank: ' + str(self.sum_rr/num_queries))
                print('Mean nDCG: ' + str(self.sum_ndcg/num_queries))

    def evaluate(self, result_set, query, size=None):
        if size is None:
            size = result_set.result_size()
        tbl = list()
        for i in range(min(size, len(result_set.doc_ids))):
            docid = result_set.doc_ids[i]
            tbl.append(docid)
        return self.run(tbl, query)

    def run(self, tbl, query):
        precision = self.calc_precision(tbl, query)
        self.sum_prec += precision
        recall = self.calc_recall(tbl, query)
        self.sum_recall += recall
        f1 = self.calc_f1(precision, recall, 1.0)
        self.sum_f1 += f1
        avg_prec = self.calc_avg_prec(tbl, query)
        self.sum_avg_prec += avg_prec
        rr = self.calc_rr(tbl, query)
        self.sum_rr += rr
        ndcg = self.calc_ndcg(tbl, query)
        self.sum_ndcg += ndcg

        return {'missing': self.missing, 'precision': precision, 'recall': recall, 'f1': f1, 'avg_prec': avg_prec,
                'rr': rr, 'ndcg': ndcg}

    def calc_precision(self, tbl, query, k=100000):
        # TODO Precision
        return 0.0

    def calc_recall(self, tbl, query):
        tp = 0
        fn = 0
        total_relevant = 0
        if query not in self.rels:
            print('No relevance judgements for query: ' + str(query))
            self.missing = -1
            return 0
        for rel in self.rels[query].values():
            if rel > Evaluate.REL_THRESH:
                total_relevant += 1

        for docid in tbl:
            if docid not in self.rels[query]:
                print('No relevance information for docID: ' + str(docid))
                self.missing += 1
                # HW3 Students, don'y copy the missing+=1 code from here.
                # This will cause you to double/triple/... count missing docIDs.
                continue
            rel = self.rels[query][docid]

            if rel > self.REL_THRESH:
                tp += 1

        fn = total_relevant - tp
        if (tp+fn) == 0:
            return 0
        return tp / (tp + fn)

    def calc_f1(self, precision, recall, beta):
        # TODO F1
        return 0.

    def calc_avg_prec(self, tbl, query):
        # TODO MAP
        return 0.

    def calc_rr(self, tbl, query):
        # TODO RR
        return 0.

    def calc_ndcg(self, tbl, query):
        #TODO NDCG
        return 0.

if __name__ == "__main__":
    if len(sys.argv) == 2:
        print('Using user provided parameters')
        qrels = sys.argv[1]
    else:
        print('User did not provide 1 input argument; reverting to qrels folder')
        qrels = Evaluate.QRELS_FLDR
    e = Evaluate()
    e.self_assess([f for f in listdir(qrels) if isfile(join(qrels, f))])
