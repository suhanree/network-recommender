# Find the users for each given city, and find degree distribution
# of these users from this information.

# by Suhan Ree
# last edited on 06-16-2015

import numpy as np
import csv
import os
import cPickle as pickle

# Filename for the pickled data of reviews with city info.
review_city_dataframe_pickle_filename = '../data/review_dataframea.pkl'
user_by_city_pickle_filename = '../data/user_by_city.pkl'
network_filename = '../data/network.csv'
network_city_filename = '../data/network%s.csv'
degree_filename = '../data/degrees%s'


def save_network_to_file(filename, network_dict):
    """
    Save the network data in dict to a csv file.
    Input:
        filename: filename for the network.
        network_dict: network info saved in dict.
    Output:
        None
    """
    with open(filename, 'wb') as f:
        csv_writer = csv.writer(f)
        for key in network_dict:
            csv_writer.writerow([key] + network_dict[key])
    return


def save_degree_to_file(filename, degrees):
    """
    Save the degree data in array to a file.
    Input:
        filename: filename for the degree.
        degrees: degree info saved in a dict
    Output:
        None
    """
    with open(filename, 'wb') as f:
        for id in degrees:
            f.write(str(id) + ',' + str(degrees[id]) + '\n')
    return


def find_city(user_id, user_cities, friends, user_city_info):
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
    city_info = user_city_info.copy()
    nfriends = []
    for city in user_cities:
        nfriend = 0
        #print user_id, user_id in friends
        for friend in friends[user_id]:
            if city_info[friend] > -1 and city == city_info[friend]:
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
        return user_cities[arg[0]]
    else:
        # print arg, user_cities, nfriends
        return user_cities[arg[np.random.randint(len(arg))]]


def main():
    """
    Find the users for each given city (save them in pickle files),
    and find build networks for given cities and degree distributions.
    """
    if os.path.exists(review_city_dataframe_pickle_filename):
        print "Reading from the pickled data: " + \
            review_city_dataframe_pickle_filename
        with open(review_city_dataframe_pickle_filename, 'r') as f:
            review_city_df = pickle.load(f)
    else:
        print "The file, " + review_city_dataframe_pickle_filename +\
            ", does not exist."
        return

    # Read the network file (whole) and store the info in dict.
    all_friends = {}
    with open(network_filename, 'r') as f:
        for line in f:
            # For each line (csv format), find id's.
            ids = map(int, line.strip().split(','))
            # The first id will be a node, and following nodes are friends.
            current_friends = []
            for i, id in enumerate(ids):
                if i:  # Exclude the first entry.
                    current_friends.append(id)
            all_friends[ids[0]] = current_friends

    # Find the cities by the user.
    cities_by_user = review_city_df.groupby('user_id_int', sort=True)\
        .business_city_int.unique()
    # Initialize city info as -1.
    user_city_int = -np.ones(len(cities_by_user))
    # We already know that only 5% of users have reviews in more than 1 city.
    # First, assign cities to 95% of users who have reviews in one city.
    for user_id, user_cities in enumerate(cities_by_user):  # For all users.
        if len(user_cities) == 1:
            user_city_int[user_id] = user_cities[0]
    # Second, for users with multiple cities, decide based on
    # friends of the network.
    for user_id, user_cities in enumerate(cities_by_user):  # For all users.
        #print 'a', user_id, user_cities
        if len(user_cities) > 1:
            user_city_int[user_id] = find_city(user_id, user_cities,
                                               all_friends, user_city_int)

    # Cities we are interested in: Phoenix, Las Vegas and Montreal, here.
    cities = [0, 1, 3]
    n_cities = len(cities)

    # Find users for cities and store them in sets, save them in a pickle file.
    users = [set(np.where(user_city_int == i)[0]) for i in cities]
    print len(users[0]), len(users[1]), len(users[2])
    with open(user_by_city_pickle_filename, 'wb') as f:
        pickle.dump(users, f)

    # Using this info, find network for each cities.
    # We only considers edge belongs to a network if both end users
    # belong to the city.
    friends = [{}] * n_cities
    for i in range(n_cities):
        for id1 in all_friends:
            if id1 in users[i]:
                current_friends = []
                for id2 in all_friends[id1]:
                    if id2 in users[i]:
                        current_friends.append(id2)
                friends[i][id1] = current_friends
        # Now it is time to save network data into csv files.
        save_network_to_file(network_city_filename % cities[i], friends[i])

    # Find degrees and save degree info into files.
    for i in range(n_cities):
        degrees = {}
        for id in friends[i]:
            degrees[id] = len(friends[i][id])
        save_degree_to_file(degree_filename % cities[i], degrees)
    return


if __name__ == '__main__':
    main()
