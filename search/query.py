from index.inverted_index import InvertedIndex
from index.lexicon import Lexicon
from index.documents import WhitespaceTokenizer, CaseFoldingNormalizer, Fields, Field


class Query:
    def __init__(self, query_string, tokenizer = WhitespaceTokenizer, normalizer = CaseFoldingNormalizer):
        self.query_string = query_string
        self.tokenizer = tokenizer
        self.normalizer = normalizer
        toks = tokenizer.tokenizer_str(self.query_string)
        toks = normalizer.normalize(toks)
        self.terms = list(zip(toks, len(toks)*[1.0]))


class Matching:
    RETRIEVED_SET_SIZE = 200

    def __init__(self, retrieval_model):
        self.query_term_to_match_list = None
        self.score_modifiers = []
        self.num_retrieved_docs = 0
        self.index = InvertedIndex()
        self.result_set = None
        self.retrieval_model = retrieval_model

    def initialize(self, query_terms: Query):
        query_term_strings = query_terms.terms
        self.query_term_to_match_list = dict()
        for query_term, wgt in query_term_strings:
            t = Lexicon().get_term_id(query_term)
            if t != -1:
                self.query_term_to_match_list[query_term] = (t, wgt)
            else:
                print('Term', query_term, 'not found. Skipping...')

    def pseudo_relevance_match(self, query_terms):
        # TODO implement pseudo relevance feedback matching
        alpha = 0.9
        beta = 0.75
        N_rel = 5
        # you are welcome to experiment with there values.

        return self.match(query_terms)

    def match(self, query_terms):
        self.initialize(query_terms)
        results = dict()
        query_length = len(self.query_term_to_match_list)

        # The posting list iterator array (one per term) and initialization
        posting_list_list = list()

        for term, term_id in self.query_term_to_match_list.items():
            posting_list_list.append((self.index.get_postings(term_id[0]), term_id[1]))

        for f in Fields().get_fields():
            accumulators = dict()
            target_result_set_size_reached = False
            current_posting_list = None

            # while not end of all posting lists
            for current_posting_list_index in range(len(posting_list_list)):
                current_posting_list, wgt = posting_list_list[current_posting_list_index]
                for current_posting in range(current_posting_list.size(f.field)):
                    posting_list, wgt = posting_list_list[current_posting_list_index]
                    current_doc_id = posting_list.postings[f.field][current_posting].doc

                    post = current_posting_list.postings[f.field][current_posting]
                    post.frequency *= wgt

                    # We create a new hit for each new doc id considered
                    current_candidate = None
                    if current_doc_id in accumulators:
                        current_candidate = accumulators[current_doc_id]
                    else:
                        current_candidate = Hit(current_doc_id)

                    accumulators[current_doc_id] = current_candidate

                    self.assign_score(current_posting_list_index, self.retrieval_model, current_candidate, post, len(current_posting_list.postings[f.field]), f)

            self.result_set = ResultSet(accumulators.values())
            self.num_retrieved_docs = len(self.result_set.scores)
            self.finalize(query_terms, f)
            results[f.field] = self.result_set

        final_scores = dict()
        for f in Fields().get_fields():
            for i in range(len(results[f.field].doc_ids)):
                if results[f.field].doc_ids[i] not in final_scores :
                    final_scores[results[f.field].doc_ids[i]] = Hit(results[f.field].doc_ids[i])

                weighted_score = results[f.field].scores[i] * Fields().get_weight(f.field)
                final_scores[results[f.field].doc_ids[i]].update_score(weighted_score)
                final_scores[results[f.field].doc_ids[i]].update_occurrence(i)

        rs = ResultSet(final_scores.values())
        self.num_retrieved_docs = len(final_scores.values())
        set_size = min(self.RETRIEVED_SET_SIZE, self.num_retrieved_docs)
        if set_size == 0:
            set_size = self.num_retrieved_docs
        rs.exact_result_size = self.num_retrieved_docs
        rs.result_size = set_size
        rs.sort(set_size)

        return rs

    def add_score_modifier(self, score_modifier):
        self.score_modifiers.append(score_modifier)

    def finalize(self, query_terms: Query, field : Field):
        set_size = min(self.RETRIEVED_SET_SIZE, self.num_retrieved_docs)
        if set_size == 0:
            set_size = self.num_retrieved_docs

        self.result_set.set_exact_result_size = self.num_retrieved_docs
        self.result_set.result_size = set_size
        self.result_set.sort(set_size)

        for score_modifier in self.score_modifiers:
            if score_modifier.modify_scores(self.index, query_terms, self.result_set, field):
                self.result_set.sort(self.result_set.result_size)

    def assign_score(self, pos, retrieval_model, hit, posting, document_frequency, field):
        hit.update_score(retrieval_model.score(posting, document_frequency, field))
        hit.update_occurrence(1 << pos)


class Hit:
    def __init__(self, doc_id):
        self.doc_id = doc_id
        self.score = 0.0
        self.occurrence = 0

    def update_score(self, update):
        self.score += update

    def update_occurrence(self, update):
        self.occurrence |= update


class ResultSet:

    def __init__(self, hits):
        self.result_size = len(hits)
        self.exact_result_size = self.result_size
        self.doc_ids = list()
        self.scores = list()
        self.occurrences = list()

        for hit in hits:
            self.doc_ids.append(hit.doc_id)
            self.scores.append(hit.score)
            self.occurrences.append(hit.occurrence)

    def sort(self, top_docs):
        results = list()
        for i in range(self.result_size):
            results.append( (self.doc_ids[i], self.scores[i], self.occurrences[i]) )
        results = sorted(results, key=lambda x: x[1], reverse=True)
        self.doc_ids = list()
        self.scores = list()
        self.occurrences = list()
        for d, s, o in results:
            self.doc_ids.append(d)
            self.scores.append(s)
            self.occurrences.append(o)
