# To run the recommender system.

# by Suhan Ree
# last edited on 06-22-2015

import sys
import pandas as pd
import numpy as np
from scipy import sparse
import itertools
from factorization import Matrix_Factorization  # , MetaPredictor
from using_friends import Using_Friends
from my_utilities import read_dictlist_from_file, reindex_graph

# Filenames needed.
ratings_filename = "../data/reviews" + sys.argv[1]
network_filename = "../data/network" + sys.argv[1] + "b.csv"
#ratings_filename = "sample_ratings"
#network_filename = "sample_network"


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
                            names=['user_id', 'item_id', 'rating'], header=None)

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
            self.list_ratings_rest.append(sparse.dok_matrix((u_size,
                                                                 i_size)))
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
        fold_number = []  # Fold number for each review. (-1: for test set)
        for _ in xrange(self.n_reviews):
            if np.random.rand() < self.test_ratio:
                fold_number.append(-1)
            else:
                fold_number.append(np.random.randint(self.k))

        count = 0
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
            rating = float(row.rating)
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
        """
        for j in range(k):
            print j, len(self.list_ratings_val[j])
            print j, len(self.list_ratings_rest[j])
        print len(self.ratings_test)
        print len(self.ratings_train)
        print self.users_id_map
        print self.items_id_map
        print 'test', self.ratings_test
        print 'train', self.ratings_train
        for i in range(self.k):
            print 'val', self.list_ratings_val[i]
            print 'rest', self.list_ratings_rest[i]
        """

        # Now read the network.
        temp_network = read_dictlist_from_file(network_filename)
        # But we need to map ID's into consecutive integers.
        self.my_network, users_id_map, not_counted = reindex_graph(temp_network,
                                                            self.users_id_map)
        if not_counted > 0:
            print "    There are some users not counted for the network:", \
                not_counted
        return


    def validate(self, recommender, use_average=False):
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
        for i in range(self.k):
            print "Validation set", i, "started."
            recommender.fit(self.list_ratings_rest[i])
            if use_average:
                prediction = recommender.pred_average(False, True)
                (rmse, ratio) = self.find_rmse_prediction(prediction,
                                                self.list_ratings_val[i])
            else:
                (rmse, ratio) = self.find_rmse(recommender,
                                            self.list_ratings_val[i])
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
            #print irow, icol, val, recommender.pred_one_rating(irow, icol)
            predicted = recommender.pred_one_rating(irow, icol)
            #print irow, icol, val-predicted
            if predicted > 0.0001:
                squared_sum += (val - predicted)**2
                n_predicted += 1
            else:
                n_not_predicted += 1
            #print irow, icol, val, recommender.pred_one_rating(irow, icol)
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


def main():
    """
    To run the recommender model.
    """
    # Create the Validator object.
    # k: number of folds for cross validation.
    k = 5
    val = Validator(ratings_filename, network_filename, k, 0.)
    """
    my_rec = Matrix_Factorization(n_features = 10,
                        learn_rate = 0.1,
                        regularization_param = 0.1,
                        optimizer_pct_improvement_criterion=1,
                        user_bias_correction = True,
                        item_bias_correction = True)
    vals = val.validate(my_rec)
    print vals, np.mean(vals[0])

    """
    # Creating an object for my model
    nfeat = int(sys.argv[2])
    user_bias = bool(sys.argv[3])
    item_bias = bool(sys.argv[4])
    for lrate in [0.0005, 0.001, 0.003, 0.005, 0.007, 0.009]:
        for rparam in [0.005, 0.01, 0.03, 0.05, 0.07]:
            my_rec = Matrix_Factorization(n_features = nfeat,
                                learn_rate = lrate,
                                regularization_param = rparam,
                                optimizer_pct_improvement_criterion=3,
                                user_bias_correction = user_bias,
                                item_bias_correction = item_bias)
            val_results = val.validate(my_rec)
            print 'validation results: '
            print nfeat, lrate, rparam, val_results, np.mean(val_results)
    """
    for rlimit in [1,2,3,4,5]:
        for flimit in [0.2, 0.3, 0.4, 0.5]:
            for weight in [0.5, 0.6, 0.7, 0.8]:
                uf = Using_Friends(val.get_network(),
                    n_ratings_limit=rlimit, n_friend_limit_ratio=flimit,
                    weight_for_depth2=weight)
                (val_results, ratios) = val.validate(uf)
                print 'validation results: '
                print 'r', rlimit, flimit, weight, ratios, np.mean(ratios)
                print 'e', rlimit, flimit, weight, val_results,\
                    np.mean(val_results)
    #my_meta_predictor = MetaPredictor(my_mf_rec_engine, my_pop_rec_engine,\
    #    criteria=5)
    #my_meta_predictor.fit(ratings_mat)
    """



if __name__ == "__main__":
    if len(sys.argv) != 5:
        print "Usage: python run_recommender.py 0 8 0 1"
        print "     0 is a city number (0: Phoenix, 1: Las Vegas, 3: Montreal)"
        print "     8 is n_feature, the number of latent features"
        print "     1 if bias (user) is considered, 0 otherwise"
        print "     1 if bias (item) is considered, 0 otherwise"
        sys.exit()
    main()
