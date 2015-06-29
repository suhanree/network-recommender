# Draw a graph using graph_tool.
# It has to read the csv file, and convert it to the graph_tool Graph object.

# Filename: draw_graph.py
# by Suhan Ree
# last edited on 06-20-2015

from graph_tool.all import *

from my_utilities import read_dictlist_from_file, read_dict_from_file

# Filename for the pickled data of reviews with city info.
network_filename = '../data/network0.csv'
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
            if id1 > user_id:
                gg.add_edge(gg.vertex(user_id_map[user_id]),
                            gg.vertex(user_id_map[id1]))
    print "Done reading the graph."
    if user_by_city_filename is None:
        return (gg, None)
    if user_by_city_filename is not None:
        cities = read_dict_from_file(user_by_city_filename)
        # Adding vertex property as city
        city_prop = gg.new_vertex_property("int")
        for user_id in cities:
            city_prop[gg.vertex(user_id_map[user_id])] = cities[user_id]
    print "Done reading the city."
    return (gg, city_prop)


def main():
    (gg, temp) = read_file(network_filename)
    pos = sfdp_layout(gg)
    graph_draw(gg, pos=pos, output='sample.png')
    return


if __name__ == '__main__':
    main()
