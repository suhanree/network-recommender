# Make a joined dataframe from user, business, and review json files..
# Filename: make_joined_dataframe.py

# by Suhan Ree
# last edited on 06-15-2015

import pandas as pd
# import numpy as np
import json
import csv
import os
import cPickle as pickle

from my_utilities import read_json_file

# Filename for the pickled data of user_id and numbered id map.
user_filename = '../data/yelp_academic_dataset_user.json'
user_pickle_filename = '../data/user_id_map.pkl'
business_filename = '../data/yelp_academic_dataset_business.json'
business_pickle_filename = '../data/business_id_map.pkl'
review_filename = '../data/yelp_academic_dataset_review_notext.json'

dataframes_pickle_filename = '../data/dataframes.pkl'
joined_dataframe_pickle_filename = '../data/joined_dataframe.pkl'


def find_id_map(data_json, id_label, pickle_filename):
    """
    Given the data and the pickled filename, find the id map.
    If pickled file exists, it will read it from the file.
    Input:
        data_json: list of json objects from a json file.
        id_label: string label for the id in json object.
        pickle_filename: filename of the pickled file.
    Output:
        id_map: dictionary (key: string id, value: integer id)
    """
    id_map = {}  # empty dict.
    if os.path.exists(pickle_filename):
        print "Reading from the pickled data:" + pickle_filename
        with open(pickle_filename, 'r') as f:
            id_map = pickle.load(f)
    else:
        id = 0
        for one_data in data_json:
            str_id = one_data[id_label]
            if str_id not in id_map:
                id_map[str_id] = id
                id += 1
        with open(pickle_filename, 'wb') as f:
            pickle.dump(id_map, f)
    return id_map


def main():
    """
    From 3 json files, it will combine data and create a new dataframe,
    and store it in a pickled file.
    """
    if os.path.exists(dataframes_pickle_filename):
        with open(dataframes_pickle_filename, 'r') as f:
            (user_df, business_df, review_df) = pickle.load(f)
    else:
        # Read json file for user.
        user_jsons = read_json_file(user_filename)
        # Each user will be assigned with an integer instead of string user_id
        # This mapping data will be stored in a dictionary, and will be pickled.
        # But if this info is already pickled it will just read from it.
        user_id_map = find_id_map(user_jsons, 'user_id', user_pickle_filename)
        n_users = len(user_id_map)   # Total number of users.

        # For each user, pick only necessary columns.
        for user in user_jsons:
            original_keys = user.keys()
            user['user_id_int'] = user_id_map[user['user_id']]
            user['user_review_count'] = int(user['review_count'])
            user['user_stars'] = float(user['average_stars'])
            # delete all other values not necessary here.
            for key in original_keys:
                user.pop(key, None)

        # Convert the new list into the dataframe.
        user_df = pd.read_json(json.dumps(user_jsons))
        print "Done for users with %s users." % n_users

        # Read json file for business.
        business_jsons = read_json_file(business_filename)
        business_id_map = find_id_map(business_jsons, 'business_id',
                                    business_pickle_filename)
        n_businesses = len(business_id_map)   # Total number of businesses.

        # For each business, pick only necessary columns.
        categories_map = {}  # Storing category information in a separate dict.
        for business in business_jsons:
            original_keys = business.keys()
            business_id = business_id_map[business['business_id']]
            categories_map[business_id] = business['categories']
            business['business_id_int'] = business_id
            business['business_review_count'] = int(business['review_count'])
            business['business_stars'] = float(business['stars'])
            business['business_type'] = business['type']
            business['business_city'] = business['city']
            business['business_latitude'] = float(business['latitude'])
            business['business_longitude'] = float(business['longitude'])
            # delete all other values not necessary here.
            for key in original_keys:
                business.pop(key, None)

        # Convert the new list into the dataframe.
        business_df = pd.read_json(json.dumps(business_jsons))
        print "Done for businesses with %s businesses." % n_businesses

        # Read json file for reviews.
        review_jsons = read_json_file(review_filename)
        n_reviews = len(review_jsons)   # Total number of reviews.

        # For each user, pick only necessary columns.
        for review in review_jsons:
            original_keys = review.keys()
            review['business_id_int'] = business_id_map[review['business_id']]
            review['user_id_int'] = user_id_map[review['user_id']]
            review['review_stars'] = int(review['stars'])
            # delete all other values not necessary here.
            for key in original_keys:
                review.pop(key, None)

        # Convert the new list into the dataframe.
        review_df = pd.read_json(json.dumps(review_jsons))
        print "Done for reviews with %s reviews." % n_reviews

        # Storing these dataframes as a pickled file.
        with open(dataframes_pickle_filename, 'wb') as f:
            pickle.dump((user_df, business_df, review_df), f)
    return


if __name__ == '__main__':
    main()
