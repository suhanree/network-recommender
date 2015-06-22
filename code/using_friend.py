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
    def __init__(self, n_ratings_limit=1, n_friend_limit_ratio = 1.0,
                 network_filename):
        """
        Constructor of the class
        Input:
            n_ratings_limit: lower limit for the number of ratings
                for prediction (default: 1)
            n_friend_limit_ratio: upper limit for the ratio for the number
                of friends for prediction (default: 1.0)
            network_filename: filename for the network
                (in csv format with no header)
                ("2,1,3,4" in a line means 2 has friends 1, 3, and 4)
        """
        self.n_ratings_limit = n_ratings_limit
        self.n_friend_limit_ratio = n_friend_limit_ratio

        self.ratings_mat = None  # will be obtained in fit method.
        self.ratings_mat_coo = None  # will be obtained in fit method.
        self.my_network = read_dictlist_from_file(network_filename)
        self.my_friends = {}  # will be found in fit method.
        self.my_friends2 = {}  # {friends of friends} - {friends}
                                # (store only additional friends).

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

        n_friends_limit = self.n_friend_limit_ratio * self.n_users
        # Finding friends and friends of friends for every user.
        for user_id in self.my_network:
            temp_friends = self.my_network[user_id]
            if len(temp_friends) > n_friends_limit:
                    self.my_friend[user_id] = \
                        self.pick_random(temp_friends, n_friends_limit)
                    self.my_friends2[user_id] = set([])
                    countinue  # No need to find friends of friends.
            else:
                self.my_friends[user_id] = set(temp_friends)

            temp_friends2 = []
            temp_friends2_set = set([temp_friends])
            for friend in self.my_network[user_id]:
                for friend2 in self.my_network[friend]:
                    if friend2 not in temp_friends2_set:
                        temp_friends2.append(friend2)
                        temp_friends2_set.add(friend2)
            if len(temp_friends2) > n_friends_limit - len(temp_friends):
                    self.my_friend2[user_id] = \
                        self.pick_random(temp_friends2,
                                         n_friends_limit - len(temp_friends))
            else:
                self.my_friends2[user_id] = set([temp_friends2])


    def pred_one_rating(self, user_id, item_id):
        """
        Predict for one user-item pair
        """
        # Find friends who rated the item and just averages them.
        # If no friend has reviewed the same item, return 0.
        count = 0
        rating_sum = 0
        for irow, icol, val in izip(self.ratings_mat_coo.row,
                                   self.ratings_mat_coo.col,
                                   self.ratings_mat_coo.data):
            if irow in my_friends[user_id] and icol == item_id:
                rating_sum += val
                count += 1
        if count >= self.n_ratings_limit:
            return rating_sum/float(count)
        else:
            return 0


    def pred_one_user(self, user_id):
        """
        Predict for one user.
        Output:
            predicted: np.array (1d)
        """
        # Find friends who rated the item and just averages them.
        # If no friend has reviewed the same item, return 0.
        prediction = np.zero(self.n_items)
        counts = np.zero(self.n_items, dtype='int')
        for irow, icol, val in izip(self.ratings_mat_coo.row,
                                   self.ratings_mat_coo.col,
                                   self.ratings_mat_coo.data):
            if irow in my_friends[user_id]:
                prediction[icol] += val
                counts[icol] += 1
        # Find averages for all items except the ones with no ratings.
        for icol in xrange(self.n_items):
            if counts[icol] >= self.n_ratings_limit:
                prediction[icol] = prediction[icol] / counts[icol]
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
        items_not_predicted = set(np.where(pred_output == 0)[0])
        items_rated_by_this_user = set(self.ratings_mat_coo[
            np.where(self.ratings_mat_coo.row == user_id)[0]])
        items_predicted =\
            np.array([i for i in xrange(self.n_items)
                      if i not in items_rated_by_this_user and
                        i not in items_not_predicted])
        return np.argsort(pred_output[items_predicted])[-num:][::-1]
