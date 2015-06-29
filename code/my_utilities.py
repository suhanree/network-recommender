# Utilities for the project.

# Filename: my_utilities.py
# by Suhan Ree
# last edited on 06-18-2015

import numpy as np
# import pandas as pd
import json
import csv
import os
import cPickle as pickle
import networkx as nx


def read_json_file(filename):
    """
    To read the json file and return a json object.
    Input:
        filename: name of the file
    Output:
        user_json: json object for users.
    """
    data_json = []
    with open(filename) as f:
        for line in f:
            data_json.append(json.loads(line))
    return data_json


def find_id_map(data_json, id_label, pickle_filename):
    """
    Given the data and the pickled filename, find the id map.
    If pickled file exists, it will read the info from the file.
    Input:
        data_json: list of json objects from a json file.
        id_label: string label for the id in json object.
        pickle_filename: filename of the pickled file.
    Output:
        id_map: dictionary (key: string id, value: integer id)
    """
    id_map = {}  # empty dict.
    if os.path.exists(pickle_filename):
        print "Reading from the pickled data:", pickle_filename
        with open(pickle_filename, 'r') as f:
            id_map = pickle.load(f)
    else:
        user_id = 0
        for one_data in data_json:
            str_id = one_data[id_label]
            if str_id not in id_map:
                id_map[str_id] = user_id
                user_id += 1
        with open(pickle_filename, 'wb') as f:
            pickle.dump(id_map, f)
    return id_map


def read_dictlist_from_file(filename, format='csv'):
    """
    Read dictionary data with lists (e.g., network) from a file.
    Input:
        filename: name of the file.
        format: default='csv'
    Output:
        my_dict: dictionary that contains info
            (e.g., my_dict[id] for a network is a list of frineds for id)
    """
    my_dict = {}
    with open(filename, 'r') as f:
        if format == 'csv':
            csv_reader = csv.reader(f, delimiter=',')
            for row in csv_reader:
                # row is a list of strings.
                user_id = int(row.pop(0))
                my_dict[user_id] = map(int, row)
    return my_dict


def write_dictlist_to_file(filename, my_dict, format='csv'):
    """
    Write dictionary data with lists (e.g., network) into a file.
    Input:
        filename: name of the file.
        my_dict: dictionary that contains info
            (e.g., my_dict[id] for a network is a list of frineds for id)
        format: default='csv'
    Output:
        None
    """
    with open(filename, 'wb') as f:
        if format == 'csv':
            csv_writer = csv.writer(f)
            for user_id in my_dict:
                csv_writer.writerow([user_id] + my_dict[user_id])
    return


def read_dict_from_file(filename, separator=','):
    """
    Read the dict data from a file.
    Input:
        filename: name of the file.
    Output:
        my_dict: dictionary (e.g., degree info, my_dict[user_id] = int).
    """
    my_dict = {}
    with open(filename, 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        for row in csv_reader:
            my_dict[int(row[0])] = int(row[1])
    return my_dict


def write_dict_to_file(filename, my_dict, separator=','):
    """
    Write the dict data to a file.
    Input:
        filename: name of the file.
        my_dict: dictionary (e.g., degree info, my_dict[user_id] = int)
            saved in a dict.
    Output:
        None
    """
    with open(filename, 'wb') as f:
        for user_id in my_dict:
            f.write(str(user_id) + separator + str(my_dict[user_id]) + '\n')
    return


def write_ratings_to_file(filename, review_df, separator=','):
    """
    Write ratings data to a file.
    Input:
        filename: name of the file.
        review_df: pandas dataframe that contains ratings data.
        separator: character that separates columns.
    Output:
        None
    """
    with open(filename, 'w') as f:
        for index, row in review_df.iterrows():
            f.write(str(row['user_id_int']) + separator +
                    str(row['business_id_int']) + separator +
                    str(row['review_stars']) + '\n')
    return


def convert_to_nx(graph_dict):
    """
    Converting a graph object from dict of lists to networkx object.
    Input:
        graph_dict: graph as dict of lists.
    Output:
        graph_nx: graph as networkx object.
    """
    graph_nx = nx.Graph()
    # Adding nodes.
    graph_nx.add_nodes_from(graph_dict.keys())
    # Adding edges.
    for node in graph_dict:
        for friend in graph_dict[node]:
            if node < friend:
                graph_nx.add_edge(node, friend)
    return graph_nx


def convert_from_nx(graph_nx):
    """
    Converting a graph object from networkx object to a dict of lists
    Input:
        graph_nx: graph as networkx object.
    Output:
        graph_dict: graph as dict of lists.
    """
    graph_dict = {}
    for node in graph_nx.nodes_iter():
        graph_dict[node] = []
        for friend in graph_nx.neighbors(node):
            graph_dict[node].append(friend)
    return graph_dict


def adjacency_matrix(graph_dict):
    """
    Returns the adjacency matrix in np.arary from a graph in dict lof lists.
    Input:
        graph_dict: graph in a dict of lists (it is assumed that user ID's
            are numbered from 0 to size-1 consecutively.
    Output:
        adjacency: adjacency matrix in np.array (at the moment, it is assumed
            that the size is not too big, so that we can use dense matrices).
    """
    size = len(graph_dict)
    adjacency = np.zeros((size, size))
    for user_id in graph_dict:
        for friend_id in graph_dict[user_id]:
            adjacency[user_id, friend_id] = 1
    return adjacency


def reindex_graph(graph_dict, users_id_map=None):
    """
    reindex the graph so that user ID's are indexed from 0 to n-1
    consecutively.
    Input:
        graph_dict: a dict of lists representing a graph.
        users_id_map: map for old user ID to new user ID (if found, already)
                        (default: None)
    Output:
        new_graph_dict: a dict of lists representing the same graph
        users_id_map: returns the map between old and new ID's
                    If we are given an old one, it will be returned.
        num_not_counted: number of users not counted.
    """
    new_graph_dict = {}
    if users_id_map is not None:
        not_counted = set([])
        for u_id in graph_dict:
            if u_id in users_id_map:
                new_graph_dict[users_id_map[u_id]] = []
                for u_id2 in graph_dict[u_id]:
                    if u_id2 in users_id_map:
                        new_graph_dict[users_id_map[u_id]].\
                            append(users_id_map[u_id2])
                    else:
                        not_counted.add(u_id2)
            else:
                not_counted.add(u_id)
        return new_graph_dict, users_id_map, len(not_counted)
    else:
        users_id_map = {}
        new_id = 0
        for u_id in graph_dict:
            if u_id not in users_id_map:
                users_id_map[u_id] = new_id
                new_id += 1
            new_graph_dict[users_id_map[u_id]] = []
            for u_id2 in graph_dict[u_id]:
                if u_id2 not in users_id_map:
                    users_id_map[u_id2] = new_id
                    new_id += 1
                new_graph_dict[users_id_map[u_id]].\
                    append(users_id_map[u_id2])
        return new_graph_dict, users_id_map, 0
