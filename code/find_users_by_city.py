# Find the users for each given city, and find degree distribution
# of these users from this information.

# by Suhan Ree
# last edited on 06-15-2015

import csv
import os
import cPickle as pickle

# Filename for the pickled data of reviews with city info.
review_pickle_filename = '../data/review_dataframe0.pkl'
users_pickle_filename = '../data/users_by_city.pkl'
network_whole_filename = '../data/network.csv'
network_filename = '../data/network%s.csv'
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
        for key in network_dict:
            f.write(key)
            for friend in network_dict[key]:
                f.write(',' + str(key))
            f.write('\n')
    return


def save_degree_to_file(filename, degrees):
    """
    Save the degree data in array to a file.
    Input:
        filename: filename for the degree.
        degrees: degree info saved in an array.
    Output:
        None
    """
    with open(filename, 'wb') as f:
        for deg in degrees:
            f.write(deg + '\n')
    return


def main():
    """
    Find the users for each given city (save them in pickle files),
    and find build networks for given cities and degree distributions.
    """
    if os.path.exists(review_pickle_filename):
        print "Reading from the pickled data:", review_pickle_filename
        with open(review_pickle_filename, 'r') as f:
            review_city_df = pickle.load(f)
    else:
        print "The file,", review_pickle_filename, ", does not exist."
        return

    # Find unique users for 3 cities (Phoenix, Las Vegas, and Montreal), and
    # store them in sets.
    users_by_cities = review_city_df.groupby('business_city_int')\
        .user_id_int.unique()
    users = [set(users_by_cities[1]), set(users_by_cities[5]),
             set(users_by_cities[3])]
    # For Phoenix (0), Las Vegas (1), and Montreal (2).

    # Save them in a pickle file.
    with open(users_pickle_filename, 'wb') as f:
        pickle.dump(users, f)

    # Read the network file (whole) and store the info in dict.
    friends = {}
    with open(network_whole_filename, 'r') as f:
        for line in f:
            # For each line (csv format), find id's.
            # To save the storage and time, friends with id1<id2 are stored.
            # For example, the edge from 1 to 2 will be only stored once.
            ids = map(int, line.strip().split(','))
            # The first id will be a node, and following nodes are friends.
            current_friends = []
            for i, id in enumerate(ids):
                if i:  # Exclude the first entry.
                    current_friends.append(id)
            friends[id] = current_friends

    # Using this info, find network for each cities.
    # We only considers edge belongs to a network if both end users
    # belong to the city.
    friends0 = {}
    friends1 = {}
    friends2 = {}
    for id1 in friends:
        if id1 in users[0]:
            current_friends = []
            for id2 in users[0][id1]:
                if id2 in users[0]:
                    current_friends.append(id2)
            friends0[id1] = current_friends
        if id1 in users[1]:
            current_friends = []
            for id2 in users[1][id1]:
                if id2 in users[1]:
                    current_friends.append(id2)
            friends1[id1] = current_friends
        if id1 in users[2]:
            current_friends = []
            for id2 in users[2][id1]:
                if id2 in users[2]:
                    current_friends.append(id2)
            friends2[id1] = current_friends

    # Now it is time to save network data into csv files.
    save_network_to_file(network_filename % 1, friends0)
    save_network_to_file(network_filename % 2, friends0)
    save_network_to_file(network_filename % 3, friends0)

    # Find degrees and save degree info into files.
    degrees = {}
    with open(network_filename, 'wb') as f:
        csv_writer = csv.writer(f)
        for user_json in user_jsons:
            id = user_id_map[user_json['user_id']]
            friend_list = []
            for friend in user_json['friends']:
                friend_id = user_id_map[friend]
                if id < friend_id:
                    friend_list.append(friend_id)
            degrees[id] = len(friend_list)
            csv_writer.writerow([id] + friend_list)

    # Saving degree information to a file.
    with open(degree_filename, 'wb') as f:
        for id in xrange(n_users):
            f.write(str(degrees[id]) + '\n')
    return


if __name__ == '__main__':
    main()
