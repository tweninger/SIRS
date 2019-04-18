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
        """
        Initialize PageRank object, and loads the PageRank graph.

        :param webgraph: A file from which web graph will be loaded
        :param num_docs: Number of documents
        """

        # IMPORTANT - Node ids should correspond to docids. (index starts at 1)
        self.graph = list()
        for n in range(1, num_docs+1):
            self.graph.append(Node(n))

        # TODO - load graph from file. Create edges within Node object.


    def calculate_pagerank(self):
        pass
        # TODO - fill in this function
