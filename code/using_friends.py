# Classes that usese friends for recommendations.

# by Suhan Ree
# last edited on 06-21-2015

import numpy as np
import itertools
import sys


class Using_Friends():
    """
    Class that uses friends or friends of friends for recommendation.
    It uses information of friends from the given network.
    """
    def __init__(self, my_network,
                 n_ratings_limit=1, n_friend_limit_ratio=0.5,
                 weight_for_depth2=0.5):
        """
        Constructor of the class
        Input:
            my_network: network info in the form of dict of lists.
            n_ratings_limit: lower limit for the number of ratings
                for prediction; should be 1 or higher  (default: 1)
            n_friend_limit_ratio: upper limit for the ratio for the number
                of friends for prediction; should be a float between 0 and 1
                (default: 0.5)
            weight_for_depth2: if friends of friends are used for recommendation
                the weight can be given; should be a float between 0 and 1
                (default: 0.5)
        """
        self.n_ratings_limit = n_ratings_limit
        self.n_friend_limit_ratio = n_friend_limit_ratio
        self.weight_for_depth2 = weight_for_depth2

        self.ratings_mat = None  # will be obtained in fit method.
        self.ratings_mat_coo = None  # will be obtained in fit method.
        self.my_network = my_network
        self.my_friends = {}  # will be found in fit method (dict of sets).
        self.my_friends2 = {}  # {friends of friends} - {friends} (dict of sets)
                                # (store only additional friends).
        self.rows_nonzero = []  # Rows with nonzero items given an item
                                # (list of lists).

        self.n_users = None
        self.n_items = None
        self.n_rated = None


    def fit(self, ratings_mat):
        self.ratings_mat = ratings_mat.copy()  # in dok (dictionary) format.
        self.ratings_mat_coo = ratings_mat.tocoo()  # Converting to coo format.
                          # coo is better for looping over nonzero values.
        self.n_users, self.n_items = ratings_mat.shape
        self.n_rated = self.ratings_mat_coo.row.size
        print "    problem size:", self.n_users, self.n_items, self.n_rated

        # Get the upper limit for the number of friends & friends of friends
        n_friends_limit = self.n_friend_limit_ratio * self.n_users

        # Finding friends and friends of friends for every user.
        # And store them in sets for easier searches.
        # self.my_network contains information for friends in a dict.
        for user_id in self.my_network:
            # First, add the friends of depth 1 (ones that are connected).
            # temporary list (not copied).
            temp_friends = self.my_network[user_id]
            if len(temp_friends) > n_friends_limit:
                    self.my_friend[user_id] = \
                        self.pick_random(temp_friends, n_friends_limit)
                        # this will returns a set of friends
                    self.my_friends2[user_id] = set([])  # empty set
                    continue  #No need to find friends of friends for this user
            else:
                self.my_friends[user_id] = set(temp_friends)

            # Second, we add friends of depth 2, if needed.
            temp_friends2 = []
            temp_friends2_set = set(temp_friends)  # To be used for checking.
            temp_friends2_set.add(user_id)  # Don't want to add this user.
            for friend in temp_friends:
                for friend2 in self.my_network[friend]:
                    if friend2 not in temp_friends2_set:
                        temp_friends2.append(friend2)
                        temp_friends2_set.add(friend2)
            if len(temp_friends2) > n_friends_limit - len(temp_friends):
                    self.my_friends2[user_id] = \
                        self.pick_random(temp_friends2,
                                         n_friends_limit - len(temp_friends))
            else:
                self.my_friends2[user_id] = set(temp_friends2)

        # Here we also find rows with non-zero ratings for given item.
        # It will be more efficient for predictions to have these ready
        # even though it uses more memory.
        for icol in xrange(self.n_items):
            self.rows_nonzero.append([])
        for irow, icol in itertools.izip(self.ratings_mat_coo.row,
                               self.ratings_mat_coo.col):
            self.rows_nonzero[icol].append(irow)
            # it's OK, because the order doesn't matter.

        print "    Fitting done."
        return self  # Return the fitted self in case.


    def pred_one_rating(self, user_id, item_id):
        """
        Predict for one user-item pair
        Find friends & friends of friends who rated the item, and get average
        of them (if friends of friends are used, the weight will be used).
        If neither a friend nor a friend of a friend has reviewed the item,
        then it will return 0.
        Input:
            user_id, item_id: ID's for the given user and item.
        Output:
            rating: predicted rating.
        """
        # For already rated user-item pair.
        if self.ratings_mat[user_id, item_id] != 0:
            return self.ratings_mat[user_id, item_id]

        # Rows for non-zero ratings for the given item.
        rows = self.rows_nonzero[item_id]
        if len(rows) < self.n_ratings_limit:  # No need to search thru friends.
            return 0
        count = 0.
        rating_sum = 0.
        for irow in rows:  # For all rows with non-zero ratings.
            if irow in self.my_friends[user_id]:
                rating_sum += self.ratings_mat[irow, item_id]
                count += 1.   # weight is 1 for direct friends.
            elif irow in self.my_friends2[user_id]:
                rating_sum += self.ratings_mat[irow, item_id]\
                    * self.weight_for_depth2
                count += self.weight_for_depth2
        if count >= self.n_ratings_limit:
            return rating_sum/count
        else:
            return 0


    def pred_one_user(self, user_id):
        """
        Predict for ratings for all itmes for one user (except the ones that
        are rated already).
        Find friends & friends of friends who rated the item and get averages
        of them (if friends of friends are used, the weight will be used).
        If neither a friend nor a friend of a friend has reviewed the item,
        then it will return 0.
        Input:
            user_id, item_id: ID's for the given user and item.
        Predict for one user.
        Output:
            predicted: np.array (1d)
        """
        prediction = np.zeros(self.n_items)  # Initialize predictions.
        counts = np.zeros(self.n_items, dtype='int')
        for item_id in xrange(self.n_items):
            prediction[item_id] = self.pred_one_rating(user_id, item_id)
            # There is no efficiency lost, by calling this function one by one.
        return prediction


    def pred_all(self):
        """
        Predict for all user-item pairs.
        Output:
            predicted: np.array (2d)
        """
        return None  # not implemeted here.


    def top_n_recs(self, user_id, num):
        """
        Find top items for a given user based on friends.
        Input:
            user_id: user for recommendation.
            num: number of recommendations.
        Output:
            recom: list of itmes for recommendation.
        """
        pred_output = self.pred_one_user(user_id)  # 1d np.array
        items_predicted = np.ones(self.n_items, dtype='bool')
        for icol in xrange(self.n_items):
            if self.ratings_mat[user_id, icol]:
                items_predicted[icol] = False
        return np.argsort(pred_output[items_predicted])[-num:][::-1]


    def pick_random(self, friends_list, n_friends_limit, seed=789):
        """
        Pick a certain number of friends from a list of friends randomly.
        Input:
            friends_list: a list of friends.
            n_friends_limit: the number of friends to be picked.
            seed: random seed to be used (default: 789)
        Output:
            friends_set: a set of friends with n_friends_limit friends.
        """
        # If the number of friends is already less than the given number,
        # just return the set of the list.
        if len(friends_list) <= n_friends_limit:
            return set(friends_list)

        np.random.seed(seed)  # Set the seed as given
        return set(np.random.choice(friends_list, size=n_friends_limit,
                                    replace=False))
