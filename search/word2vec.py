import gzip
import logging
import os

import gensim

from definitions import ROOT_DIR

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
reviews_txtgz = os.path.join(ROOT_DIR, 'data/reviews_data.txt.gz')


def read_input(input_file):
    """This method reads the input file which is in gzip format"""

    logging.info("reading file {0}...this may take a while".format(input_file))
    with gzip.open(input_file, 'rb') as f:
        for i, line in enumerate(f):

            if (i % 10000 == 0):
                logging.info("read {0} reviews".format(i))
            # do some pre-processing and return list of words for each review
            # text
            yield gensim.utils.simple_preprocess(line)


documents = list(read_input(reviews_txtgz))
logging.info("Done reading data file")

model = gensim.models.Word2Vec(documents, size=150, window=10, min_count=2, workers=10)
model.train(documents, total_examples=len(documents), epochs=10)

print(model.wv.most_similar(positive=['king', 'woman'], negative=['man'], topn=20))
print(model.wv.most_similar(positive=['engineering', 'profit'], negative=['smart'], topn=20))
print(model.wv.most_similar(positive=['college'], negative=['professor'], topn=20))
print(model.wv.most_similar(positive=['vacation', 'homework'], negative=['money'], topn=20))