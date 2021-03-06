# Define the Validator class.
# It reads the input file, arrange validation sets (for k-fold validation), and
# find RMSE's.
# Here id's are mapped again, to make user ID's consecutive for each city.

# Filename: validator.py
# by Suhan Ree
# last edited on 06-27-2015

import pandas as pd
import numpy as np
from scipy import sparse
import itertools
from my_utilities import read_dictlist_from_file, reindex_graph


class Validator():
    """
    Class for reading the ratings file, and computing RMSE's for the given model
    """
    def __init__(self, ratings_filename, network_filename, k=5,
                 test_ratio=None):
        """
        Constructor for Validator class.
        It will read the ratings information from the file
        and save it to a sparse matrix (dok format).
        Input:
            ratings_filename: filename for ratings.
            network_filename: filename for the network
                (in csv format with no header)
                ("2,1,3,4" in a line means 2 has friends 1, 3, and 4)
            k: number of folds for cross validation (default: 5)
            test_ratio: ratio of test set (float, 0~1, default: None)
        """
        self.my_network = {}
        self.ratings_filename = ratings_filename
        self.k = int(k)
        self.test_ratio = test_ratio

        # Read the files.
        ratings_contents = pd.read_csv(ratings_filename,
                                       names=['user_id', 'item_id', 'rating'],
                                       header=None)

        # Creating matrices.
        # ratings_mat: ratings info on a matrix
        # ratings_testing: ratings info for testing (test set).
        # list_ratings_val: list of ratings for validation (determined by k)
        # list_ratings_training: list of ratings for training (determined by k)
        u_size = ratings_contents.user_id.nunique()
        i_size = ratings_contents.item_id.nunique()
        self.ratings_train = sparse.dok_matrix((u_size, i_size))
        self.ratings_test = sparse.dok_matrix((u_size, i_size))
        self.list_ratings_val = []
        self.list_ratings_rest = []
        for i in range(self.k):
            self.list_ratings_val.append(sparse.dok_matrix((u_size, i_size)))
            self.list_ratings_rest.append(sparse.dok_matrix((u_size, i_size)))
        # Since no arithmetic will be used for these matrices,
        # dok_matrix (dictionary of keys) will be used.

        # Dict to store ID mapping info.
        self.users_id_map = {}
        self.items_id_map = {}

        # Converting user_id and item_id to make them continuous starting from 0
        u_id = 0  # New id for users starting from 0 to size-1
        i_id = 0  # New id for items starting from 0 to size-1

        # As we read the data, we will perform the division for k folds.
        # And ratings matrices for all folds and outside of folds will be
        # stored in lists of matrices.
        self.n_reviews = ratings_contents.shape[0]

        rating_dict = {}  # dict to store ratings
        for _, row in ratings_contents.iterrows():
            u_temp = int(row.user_id)
            i_temp = int(row.item_id)
            if u_temp not in self.users_id_map:
                self.users_id_map[u_temp] = u_id
                u_id += 1
            if i_temp not in self.items_id_map:
                self.items_id_map[i_temp] = i_id
                i_id += 1
            uu = self.users_id_map[u_temp]
            ii = self.items_id_map[i_temp]
            pair = (uu, ii)
            rating = float(row.rating)

            if pair not in rating_dict:
                rating_dict[pair] = [rating]
            else:
                rating_dict[pair].append(rating)

        # Assigning sets for cross-validations.
        fold_number = []  # Fold number for each review. (-1: for test set)
        for _ in xrange(len(rating_dict)):
            if np.random.rand() < self.test_ratio:
                fold_number.append(-1)
            else:
                fold_number.append(np.random.randint(self.k))
        count = 0
        for pair in rating_dict:
            (uu, ii) = pair
            # In case there are multiple ratings for the same (user, business)
            # pair, take the average.
            rating = np.mean(rating_dict[pair])
            if fold_number[count] == -1:
                self.ratings_test[uu, ii] = rating
            else:
                self.ratings_train[uu, ii] = rating
                for j in range(k):
                    if fold_number[count] == j:  # Inside fold.
                        self.list_ratings_val[j][uu, ii] = rating
                    else:  # Outside fold.
                        self.list_ratings_rest[j][uu, ii] = rating
            count += 1

        # Now read the network.
        temp_network = read_dictlist_from_file(network_filename)
        # But we need to map ID's into consecutive integers.
        self.my_network, users_id_map, not_counted =\
            reindex_graph(temp_network, self.users_id_map)
        if not_counted > 0:
            print "    There are some users not counted for the network:", \
                not_counted
        return

    def validate(self, recommender, use_average=False, run_all=True):
        """
        Perform the K-fold validation using k folds (k times)
        Here we already have split ratings for k folds.
        Input:
            recommender: model
            ratings: ratings matrix for
            use_average: if True, predict using just averages (default: False)
        Output:
            rmse: list of RMSE for each fold.
        """
        # Perform k-fold validation k times.
        list_rmse = []
        list_ratio = []  # Ratio of predictions.
        if run_all:
            for i in range(self.k):
                print "Validation set", i, "started."
                recommender.fit(self.list_ratings_rest[i])
                if use_average:
                    prediction = recommender.pred_average(False, True)
                    (rmse, ratio) =\
                        self.find_rmse_prediction(prediction,
                                                  self.list_ratings_val[i])
                else:
                    (rmse, ratio) =\
                        self.find_rmse(recommender, self.list_ratings_val[i])
                list_rmse.append(rmse)
                list_ratio.append(ratio)
        else:
            print "Validation set", 0, "started."
            recommender.fit(self.list_ratings_rest[0])
            if use_average:
                prediction = recommender.pred_average(False, True)
                (rmse, ratio) =\
                    self.find_rmse_prediction(prediction,
                                              self.list_ratings_val[0])
            else:
                (rmse, ratio) =\
                    self.find_rmse(recommender, self.list_ratings_val[0])
            list_rmse.append(rmse)
            list_ratio.append(ratio)
        return list_rmse, list_ratio

    def find_test_rmse(self, recommender):
        """
        Find the RMSE for the test set
        Input:
            recommender: fitted model.
        Output
            None
        """
        recommender = recommender.fit(self.ratings_train)
        (rmse, ratio) = self.find_rmse(recommender, self.ratings_test)
        return (rmse, ratio)

    def find_rmse(self, recommender, ratings):
        """
        Using the fitted model, compute the RMSE of the validation set.
        Has the feature that if there is no prediction, it will ignore those.
        So it only considers the ones with predictions (useful for network-based
        model).
        Input:
            recommender: model (fitted)
            ratings_val: sparse matrix containing validation set.
        Output:
            rmse: float
            ratio_predicted: ratio of ratigns predicted (float)
        """
        mat = ratings.tocoo()  # coo format is know to be faster when looping.
        n_total = len(mat.row)
        # Loop over non-zero values
        squared_sum = 0.
        n_not_predicted = 0
        n_predicted = 0
        for irow, icol, val in itertools.izip(mat.row, mat.col, mat.data):
            predicted = recommender.pred_one_rating(irow, icol)
            if predicted > 0.0001:
                squared_sum += (val - predicted)**2
                n_predicted += 1
            else:
                n_not_predicted += 1
        if n_predicted == 0:
            return (None, None)
        else:
            return np.sqrt(squared_sum/n_predicted), n_predicted/float(n_total)

    def find_rmse_prediction(self, prediction, ratings):
        """
        Using the prediction matrix, compute the RMSE of the validation set.
        Has the feature that if there is no prediction, it will ignore those.
        So it only considers the ones with predictions (useful for network-based
        model).
        Input:
            prediction: prediction matrix.
            ratings_val: sparse matrix containing validation set.
        Output:
            rmse: float
            ratio_predicted: ratio of ratigns predicted (float)
        """
        mat = ratings.tocoo()  # coo format is know to be faster when looping.
        n_total = len(mat.row)
        # Loop over non-zero values
        squared_sum = 0.
        n_not_predicted = 0
        n_predicted = 0
        for irow, icol, val in itertools.izip(mat.row, mat.col, mat.data):
            if prediction[irow, icol] > 0.0001:
                squared_sum += (val - prediction[irow, icol])**2
                n_predicted += 1
            else:
                n_not_predicted += 1
        if n_predicted == 0:
            return (None, None)
        else:
            return np.sqrt(squared_sum/n_predicted), n_predicted/float(n_total)

    def get_baseline(self):
        """
        Find the baseline RMSE using just averages, which is just the standard
        deviation of the given data.
        Input: None
        Output:
            std: standard deviation
        """
        return self.ratings_train.tocoo().data.std()

    def get_network(self):
        """
        Return the network in a dict of lists
        """
        return self.my_network

    def get_matrix_train(self):
        """
        Return the ratigns matrix of a train set.
        """
        return self.ratings_train

    def run_fit(self, model):
        """
        Run fit method for the given model (mostly for testing purpose)
        """
        model.fit(self.ratings_train)
