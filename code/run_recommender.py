# To run the recommender.

# by Suhan Ree
# last edited on 06-18-2015

import pandas as pd
import numpy as np
from scipy import sparse
import itertools
from factorization import MatrixFactorization # , MetaPredictor

def get_ratings_data(filename, k=5):
    """
    Read the ratings information from the file.
    Input:
        filename: filename of the file
        k: number of folds for k-fold cross-validation
    Output:
        ratings_mat: ratings info on a matrix
        list_ratings_val: list of ratings for validation (determined by k)
        list_ratings_training: list of ratings for training (determined by k)
    """
    # Read the file.
    ratings_contents = pd.read_csv(filename, names=['user_id', 'item_id',
                                                 'rating'], header=None)
    # Creating a matrix
    u_size = ratings_contents.user_id.nunique()
    i_size = ratings_contents.item_id.nunique()
    ratings_as_mat = sparse.coo_matrix((u_size, i_size))

    # Dict to store ID mapping info.
    users_id_map = {}
    items_id_map = {}

    # Converting user_id and item_id to make them continuous starting from 0
    u_id = 0  # New id for users starting from 0 to size-1
    i_id = 0  # New id for items starting from 0 to size-1

    # As we read the data, we will perform the division for k folds.
    # And ratings matrices for all folds and outside of folds will be
    # stored in lists of matrices.
    list_ratings_val = []
    list_ratings_training = []
    n_reviews = ratings_contents.shape[0]
    fold_number = []  # Fold number for each review.
    for _ in xrange(n_reviews):
        fold_number.append(np.random.randint(k))
    list_ratings_val = []
    list_ratings_training = []
    for i in range(k):
        list_ratings_val.append(sparse.coo_matrix((u_size, i_size)))
        list_ratings_training.append(sparse.coo_matrix((u_size, i_size)))

    count = 0
    for _, row in ratings_contents.iterrows():
        u_temp = int(row.user_id)
        i_temp = int(row.item_id)
        if u_temp not in users_id_map:
            users_id_map[u_temp] = u_id
            u_id += 1
        if i_temp not in items_id_map:
            items_id_map[i_temp] = i_id
            i_id += 1
        uu = users_id_map[u_temp]
        ii = items_id_map[i_temp]
        rating = float(row.rating)
        ratings_as_mat[uu, ii] = rating
        for j in range(k):
            if fold_number[count] == j:  # Inside fold.
                list_ratings_val[j][uu, ii] = rating
            else:  # Outside fold.
                list_ratings_training[j][uu, ii] = rating
        count += 1
    return ratings_as_mat, list_ratings_val, list_ratings_training


def validation(recommender, list_ratings_val, list_ratings_training):
    """
    Perform the K-fold validation using k folds.
    Here we are getting already split ratings for k folds.
    Input:
        recommender: model
        list_ratings_val: list of ratings for validation (determined by k)
        list_ratings_training: list of ratings for training (determined by k)
    Output:
        rmse: list of RMSE for each fold.
    """
    # Getting the already split data.
    k = len(list_ratings_training)

    # Perform k-fold validation k times.
    list_rmse = []
    for i in range(k):
        recommender.fit(list_ratings_training[i])
        list_rmse.append(find_rmse(recommender, list_ratings_val[i]))
    return list_rmse


def find_rmse(model, ratings_val):
    """
    Using the fitted model, compute the RMSE of the validation set.
    Input:
        model: model (fitted)
        ratings_val: sparse matrix containing validation set.
    Output:
        rmse: float
    """
    squared_sum = 0
    # It's been known that COO is faster for this type of process.
    coo_mat = ratings_val.tocoo()
    # Loop over non-zero values.
    for i, j, val in itertools.izip(coo_mat.row, coo_mat.col, coo_mat.data):
        squared_sum += (coo_mat[i, j] - model.pred_one_rating(i, j))**2



def mse_sparse_with_dense(sparse_mat, dense_mat):
    """
    Computes mean-squared-error between a sparse and a dense matrix.
    Does not include the 0's from
    the sparse matrix in computation (treats them as missing)
    """
    #get mask of non-zero, mean-square of those, divide by count of those
    nonzero_idx = sparse_mat.nonzero()
    mse = (np.array(sparse_mat[nonzero_idx] - dense_mat[nonzero_idx])**2).mean()
    return mse


def mse_sparse_with_dense2(sparse_mat, dense_mat):
    """
    Computes mean-squared-error between a sparse and a dense matrix.
    Does not include the 0's from
    the sparse matrix in computation (treats them as missing)
    """
    #get mask of non-zero, mean-square of those, divide by count of those
    nonzero_idx = sparse_mat.nonzero()
    mse = (np.array(sparse_mat[nonzero_idx].todense()) * \
            np.array(sparse_mat[nonzero_idx] - dense_mat[nonzero_idx]) **2)\
        .mean()
    return mse


def main():
    # Read the the ratings data from a file, and store them in matrices.
    ratings_data_fname = "../data/training_ratings_for_kaggle_comp.csv"
    ratings_mat = get_ratings_data(ratings_data_fname)

    # Creating an object for my model
    my_mf_engine = MatrixFactorization(n_features = 3,\
                            item_bias_correction=True, saving_matrices=False)
    my_mf_engine.fit(ratings_mat)

    #my_meta_predictor = MetaPredictor(my_mf_rec_engine, my_pop_rec_engine,\
    #    criteria=5)
    #my_meta_predictor.fit(ratings_mat)

    val_results = validation(my_mf_engine, 0.3, 0.3, ratings_mat)
    print 'validation results: ', val_results


if __name__ == "__main__":
    main()
