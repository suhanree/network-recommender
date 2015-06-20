# Draw a graph using graph_tool.
# It has to read the csv file, and convert it to the graph_tool Graph object.

# by Suhan Ree
# last edited on 06-20-2015

import numpy as np
import matplotlib
from graph_tool.all import *

from my_utilities import read_dictlist_from_file, read_dict_from_file

# Filename for the pickled data of reviews with city info.
network_filename = '../data/networkr.csv'
user_by_city_filename = '../data/user_by_city'


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
        gg.vertex_properties['city_prop'] = city_prop  # making it internal
    print "Done reading the city."
    return gg


def main():
    gg = read_file(network_filename, user_by_city_filename)
    city = gg.vertex_properties["city_prop"]

    pos = sfdp_layout(gg, groups=city)
    print "Done calculating positions."
    graph_draw(g, pos, output_size=(1000, 1000), vertex_color=[1,1,1,0],
                vertex_fill_color=city, vertex_size=1, edge_pen_width=1.2,
                vcmap=matplotlib.cm.gist_heat_r, output="whole_network.png")
    return


if __name__ == '__main__':
    main()
