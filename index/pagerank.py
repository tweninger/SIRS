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
    alpha = 0.85
    iter = 50

    def __init__(self, webgraph, num_docs):
        self.graph = list()
        for i in range(0, num_docs):
            self.graph.append(Node(i))

        with open(webgraph, 'r') as br:
            for line in br:
                ids = line.split('->')
                src = int(ids[0].strip())
                dst = int(ids[1].strip())
                self.graph[src].add_out_link(self.graph[dst])
                if self.graph[src] is not None and self.graph[dst] is not None:
                    self.graph[dst].add_in_link(self.graph[src])
                    self.graph[src].add_out_link(self.graph[dst])

    def calculate_pagerank(self):
        nnodes = len(self.graph)
        #init
        for node in self.graph:
            node.data /= nnodes

        #sinks
        dangle = [n.data for n in self.graph if len(n.get_out_links()) == 0]

        danglesum = PageRank.alpha / nnodes * sum(n for n in dangle)
        teleportsum = (1.0 - PageRank.alpha) / nnodes * sum(n.data for n in self.graph)

        for i in range(1, PageRank.iter):
            data_last = [n.data for n in self.graph]
            for node in range(nnodes):
                for out_link in self.graph[node].get_out_links():
                    out_link.data += 0.0  # TODO Change me
                self.graph[node].data += danglesum + teleportsum  # 1 - alpha
            normalizer = 1.0 / sum(n.data for n in self.graph)
            for node in self.graph:
                node.data *= normalizer

    def get_pagerank(self, docid):
        if docid in self.graph:
            return self.graph[docid].get_data()
        else:
            return -1.0