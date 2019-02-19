import abc, math
from search.query import ResultSet, Query
from index.direct_index import DirectIndex


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