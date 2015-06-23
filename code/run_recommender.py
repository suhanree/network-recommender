# To run the recommender system.

# by Suhan Ree
# last edited on 06-22-2015

import sys
import pandas as pd
import numpy as np
from scipy import sparse
import itertools
from factorization import Matrix_Factorization # , MetaPredictor
from using_friends import Using_Friends
from my_utilities import read_dictlist_from_file



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
        not_counted = set([])
        for u_id in temp_network:
            if u_id in self.users_id_map:
                self.my_network[self.users_id_map[u_id]] = []
                for u_id2 in temp_network[u_id]:
                    if u_id2 in self.users_id_map:
                        self.my_network[self.users_id_map[u_id]].\
                            append(self.users_id_map[u_id2])
                    else:
                        not_counted.add(u_id2)
            else:
                not_counted.add(u_id)

        if len(not_counted) > 0:
            print "    There are some users not counted for the netwrok:", \
                len(not_counted)
        return


    def validate(self, recommender):
        """
        Perform the K-fold validation using k folds (k times)
        Here we already have split ratings for k folds.
        Input:
            recommender: model
            ratings: ratings matrix for
        Output:
            rmse: list of RMSE for each fold.
        """
        # Perform k-fold validation k times.
        list_rmse = []
        list_ratio = []  # Ratio of predictions.
        for i in range(self.k):
            print "Validation set", i, "started."
            recommender.fit(self.list_ratings_rest[i])
            #print 'v', self.list_ratings_val[i]
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
            if predicted > 0.0001:
                squared_sum += \
                    (val - recommender.pred_one_rating(irow, icol))**2
                n_predicted += 1
            else:
                n_not_predicted += 1
            #print irow, icol, val, recommender.pred_one_rating(irow, icol)
        if n_predicted == 0:
            return (None, None)
        else:
            return np.sqrt(squared_sum/n_predicted), n_predicted/float(n_total)


    def get_network(self):
        """
        Return the network in a dict of lists
        """
        return self.my_network


    def run_fit(self, model):
        """
        Run fit method for the given model (mostly for testing purpose)
        """
        model.fit(self.ratings_train)


def main():
    """
    To run the recommender model.
    """
    # Read the the ratings data from a file, and store them in matrices.
    ratings_filename = "../data/reviews" + sys.argv[1]
    network_filename = "../data/network" + sys.argv[1] + ".csv"
    #ratings_filename = "sample_ratings"
    #network_filename = "sample_network"
    # k: number of folds for cross validation.
    k = 10
    val = Validator(ratings_filename, network_filename, k, 0.)

    """
    # Creating an object for my model
    nfeat = int(sys.argv[2])
    if_bias = bool(sys.argv[3])
    for lrate in [0.025, 0.005, 0.0075, 0.01]:
        for rparam in [0.5, 1.0, 1.5, 2.0]:
            my_rec = Matrix_Factorization(n_features = nfeat,
                                learn_rate = lrate,
                                regularization_param = rparam,
                                optimizer_pct_improvement_criterion=1,
                                user_bias_correction = if_bias,
                                item_bias_correction = if_bias)
            val_results = val.validate(my_rec)
            print 'validation results: '
            print nfeat, lrate, rparam, val_results, np.mean(val_results)
    """
    uf = Using_Friends(val.get_network(),
                 n_ratings_limit=3, n_friend_limit_ratio=0.3,
                 weight_for_depth2=0.5)
    (val_results, ratios) = val.validate(uf)
    print 'validation results: '
    print ratios, np.mean(ratios)
    print val_results, np.mean(val_results)
    #my_meta_predictor = MetaPredictor(my_mf_rec_engine, my_pop_rec_engine,\
    #    criteria=5)
    #my_meta_predictor.fit(ratings_mat)



if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "Usage: python run_recommender.py 0 8 1"
        print "     0 is a city number (0: Phoenix, 1: Las Vegas, 3: Montreal)"
        print "     8 is n_feature, the number of latent features"
        print "     1 if bias (user and item) is considered, 0 otherwise"
        sys.exit()
    main()
