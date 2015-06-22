# Classes for matrix factorization for recommender system.

# by Suhan Ree
# last edited on 06-18-2015

import numpy as np
import itertools


class MatrixFactorization():
    """
    Class for matrix factorization for recommender.
    It uses SGD (Stochastic Gradient Descent) to mininize
    SSE when factoriziing.
    """
    def __init__(self, n_features=8, learn_rate=0.005,
                 regularization_param=0.02,
                 optimizer_pct_improvement_criterion=3,
                 user_bias_correction=False,
                 item_bias_correction=False,
                 saving_matrices=False,
                 saved_matrices=False):
        """
        Constructor of the class
        Input:
            n_features: number of latent features to use (model parameter)
            learn_rate: learning rate for Stochastic Gradient Descent
                        (model parameter)
            regularization_param: for regularization (model parameter)
            optimizer_pct_improvement_criterion: for SGD (model parameter)

            user_bias_correction: (default: False)
            item_bias_correction: (default: False)
            saving_matrices: True if saving u, v (default: False)
            saved_matrices: True if u. v are already saved (default: False)
        """
        self.n_features = n_features
        self.learn_rate = learn_rate
        self.optimizer_pct_improvement_criterion = \
            optimizer_pct_improvement_criterion
        self.regularization_param = regularization_param
        self.user_bias_correction = user_bias_correction
        self.item_bias_correction = item_bias_correction
        self.saving_matrices = saving_matrices
        self.saved_matrices = saved_matrices

        self.ratings_mat = None
        self.ratings_mat_coo = None
        self.user_mat = None  # u in SVD
        self.item_mat = None  # v in SVD (diagonal matrix does not exist)
        self.prediction = None  # prediction matrix found after SVD
        self.average_ratings_user = None
        self.average_ratings_item = None


    def fit(self, ratings_mat):
        filename_u = '../data/u.mat'
        filename_v = '../data/v.mat'
        if self.saved_matrices:
            self.user_mat.load(filename_u)
            self.item_mat.load(filename_v)
            return

        self.ratings_mat = ratings_mat.copy()  # in dok (dictionary) format.
        self.ratings_mat_coo = ratings_mat.tocoo()  # Converting dok to coo format.
                          # coo is better for looping over nonzero values.
        self.n_users, self.n_items = ratings_mat.shape
        self.n_rated = self.ratings_mat_coo.row.size
        print "    problem size:", self.n_users, self.n_items, self.n_rated

        # Subtract the overall average rating from ratings_mat.
        average_rating = self.ratings_mat_coo.data.mean()
        for irow, icol in itertools.izip(self.ratings_mat_coo.row,
                                         self.ratings_mat_coo.col):
            self.ratings_mat[irow, icol] -= average_rating

        # user bias subtraction done here
        if self.user_bias_correction:
            self.average_ratings_user = np.zeros(self.n_users)
            for irow in xrange(self.n_users):
                nonzero_indices = np.where(self.ratings_mat_coo.row == irow)[0]
                if nonzero_indices.size:  # With at least one review
                    self.average_ratings_user[irow] =\
                        self.ratings_mat_coo.data[nonzero_indices].mean()\
                        - average_rating
                else: self.average_ratings_user[irow] = 0
            for irow, icol in itertools.izip(self.ratings_mat_coo.row,
                                             self.ratings_mat_coo.col):
                self.ratings_mat[irow, icol] -= self.average_ratings_user[irow]
            print "    User biases subtracted"

        # item bias subtraction done here
        if self.item_bias_correction:
            self.average_ratings_item = np.zeros(self.n_items)
            for icol in xrange(self.n_items):
                nonzero_indices = np.where(self.ratings_mat_coo.col == icol)[0]
                if nonzero_indices.size:  # With at least one review
                    self.average_ratings_item[icol] =\
                        self.ratings_mat_coo.data[nonzero_indices].mean()\
                        - average_rating
                else: self.average_ratings_item[icol] = 0
            for irow, icol in itertools.izip(self.ratings_mat_coo.row,
                                             self.ratings_mat_coo.col):
                self.ratings_mat[irow, icol] -= self.average_ratings_item[icol]
            print "    Item biases subtracted"

        # Initializing u and v  (they are not sparse)
        self.user_mat = 2 * np.array(
            np.random.rand(self.n_users * self.n_features)\
            .reshape([self.n_users, self.n_features])) - 1
        self.item_mat = 2 * np.array(
            np.random.rand(self.n_items * self.n_features)\
            .reshape([self.n_features, self.n_items])) - 1

        # Iteration starts here.
        optimizer_iteration_count = 0
        pct_improvement = 0
        sse_accum = 0
        #print("    Optimizaiton Statistics")
        #print("    Iterations | Mean Squared Error  |  Percent Improvement")
        while ((optimizer_iteration_count < 2) or
               (pct_improvement > self.optimizer_pct_improvement_criterion)):
            old_sse = sse_accum
            sse_accum = 0
            for irow, icol in itertools.izip(self.ratings_mat_coo.row,
                                             self.ratings_mat_coo.col):
                error = self.ratings_mat[irow, icol] -\
                    np.dot(self.user_mat[irow, :], self.item_mat[:, icol])
                sse_accum += error**2
                for k in range(self.n_features):
                    self.user_mat[irow, k] += self.learn_rate * \
                        (2 * error * self.item_mat[k, icol] -\
                        self.regularization_param * self.user_mat[irow, k])
                    self.item_mat[k, icol] += self.learn_rate * (2 * error *\
                        self.user_mat[irow, k] - self.regularization_param\
                        * self.item_mat[k, icol])
            pct_improvement = 100 * (old_sse - sse_accum) / old_sse
            #print("    %d \t\t %f \t\t %f" % (
            #    optimizer_iteration_count, sse_accum /\
            #    self.n_rated, pct_improvement))
            old_sse = sse_accum
            optimizer_iteration_count += 1
        print "    Iteration done in", optimizer_iteration_count, "times."

        # prediction matrix (not sparse)
        self.prediction = np.dot(self.user_mat, self.item_mat)

        # average rating added.
        self.prediction += average_rating

        # Adding back baises subtracted before finding u and v
        if self.user_bias_correction:
            self.prediction = self.prediction +\
                self.average_ratings_user.reshape(-1, 1)
        if self.item_bias_correction:
            self.prediction = self.prediction +\
                self.average_ratings_item.reshape(1, -1)

        # If saveing is needed
        if self.saving_matrices:
            self.user_mat.dump(filename_u)
            self.item_mat.dump(filename_v)

    def pred_one_rating(self, user_id, item_id):
        """
        Predict for one user-item pair
        Output:
            prediected: float
        """
        return self.prediction[user_id, item_id]


    def pred_one_user(self, user_id):
        """
        Predict for one user.
        Output:
            prediected: np.array (1d)
        """
        return self.prediction[user_id]


    def pred_all(self):
        """
        Predict for all user-item pairs.
        Output:
            prediected: np.array (2d)
        """
        return self.prediction


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
        items_rated_by_this_user = set(self.ratings_mat_coo[
            np.where(self.ratings_mat_coo.row == user_id)])
        items_not_rated_by_this_user =\
            np.array([i for i in xrange(self.n_items)
                      if i not in items_rated_by_this_user])
        return np.argsort(pred_output[items_not_rated_by_this_user])\
            [-num:][::-1]


"""
class MetaPredictor(object):
    def __init__(self, recom_svd, recom_pop, criteria=5):
        self.recom_svd = recom_svd
        self.recom_pop = recom_pop
        self.criteria = criteria
        self.ratings_mat = None

        self.n_users = None
        self.n_items = None

    def fit(self, ratings_mat):
        self.ratings_mat = ratings_mat
        self.n_users, self.n_items = ratings_mat.shape

        self.recom_svd.fit(ratings_mat)
        self.recom_pop.fit(ratings_mat, '../data/user_group.csv')

    def pred_one_user(self, user_id, report_run_time=False):
        n_rated_by_user = len(self.ratings_mat[user_id].nonzero()[1])
        if n_rated_by_user < self.criteria:
            return self.recom_pop.pred_one_user(user_id,
                                                report_run_time=report_run_time)
        else:
            return self.recom_svd.pred_one_user(user_id,
                                                report_run_time=report_run_time)

    def pred_all_users(self, report_run_time=False):
        out = np.zeros((self.n_users, self.n_items))
        for id in xrange(self.n_users):
            out[id] = self.pred_one_user(id).reshape(1, -1)
        return out

    def top_n_recs(self, user_id, n):
        n_rated_by_user = len(ratings_mat[user_id].nonzero()[1])
        if n_rated_by_user < self.criteria:
            return self.recom_pop.top_n_recs(user_id, n)
        else:
            return self.recom_svd.top_n_recs(user_id, n)
        return self.average_ratings[self.sorted_indices][:n]
"""
