class Node(object):
    def __init__(self, i):
        self.id = i
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

    def __init__(self, webgraph, num_docs):
        self.graph = list()
        for n in range(0, num_docs):
            self.graph.append(Node(n))

    def calculate_pagerank(self):
        pass

    def get_pagerank(self, docid):
        return 0.0