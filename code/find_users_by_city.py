# (1) Find the users for each given city based on where each user left reviews.
# (2) For users who left users in multiple users (~5%), use their friends to
#       determine the city using majority. (If tied, choose randomly among
#       tied cities.)
# (3) Find degree distribution and network info for each city.
# Note: Here users without any friend (192,621 out of 366,715) will not
# be used for this analysis.

# Filename: find_users_by_city.py
# by Suhan Ree
# last edited on 06-18-2015

import numpy as np
import os
import cPickle as pickle
import networkx as nx

from my_utilities import write_dictlist_to_file, write_dict_to_file
from my_utilities import read_dictlist_from_file, write_ratings_to_file
from my_utilities import convert_to_nx, convert_from_nx

# Filename for the pickled data of reviews with city info.
# inputs:
review_by_city_dataframe_pickle_filename =\
    '../data/review_by_city_dataframe.pkl'
network_filename = '../data/network.csv'

# outputs:
user_by_city_filename = '../data/user_by_city'
network_city_filename = '../data/network%s.csv'
degree_city_filename = '../data/degrees%s'
review_by_city_filename = '../data/reviews%s'


def find_city(user_id, user_cities, friends, user_city_int):
    """
    Determine the city when the user left reviews in multiple cities.
    Basic idea is that the user will belong to the city where most of
    my friends belong to.
    If there is a tie, choose one city randomly.
    Input:
        user_id: id of the given user (int)
        user_cities: list of cities (lsit of int)
        friends: dict representing the network
        user_city_info: already known city info for users.
    Output:
        city: city (int)
    """
    nfriends = []
    for city in user_cities:
        nfriend = 0
        # print user_id, user_id in friends
        for friend in friends[user_id]:
            if friend in user_city_int and city == user_city_int[friend]:
                nfriend += 1
        nfriends.append(nfriend)
    # To find ties, we use a list. If there is a tie, pick one randomly.
    max = -1
    arg = []
    for i, n in enumerate(nfriends):
        if n > max:
            max = n
            arg = [i]
        elif n == max:
            arg.append(i)
    if len(arg) == 1:
        return (user_cities[arg[0]], 0)  # 0 means not randomly chosen.
    else:
        # 1 means the city is randomly chosen.
        return (user_cities[arg[np.random.randint(len(arg))]], 1)


def main():
    """
    Find the users for each given city (save them in pickle files),
    and find build networks for given cities and degree distributions.
    """
    if os.path.exists(review_by_city_dataframe_pickle_filename):
        print "Reading from the pickled data: " + \
            review_by_city_dataframe_pickle_filename
        with open(review_by_city_dataframe_pickle_filename, 'r') as f:
            review_city_df = pickle.load(f)
    else:
        print "The file, " + review_by_city_dataframe_pickle_filename +\
            ", does not exist."
        return

    # Read the network file (whole) and store the info in dict.
    all_friends = read_dictlist_from_file(network_filename)

    # Find the cities by the user.
    cities_by_user = review_city_df.groupby('user_id_int', sort=True)\
        .business_city_int.unique()

    # Initialize city info for all remaining users as a dict.
    user_city_int = {}

    # We already know that only 5% of users have reviews in more than 1 city.

    # First, assign cities to 95% of users who have reviews in one city.
    for user_id, user_cities in cities_by_user.iteritems():  # For all users.
        if len(user_cities) == 1:
            user_city_int[user_id] = user_cities[0]

    # Second, for users with multiple cities, decide based on
    # friends of the network.
    random_seed = 123
    np.random.seed(random_seed)  # initializning the RNG.
    n_random = 0  # Number of random choices.
    for user_id, user_cities in cities_by_user.iteritems():  # For all users.
        if user_id not in user_city_int:
            (user_city_int[user_id], rand) = find_city(user_id, user_cities,
                                                    all_friends, user_city_int)
            n_random += rand

    # Write the user info into a file.
    write_dict_to_file(user_by_city_filename, user_city_int)

    # Cities we are interested in: Phoenix (0), Las Vegas (1)
    # and Montreal (3), here.
    n_cities = 10

    # Using this info, find network for each cities.
    # We only considers edge belongs to a network if both end users
    # belong to the city.
    # Reviews of all cities will be created and saved here.
    for city in range(n_cities):
        my_net = {}
        for id1 in all_friends:
            if id1 in user_city_int and user_city_int[id1] == city:
                current_friends = []
                for id2 in all_friends[id1]:
                    if id2 in user_city_int and user_city_int[id2] == city:
                        current_friends.append(id2)
                if len(current_friends) > 0:
                    # Only add users with friend in city
                    my_net[id1] = current_friends

        # Using networkx, find the largest component and only keep users in it.
        graph_nx = convert_to_nx(my_net)
        components = nx.connected_component_subgraphs(graph_nx)
        # Find the biggest subgraph.
        biggest_subgraph = None
        max_size = 0
        for comp in components:
            if comp.number_of_nodes() > max_size:
                max_size = comp.number_of_nodes()
                biggest_subgraph = comp

        # Set of users with any friend in the biggest component.
        user_with_friend = set(biggest_subgraph.nodes())

        # Now it is time to save network data into csv files
        # (both the whole network and the biggest component).
        write_dictlist_to_file(network_city_filename % city, my_net)
        write_dictlist_to_file(network_city_filename % (str(city) + 'b'),
                               convert_from_nx(biggest_subgraph))

        # Find degrees and save degree info into files.
        degrees = {}
        for id1 in my_net:
            degrees[id1] = len(my_net[id1])
        write_dict_to_file(degree_city_filename % city, degrees)

        # Reviews for each city
        # First removes businesses out of the city.
        temp_df = review_city_df[review_city_df.business_city_int == city]\
            .drop(['business_city_int'], axis=1)
        # And then, remove users who are out of the city.
        temp_df = temp_df[temp_df.apply(lambda x: x['user_id_int'] in
                                        user_with_friend, axis=1)]
        # Store them in files.
        write_ratings_to_file(review_by_city_filename % city, temp_df)

    print "Number of random choices:", n_random
    return


if __name__ == '__main__':
    main()
