# Make a joined dataframe from user, business, and review json files..
# Filename: make_joined_dataframe.py

# by Suhan Ree
# last edited on 06-17-2015

import pandas as pd
# import numpy as np
import json
import os
import cPickle as pickle
from collections import Counter
from sklearn.cluster import KMeans

from my_utilities import read_json_file, find_id_map, write_dictlist_to_file

# Filename for the pickled data of user_id and numbered id map.
user_filename = '../data/yelp_academic_dataset_user.json'
user_pickle_filename = '../data/user_id_map.pkl'
business_filename = '../data/yelp_academic_dataset_business.json'
business_pickle_filename = '../data/business_id_map.pkl'
review_filename = '../data/yelp_academic_dataset_review_notext.json'
degree_filename = '../data/degrees'

dataframes_pickle_filename = '../data/dataframes.pkl'
reduced_dataframes_pickle_filename = '../data/reduced_dataframes.pkl'
categories_business_filename = '../data/categories_business'
review_by_city_dataframe_pickle_filename =\
    '../data/review_by_city_dataframe.pkl'


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
            business['business_city'] = business['city']
            business['business_latitude'] = float(business['latitude'])
            business['business_longitude'] = float(business['longitude'])
            # delete all other values not necessary here.
            for key in original_keys:
                business.pop(key, None)

        # Writing category info into a file.
        write_dictlist_to_file(categories_business_filename, categories_map)

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
            review['review_date'] = review['date']
            # delete all other values not necessary here.
            for key in original_keys:
                review.pop(key, None)

        # Convert the new list into the dataframe.
        review_df = pd.read_json(json.dumps(review_jsons))
        print "Done for reviews with %s reviews." % n_reviews

        # Storing these dataframes as a pickled file.
        with open(dataframes_pickle_filename, 'wb') as f:
            pickle.dump((user_df, business_df, review_df), f)

    # Now we find data frames for reviews for specific cities.
    # From the business locations, we find ten cities using k-Means.
    km = KMeans(10, n_jobs=8)
    X = business_df[['business_latitude', 'business_longitude']].values
    y = km.fit_predict(X)
    y_counter = Counter(y).most_common()
    sorted_y = [c[0] for c in y_counter]
    sorted_y_map = {}
    for i in range(10):
        sorted_y_map[sorted_y[i]] = i
    # Store city info as a column. To make city numbers deterministic, City
    # numbers are ordered from the largest num of businesses to the smallest.
    business_df['business_city_int'] = map(lambda i: sorted_y_map[i], y)
    # city_names = ['Phoenix', 'Las Vegas', 'Charlotte', 'Montreal',
    #               'Edinburgh', 'Pittsburgh',  'Madison', 'Karlsruhe',
    #               'Urbana-Champaign', 'Waterloo']

    # Here we drop all users without any friend.
    # First, we need degree info already found.
    my_degrees = pd.read_csv("../data/degrees",
                             names=['user_id', 'degree'], header=None)

    # A set containing users with at least one friend.
    users2_set = set(my_degrees[my_degrees.degree > 0].user_id.values)

    # Create all dataframes that only have data with users with at least one
    # friend.
    # First, find users first.
    user_df2 = user_df[user_df.apply(lambda x: x['user_id_int'] in users2_set,
                                     axis=1)]
    # Second, find reviews done by these users.
    review_df2 = review_df[review_df
            .apply(lambda x: x['user_id_int'] in users2_set, axis=1)]
    # Lastly, find businesses that only these reviews are done for.
    businesses2_set = set(review_df2.business_id_int.unique())
    business_df2 = business_df[business_df
            .apply(lambda x: x['business_id_int'] in businesses2_set, axis=1)]

    # Dataframe with the reviews (with business city).
    review_city_df2 = business_df2[['business_id_int', 'business_city_int']]\
            .merge(review_df2, on=['business_id_int'], how='inner')

    # Store reduced dataframes to pickle file.
    with open(reduced_dataframes_pickle_filename, 'wb') as f:
        pickle.dump((user_df2, business_df2, review_df2, review_city_df2), f)
    with open(review_by_city_dataframe_pickle_filename, 'wb') as f:
        pickle.dump(review_city_df2, f)

    return


if __name__ == '__main__':
    main()
