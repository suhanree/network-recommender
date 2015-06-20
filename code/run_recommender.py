# To run the recommender.

# by Suhan Ree
# last edited on 06-18-2015

import sys
import pandas as pd
import numpy as np
from scipy import sparse
import itertools
from factorization import MatrixFactorization # , MetaPredictor


class Validator():
    """
    Class for reading the ratings file, and computing RMSE's for the given model
    """
    def __init__(self, ratings_filename, network_filename, k=5, test_ratio=None):
        """
        Constructor for class Validation,
        It will read the ratings information from the file.
        Input:
            ratings_filename: filename for ratings.
            network_filename: filename for network.
            k: number of folds for cross validation (default: 5)
            test_ratio: ratio of test set (float, 0~1, default: None)
        """
        self.ratings_filename = ratings_filename
        self.network_filename = network_filename
        self.k = int(k)
        self.test_ratio = test_ratio

        # Read the file.
        ratings_contents = pd.read_csv(ratings_filename,
                            names=['user_id', 'item_id', 'rating'], header=None)
        # Creating matrices.
        # ratings_mat: ratings info on a matrix
        # ratings_testing: ratings info for testing (test set).
        # list_ratings_val: list of ratings for validation (determined by k)
        # list_ratings_training: list of ratings for training (determined by k)
        u_size = ratings_contents.user_id.nunique()
        i_size = ratings_contents.item_id.nunique()
        print u_size, i_size
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
        for i in range(self.k):
            recommender.fit(self.list_ratings_rest[i])
            list_rmse.append(self.find_rmse(recommender,
                                            self.list_ratings_val[i]))
        return list_rmse


    def find_test_rmse(self, recommender):
        """
        Find the RMSE for the test test.
        Input:
            recommender: fitted model.
        Output
            None
        """
        recommender = recommender.fit(self.ratings_train)
        return self.find_rmse(recommender, self.ratings_test)


    def find_rmse(self, recommender, ratings):
        """
        Using the fitted model, compute the RMSE of the validation set.
        Input:
            recommender: model (fitted)
            ratings_val: sparse matrix containing validation set.
        Output:
            rmse: float
        """
        mat = ratings.tocoo()  # coo format is know to be faster when looping.
        squared_sum = 0
        count = len(mat.row)
        # Loop over non-zero values
        for irow, icol, val in itertools.izip(mat.row, mat.col, mat.data):
            squared_sum += (val - recommender.pred_one_rating(irow, icol))**2
            #print irow, icol, val, recommender.pred_one_rating(irow, icol)
        return np.sqrt(squared_sum/count)


def main():
    # Read the the ratings data from a file, and store them in matrices.
    ratings_filename = "../data/reviews" + sys.argv[1]
    #ratings_filename = "../data/sample_ratings"
    network_filename = "../data/network" + sys.argv[1]
    # k: number of folds for cross validation.
    k = 5
    val = Validator(ratings_filename, network_filename, k, 0.2)

    # Creating an object for my model
    my_rec = MatrixFactorization(n_features = 10,
                                 user_bias_correction=False,
                                 item_bias_correction=False)

    #my_meta_predictor = MetaPredictor(my_mf_rec_engine, my_pop_rec_engine,\
    #    criteria=5)
    #my_meta_predictor.fit(ratings_mat)

    val_results = val.validate(my_rec)
    print 'validation results: ', val_results


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Usage: python run_recommender.py 0"
        print "     0 is a city number (0: Phoenix, 1: Las Vegas, 3: Montreal)"
        sys.exit()
    main()
