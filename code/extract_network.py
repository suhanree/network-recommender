# Extracting netwrok data from the user json file.

# by Suhan Ree
# last edited on 06-15-2015

# import pandas as pd
# import numpy as np
# import json
import csv
import os
import cPickle as pickle

from my_utilities import read_json_file

# Filename for the pickled data of user_id and numbered id map.
userdata_filename = '../data/yelp_academic_dataset_user.json'
pickle_filename = '../data/user_id_map.pkl'
network_filename = '../data/newtork_data.csv'
degree_filename = '../data/degrees'


def main():
    """
    From the json file, it will extract the network data, and saves them
    into a csv file.
    """
    # Now we have to read from a data file in json.
    # user_json should be the list of json objects.
    user_jsons = read_json_file(userdata_filename)
    # Each user will be assigned with an integer instead of string user_id's.
    # This mapping data will be stored in a dictionary, and will be pickled.
    # But if this info is already pickled it will just read from it.
    n_users = None   # Total number of users.
    if os.path.exists(pickle_filename):
        print "Reading from the pickled data..."
        with open(pickle_filename, 'r') as f:
            user_id_map = pickle.load(f)
        n_users = len(user_id_map)
    else:
        user_id_map = {}
        id = 0
        for user_json in user_jsons:
            user_id = user_json['user_id']
            if user_id not in user_id_map:
                user_id_map[user_id] = id
                id += 1
        n_users = id    # Number of all users.
        with open(pickle_filename, 'wb') as f:
            pickle.dump(user_id_map, f)

    # Now it is time to save network data into csv file.
    degrees = {}
    with open(network_filename, 'wb') as f:
        csv_writer = csv.writer(f)
        for user_json in user_jsons:
            id = user_id_map[user_json['user_id']]
            friend_list = []
            for friend in user_json['friends']:
                friend_list.append(user_id_map[friend])
            degrees[id] = len(friend_list)
            csv_writer.writerow([id] + friend_list)

    # Saving degree information to a file.
    with open(degree_filename, 'wb') as f:
        for id in xrange(n_users):
            f.write(str(degrees[id]) + '\n')
    return


if __name__ == '__main__':
    main()
