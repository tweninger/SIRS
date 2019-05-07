class Node(object):
    def __init__(self):
        self.in_links = list()
        self.out_links = list()
        self.data = 1.0

    def add_in_link(self, nbr):
        self.in_links.append(nbr)

    def add_out_link(self, nbr):
        self.out_links.append(nbr)

    def get_in_links(self):
        return self.in_links

    def get_out_links(self):
        return self.out_links

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data


class PageRank(object):

    alpha = 0.85
    iter = 50

    def __init__(self, webgraph, num_docs):
        """
        Initialize PageRank object, and loads the PageRank graph.

        :param webgraph: A file from which web graph will be loaded
        :param num_docs: Number of documents
        """

        # IMPORTANT - Node ids should correspond to docids.
        self.graph = list()
        for n in range(1, num_docs+1):
            self.graph.append(Node())

        print('Loading Web graph')

        # TODO - load graph from file. Create edges within Node object.


        with open(webgraph, 'r') as r:
            for line in r:
                src, tgt = line.strip().split('->')
                src = int(src)
                tgt = int(tgt)
                self.graph[src].add_out_link(tgt)
                self.graph[tgt].add_in_link(src)

    def calculate_pagerank(self):
        print('Starting PageRank calculations')

        # TODO - fill in this function

        for i in range(PageRank.iter):
            for node in self.graph:
                sum = 0.0
                for inlink in node.get_in_links():
                     sum += self.graph[inlink].get_data() / len(self.graph[inlink].get_out_links())
                new_pr = (1-PageRank.alpha) + (PageRank.alpha * sum)
                node.set_data(new_pr)
