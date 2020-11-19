import networkx
import random
import numpy
import scipy.sparse.linalg

def get_nodes_degree(graph):
    return list(graph.in_degrees())

def get_nodes_closeness_centrality(graph):
    return list(networkx.closeness_centrality(graph.to_networkx()).values())

def get_nodes_betweenness_centrality(graph):
    return list(networkx.betweenness_centrality(graph.to_networkx()).values())

def get_nodes_pagerank(graph):
    return list(networkx.algorithms.link_analysis.pagerank_alg.pagerank(graph.to_networkx()).values())

def get_nodes_triangles(graph):
    return list(networkx.algorithms.cluster.triangles(graph.to_networkx()).values())

def get_nodes_random(graph):
    return list([random.random() for _ in graph.nodes()])

def get_nodes_eigenvector(graph, k=1):
    A = numpy.real(networkx.to_scipy_sparse_matrix(graph.to_networkx()))
    e, v = scipy.sparse.linalg.eigs(A, k)
    return v

NODE_INFORMATION = {'degree' : get_nodes_degree, 'closeness_centrality' : get_nodes_closeness_centrality,
                    'betweenness_centrality' : get_nodes_betweenness_centrality, 'pagerank' : get_nodes_pagerank,
                    'triangles' : get_nodes_triangles, 'random' : get_nodes_random,
                    'eig1' : (lambda g : get_nodes_eigenvector(g, 1)),
                    'eig2' : (lambda g : get_nodes_eigenvector(g, 2)),
                    'eig3' : (lambda g : get_nodes_eigenvector(g, 3))}