# MIT License
# Copyright (c) 2020 Vijay Prakash Dwivedi, Chaitanya K. Joshi, Thomas Laurent, Yoshua Bengio, Xavier Bresson


import torch
import pickle
import torch.utils.data
import time
import numpy as np
import csv
import dgl
from scipy import sparse as sp
import numpy as np

EPS = 1e-5

def get_nodes_degree(graph):
    return graph.in_degrees(graph.nodes)

def get_nodes_closeness_centrality(graph):
    return graph.closeness_centrality(graph.to_networkx())

def get_nodes_betweenness_centrality(graph):
    return graph.betweenness_centrality(graph.to_networkx())

class StructureAwareGraph(torch.utils.data.Dataset):
    # Create a StructureAwareGraph from a MoleculeDGL
    def __init__(self, molecule_dgl):
        self.data_dir = molecule_dgl.data_dir
        self.split = molecule_dgl.split
        self.num_graphs = molecule_dgl.num_graphs
        self.graph_lists = []
        self.node_labels = []
        self._prepare()

    def _prepare(self):
        print("preparing %d graphs for the %s set..." % (self.num_graphs, self.split.upper()))

        self.node_labels = []
        self.graph_labels = []

        for molecule in self.data:
            node_features = molecule['atom_type'].long()

            adj = molecule['bond_type']
            edge_list = (adj != 0).nonzero()  # converting adj matrix to edge_list

            edge_idxs_in_adj = edge_list.split(1, dim=1)
            edge_features = adj[edge_idxs_in_adj].reshape(-1).long()

            # Create the DGL Graph
            g = dgl.DGLGraph()
            g.add_nodes(molecule['num_atom'])

            for src, dst in edge_list:
                g.add_edges(src.item(), dst.item())
            g.edata['feat'] = edge_features

            # Set node features
            g.ndata['feat'] = node_features

            self.graph_lists.append(g)

            # Set node labels
            self.node_labels.append(node_features)

    def __len__(self):
        return self.n_samples

    def __getitem__(self, idx):
        return self.graph_lists[idx], self.graph_labels[idx]

class MoleculeDataset(torch.utils.data.Dataset):

    def __init__(self, name, norm='none', verbose=True):
        """
            Loading SBM datasets
        """
        start = time.time()
        if verbose:
            print("[I] Loading dataset %s..." % (name))
        self.name = name
        data_dir = 'data/'
        with open(data_dir + name + '.pkl', "rb") as f:
            f = pickle.load(f)
            self.train = StructureAwareGraph(f[0])
            self.val = StructureAwareGraph(f[1])
            self.test = StructureAwareGraph(f[2])
            self.num_atom_type = f[3]
            self.num_bond_type = f[4]
        if verbose:
            print('train, test, val sizes :', len(self.train), len(self.test), len(self.val))
            print("[I] Finished loading.")
            print("[I] Data load time: {:.4f}s".format(time.time() - start))

    # form a mini batch from a given list of samples = [(graph, label) pairs]
    def collate(self, samples):
        # The input samples is a list of pairs (graph, label).
        graphs, labels = map(list, zip(*samples))
        labels = torch.tensor(np.array(labels)).unsqueeze(1)
        tab_sizes_n = [graphs[i].number_of_nodes() for i in range(len(graphs))]
        tab_snorm_n = [torch.FloatTensor(size, 1).fill_(1. / float(size)) for size in tab_sizes_n]
        snorm_n = torch.cat(tab_snorm_n).sqrt()
        tab_sizes_e = [graphs[i].number_of_edges() for i in range(len(graphs))]
        tab_snorm_e = [torch.FloatTensor(size, 1).fill_(1. / float(size)) for size in tab_sizes_e]
        snorm_e = torch.cat(tab_snorm_e).sqrt()
        batched_graph = dgl.batch(graphs)
        return batched_graph, labels, snorm_n, snorm_e

    def _add_self_loops(self):
        # function for adding self loops
        # this function will be called only if self_loop flag is True

        self.train.graph_lists = [self_loop(g) for g in self.train.graph_lists]
        self.val.graph_lists = [self_loop(g) for g in self.val.graph_lists]
        self.test.graph_lists = [self_loop(g) for g in self.test.graph_lists]
