from flask import Flask, request, json, render_template
from search.retrievalmodel import BooleanRM, BooleanScoreModifier, CosineRM, CosineScoreModifier
from search.query import Matching, Query
from search.evaluate import Evaluate
from index.documents import Fields
from index.direct_index import DirectIndex
import math
import datetime

app = Flask(__name__)
app._static_folder = 'static'


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/searcher/")
def searcher():
    time = datetime.datetime.now()

    # Receive GET paramenters
    model = request.args.get('model', default='Boolean', type=str)
    query = request.args.get('query', default='', type=str)

    wgts = dict()
    wgts['body'] = request.args.get('bodywgt', default='', type=float)
    wgts['link'] = request.args.get('linkwgt', default='', type=float)
    wgts['title'] = request.args.get('titlewgt', default='', type=float)
    pr_wgt = request.args.get('prwgt', default='', type=float)

    result_set = None
    matching = None

    if model == 'Boolean':
        matching = Matching(BooleanRM())
        Fields().assign_weights(wgts)
        matching.add_score_modifier(BooleanScoreModifier())
    elif model == 'Cosine':
        matching = Matching(CosineRM())
        Fields().assign_weights(wgts)
        matching.add_score_modifier(CosineScoreModifier())
    result_set = matching.pseudo_relevance_match(Query(query))

    g = Evaluate()
    evaluation_results = g.evaluate(result_set, query, 10)

    results = []
    for i in range(result_set.result_size):
        doc_id = result_set.doc_ids[i]
        doc = DirectIndex().get_doc(doc_id-1)
        title = doc.resources['title']
        if title is None:
            title = ''
        results.append( {'title': title, 'docid': doc_id, 'url': doc.name} )

    data = {
        'size': result_set.result_size,
        'time': str((datetime.datetime.now() - time).seconds) + '.' + str(math.ceil((datetime.datetime.now() - time).microseconds / 1000)),
        'data': results,
        'eval': evaluation_results
    }
    response = app.response_class(
        response=json.dumps(data, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)