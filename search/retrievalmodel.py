import abc, math
from search.query import ResultSet, Query
from index.direct_index import DirectIndex
from index.inverted_index import Posting


class RetrievalModel(abc.ABC):
    @abc.abstractmethod
    def score(self, posting, document_frequency, field):
        """
        Returns a value for a given posting that is accumulated in the matcher
        :param posting: The posting to score
        :param document_frequency: Number documents this term appears in
        :param field: Field in the index to process
        :return: score
        """
        pass


class ScoreModifier(abc.ABC):
    @abc.abstractmethod
    def modify_scores(self, index, query_terms, result_set, field):
        """

        :param index:
        :param query_terms:
        :param result_set:
        :param field:
        :return:
        """
        pass


class BooleanRM (RetrievalModel):
    def score(self, posting, document_frequency, field):
        return 1.0


class BooleanScoreModifier (ScoreModifier):
    def modify_scores(self, index, query: Query, result_set: ResultSet, field):
        occurrences = result_set.occurrences
        scores = result_set.scores
        size = result_set.result_size
        start = 0
        end = size
        num_modified_document_scores = 0
        query_len_mask = 0

        for i in range(len(query.terms)):
            query_len_mask = ((query_len_mask << 1) + 1)

        # modify scores
        for i in range(start, end):
            if (occurrences[i] & query_len_mask) != query_len_mask:
                if scores[i] > -10000:
                    num_modified_document_scores += 1
                scores[i] = -10000

        if num_modified_document_scores == 0:
            return False

        result_set.result_size = size - num_modified_document_scores
        result_set.exact_result_size = result_set.exact_result_size - num_modified_document_scores

        return True

class CosineRM (RetrievalModel):
    def score(self, posting, document_frequency, field):
        return posting.frequency * math.log2(DirectIndex().get_num_docs()/document_frequency)


class CosineScoreModifier (ScoreModifier):
    def modify_scores(self, index, query: Query, result_set: ResultSet, field):
        for i in range(len(result_set.scores)):
            result_set.scores[i] = result_set.scores[i] / DirectIndex().get_doc(result_set.doc_ids[i]-1).get_num_tokens(field.field)


class JelinekMercerRM (RetrievalModel):
    def score(self, posting : Posting, document_frequency, field):
        lambd = 0.2
        N_d = DirectIndex().get_doc(posting.doc - 1).get_num_tokens(field.field)
        N = DirectIndex().get_num_tokens(field.field)
        lhs = (1-lambd) * posting.frequency / N_d
        rhs = lambd * document_frequency / N
        return - math.log(lhs + rhs)


class DirichletRM (RetrievalModel):
    def score(self, posting : Posting, document_frequency, field):
        moo = 200
        N_d = DirectIndex().get_doc(posting.doc - 1).get_num_tokens(field.field)
        N = DirectIndex().get_num_tokens(field.field)
        lhs = (N_d/(N_d+moo)) * (posting.frequency / N_d)
        rhs = (moo/(moo+N_d)) * (document_frequency / N)
        return - math.log(lhs + rhs)

class PageRankScoreModifier (ScoreModifier):

    def __init__(self, pr_wgt):
        self.pr_wgt = pr_wgt

    def modify_scores(self, index, query: Query, result_set: ResultSet, field):
        for i in range(len(result_set.scores)):
            result_set.scores[i] = result_set.scores[i] + (self.pr_wgt * math.log(float(DirectIndex().get_doc(result_set.doc_ids[i]-1).get_resources()['PR'])+1))


class BM25RM (RetrievalModel):
    def score(self, posting, document_frequency, field):
        k1 = 2.0
        b = 0.75
        idf = math.log2((DirectIndex().get_num_docs() - document_frequency)/document_frequency)
        num = (k1+1)*posting.frequency
        N_d = DirectIndex().get_doc(posting.doc - 1).get_num_tokens(field.field)
        N = DirectIndex().get_num_docs()
        avgdl = DirectIndex().get_num_tokens(field.field) / N
        den = k1 * ((1-b) + b*(N_d/avgdl) ) + posting.frequency
        return idf * (num/den)
