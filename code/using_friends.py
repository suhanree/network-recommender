# Classes that usese friends for recommendations.

# by Suhan Ree
# last edited on 06-21-2015

import numpy as np
import itertools


class Using_Friends():
    """
    Class that uses friends or friends of friends for recommendation.
    It uses information of friends from the given network.
    """
    def __init__(self, my_network,
                 n_ratings_lower_limit=3, n_ratings_upper_limit=100,
                 if_average=False):
        """
        Constructor of the class
        Input:
            my_network: network info in the form of dict of lists.
            n_ratings_lower_limit: lower limit for the number of ratings
                for prediction; should be 1 or higher  (default: 3)
            n_ratings_upper_limit: upper limit for the number
                of friends for prediction; should be an integer (>= 0)
                (default: 100)
            if_average: if True, give average item average as a prediction.
                If False, do not predict.
        """
        self.n_ratings_lower_limit = n_ratings_lower_limit
        self.n_ratings_upper_limit = n_ratings_upper_limit
        self.if_average = if_average

        self.ratings_mat = None  # will be obtained in fit method.
        self.ratings_mat_coo = None  # will be obtained in fit method.
        self.my_network = my_network
        self.my_friends = {}  # will be found in fit method (dict of sets).
        self.my_friends2 = {}  # {friends of friends} - {friends} (dict of sets)
                                # (store only additional friends).
        self.rows_nonzero = None  # Rows with nonzero items given an item
                                # (list of lists).
        self.average_ratings_item = None

        self.n_users = None
        self.n_items = None
        self.n_rated = None

        # Finding friends and friends of friends for every user.
        # And store them in sets for easier searches.
        # self.my_network contains information for friends in a dict.
        for user_id in self.my_network:
            # Add the friends (ones that are connected).
            if self.n_ratings_upper_limit == 0:  # Don't need to do any, if 0.
                self.my_friends[user_id] = set([])
            else:
                self.my_friends[user_id] = set(self.my_network[user_id])
        return
                            

    def fit(self, ratings_mat):
        self.ratings_mat = ratings_mat.copy()  # in dok (dictionary) format.
        self.ratings_mat_coo = ratings_mat.tocoo()  # Converting to coo format.
                                 # coo is better for looping over nonzero values.
        self.n_users, self.n_items = ratings_mat.shape
        self.n_rated = self.ratings_mat_coo.row.size
        print "    problem size:", self.n_users, self.n_items, self.n_rated


        # Here we also find rows with non-zero ratings for given item.
        # It will be more efficient for predictions to have these ready
        # even though it uses more memory.
        self.rows_nonzero = []
        for icol in xrange(self.n_items):
            self.rows_nonzero.append([])
        ratings_sum = np.zeros(self.n_items)
        for irow, icol, val in itertools.izip(self.ratings_mat_coo.row,
                                         self.ratings_mat_coo.col,
                                         self.ratings_mat_coo.data):
            self.rows_nonzero[icol].append(irow)
            ratings_sum[icol] += val

        # Find the average rating for each item.
        self.average_ratings_item = np.zeros(self.n_items)
        for icol in xrange(self.n_items):
            self.average_ratings_item[icol] =\
                ratings_sum[icol] / len(self.rows_nonzero[icol])
        #print self.average_ratings_item
        """
        # For test purpose.
        with open('ratings_by_item', 'w') as f:
            for irow, icol in itertools.izip(self.ratings_mat_coo.row,
                                self.ratings_mat_coo.col):
                ratings_friends = []
                ratings_friends2 = []
                ratings_all = []
                for user in self.rows_nonzero[icol]:
                    if user != irow:
                        ratings_all.append(int(self.ratings_mat[user, icol]))
                        if user in self.my_friends[irow]:
                            ratings_friends.append(int(self.ratings_mat[user,
                                        icol]))
                        if user in self.my_friends2[irow]:
                            ratings_friends2.append(int(self.ratings_mat[user,
                                        icol]))
                f.write(
                        str(int(self.ratings_mat[irow, icol])) + ' ' + 
                        str(np.mean(ratings_all)) + ' ' +
                        str(np.mean(ratings_friends)) + ' ' +
                        str(np.mean(ratings_friends2)) + ' ' + 
                        str(len(self.rows_nonzero[icol])-1) + ' ' +
                        str(len(ratings_friends)) + ' ' +
                        str(len(ratings_friends2)) + ' ' +
                        str(irow) + ' ' + str(icol) + ' ' +
                        '\n')
                f.write( ' '.join(map(str, ratings_all)) + '\n')
                f.write( ' '.join(map(str, ratings_friends)) + '\n')
                f.write( ' '.join(map(str, ratings_friends2)) + '\n')
        """
        print "    Fitting done."
        #print self.n_ratings_lower_limit
        #print self.n_ratings_upper_limit

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
        #print 'a', len(rows)
        # If there is no rating to use for prediction, no need to search thru friends.
        if len(rows) < self.n_ratings_lower_limit:  
            if self.if_average:
                return self.average_ratings_item[item_id]
            else:
                return 0
        temp_ratings = []
        for irow in rows:  # For all rows with non-zero ratings.
            if irow in self.my_friends[user_id]:
                temp_ratings.append(self.ratings_mat[irow, item_id])
        temp_ratings2 = self.pick_random(temp_ratings, self.n_ratings_upper_limit)
        #print len(temp_ratings2)
        if len(temp_ratings2) < self.n_ratings_lower_limit:
            if self.if_average:
                return self.average_ratings_item[item_id]
            else:
                return 0
        else:
            return np.mean(temp_ratings)


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


    def pick_random(self, ratings_list, n_ratings_limit, seed=789):
        """
        Pick a certain number of friends from a list of friends randomly.
        Input:
            ratings_list: a list of ratings.
            n_ratings_limit: the number of ratings to be picked.
            seed: random seed to be used (default: 789)
        Output:
            new_ratings: a list of ratings with n_ratings_limit ratings.
        """
        # If the number of ratings is already less than the given number,
        # just return the set of the list.
        if len(ratings_list) <= n_ratings_limit:
            return ratings_list

        np.random.seed(seed)  # Set the seed as given
        return np.random.choice(ratings_list, size=n_ratings_limit, replace=False)
