from definitions import ROOT_DIR
from os import listdir, mkdir
from os.path import isfile, join, exists


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
        self.sum_mrr = 0.0
        self.sum_ndcg = 0.0

        self.missing = -1

        if not exists(self.qrels):
            print('Creating qrels directory')
            mkdir(self.qrels)

        files = [f for f in listdir(self.qrels) if isfile(join(self.qrels, f))]
        self.parse(files)

    def parse(self, files):
        for qrel in files:
            with open(qrel) as r:
                q = ''
                for line in r:
                    if line.startswith('query:'):
                        q = line[7:].strip()
                        if q not in self.rels:
                            self.rels[q] = {}
                        else:
                            rel = line.split(' ')
                            if len(rel) != 2:
                                raise Exception('invalid qrels file: ' + str(qrel))
                            self.rels[q][int(rel[0])] = int(rel[1])

    def evaluate(self, result_set, query, size=None):
        if size is None:
            size = result_set.result_size()
        tbl = list()
        for docid in result_set.doc_ids:
            tbl.append(docid)
        return self.run(tbl, query)

    def run(self, tbl, query):
        precision = self.calc_precision(tbl, query)
        self.sum_prec += precision
        recall = self.calc_recall(tbl, query)
        self.sum_recall += recall
        f1 = self.calc_f1(tbl, query)
        self.sum_f1 += f1
        avg_prec = self.calc_avg_prec(tbl, query)
        self.sum_avg_prec += avg_prec
        mrr = self.calc_mrr(tbl, query)
        self.sum_mrr += mrr
        ndcg = self.calc_ndcg(tbl, query)
        self.sum_ndcg += ndcg

        return {'missing': self.missing, 'precision': precision, 'recall': recall, 'f1': f1, 'avg_prec': avg_prec,
                'mrr': mrr, 'ndcg': ndcg}

    def calc_precision(self, tbl, query):
        return 0.0

    def calc_recall(self, tbl, query):
        return 0.0

    def calc_f1(self, tbl, query):
        return 0.0

    def calc_avg_prec(self, tbl, query):
        return 0.0

    def calc_mrr(self, tbl, query):
        return 0.0

    def calc_ndcg(self, tbl, query):
        return 0.0
