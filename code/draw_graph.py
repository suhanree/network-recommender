# Draw a graph using graph_tool.
# It has to read the csv file, and convert it to the graph_tool Graph object.

# by Suhan Ree
# last edited on 06-20-2015

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from graph_tool.all import *
import os
import cPickle as pickle

from my_utilities import read_dictlist_from_file, read_dict_from_file

# Filename for the pickled data of reviews with city info.
network_filename = '../data/networkr.csv'
user_by_city_filename = '../data/user_by_city'

graph_pickle_filename = '../data/graph.pkl'
pos_pickle_filename = '../data/positions.pkl'

def read_file(network_filename, user_by_city_filename=None):
    """
    Read two files (networkr.csv, user_by_city) and create the Graph object.
    (user_id's will be reordered because Graph object needs consecutive integers
    for indices of the graph.)
    Input:
        network_filename:  filename for the network.
        user_by_city_filename: filename for the city info (optional)
    Output:
        gg: Graph object created
    """
    graph = read_dictlist_from_file(network_filename)

    gg = Graph(directed=False)  # new Graph object

    user_id_map = {}  # storing new id info
    new_id = 0
    for user_id in graph:
        temp_users = []
        temp_users.append(user_id)
        for friend in graph[user_id]:
            temp_users.append(friend)
        for id1 in temp_users:
            if id1 not in user_id_map:
                user_id_map[id1] = new_id
                gg.add_vertex()  # index for this vertex will be new_id
                new_id += 1
            if id1 != user_id:
                gg.add_edge(gg.vertex(user_id_map[user_id]),
                            gg.vertex(user_id_map[id1]))

    print "Done reading the graph."
    if user_by_city_filename is not None:
        cities = read_dict_from_file(user_by_city_filename)
        # Adding vertex property as city
        city_prop = gg.new_vertex_property("int")
        for user_id in cities:
            city_prop[gg.vertex(user_id_map[user_id])] = cities[user_id]
        #gg.vertex_properties['city_prop'] = city_prop  # making it internal
    print "Done reading the city."
    return (gg, city_prop)


def main():
    if os.path.exists(graph_pickle_filename):
        with open(graph_pickle_filename, 'r') as f:
            (gg, city_prop) = pickle.load(f)
        print "Read the graph info from pickled file."
    else:
        (gg, city_prop) = read_file(network_filename, user_by_city_filename)
        with open(graph_pickle_filename, 'wb') as f:
            pickle.dump((gg, city_prop), f)

    if os.path.exists(pos_pickle_filename):
        with open(pos_pickle_filename, 'r') as f:
            pos = pickle.load(f)
        print "Read the position info from pickled file."
    else:
        pos = sfdp_layout(gg, groups=city)
        with open(pos_pickle_filename, 'wb') as f:
            pickle.dump(pos, f)
        print "Done calculating positions."

    # Let's plot its in-degree distribution
    in_hist = vertex_hist(gg, "in")

    y = in_hist[0]
    err = np.sqrt(in_hist[0])
    err[err >= y] = y[err >= y] - 1e-2

    plt.figure(figsize=(6,4))
    plt.errorbar(in_hist[1][:-1], in_hist[0], fmt="o", yerr=err,
                     label="in")
    plt.gca().set_yscale("log")
    plt.gca().set_xscale("log")
    plt.gca().set_ylim(1e-1, 1e5)
    plt.gca().set_xlim(0.8, 1e3)
    plt.subplots_adjust(left=0.2, bottom=0.2)
    plt.xlabel("$k_{in}$")
    plt.ylabel("$NP(k_{in})$")
    plt.tight_layout()
    plt.savefig("price-deg-dist.pdf")
    plt.savefig("price-deg-dist.png")

    graph_draw(gg, pos, output_size=(1000, 1000), vertex_color=[1,1,1,0],
               # vertex_fill_color=city_prop,
               vertex_size=1, edge_pen_width=1.2,
               #vcmap=matplotlib.cm.gist_heat_r,
               output="whole_network.png")
    return


if __name__ == '__main__':
    main()
