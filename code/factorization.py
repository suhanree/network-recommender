# Classes for matrix factorization for recommender system.

# by Suhan Ree
# last edited on 06-18-2015

import numpy as np
from time import time


class MatrixFactorization():
    """
    Class for matrix factorization for recommender.
    It uses SGD (Stochastic Gradient Descent) to mininize
    RMSE when factoriziing.
    """
    def __init__(self, n_features=8, learn_rate=0.005,
                 regularization_param=0.02,
                 optimizer_pct_improvement_criterion=2,
                 user_bias_correction=False,
                 item_bias_correction=False,
                 saving_matrices=False,
                 saved_matrices=False):
        """
        Constructor of the class
        Input:
            n_features
            learn_rate
            regularization_param=0.02,
            optimizer_pct_improvement_criterion=2,
            user_bias_correction=False,
            item_bias_correction=False,
            saving_matrices=False,
            saved_matrices=False
        """
        self.n_features = n_features
        self.learn_rate = learn_rate
        self.regularization_param = regularization_param
        self.optimizer_pct_improvement_criterion = \
            optimizer_pct_improvement_criterion
        self.user_bias_correction = user_bias_correction
        self.item_bias_correction = item_bias_correction
        self.saving_matrices = saving_matrices
        self.saved_matrices = saved_matrices
        self.user_mat = None
        self.item_mat = None

        self.prediction = None
        self.average_ratings = None


    def fit(self, ratings_mat):
        filename_u = '../data/u.mat'
        filename_v = '../data/v.mat'
        if self.saved_matrices:
            self.user_mat.load(filename_u)
            self.item_mat.load(filename_v)
            return

        self.ratings_mat = ratings_mat.copy()
        boolean_mat = self.ratings_mat > 0
        self.average_rating = ratings_mat.mean()
        self.n_users, self.n_items = ratings_mat.shape
        self.n_rated = self.ratings_mat.nonzero()[0].size
        #print self.ratings_mat
        if self.item_bias_correction:
            self.average_ratings = np.zeros(self.n_items)

            n_ratings_per_item = np.array(boolean_mat.sum(axis=0)).reshape(-1)

            for icol in xrange(self.n_items):
                if n_ratings_per_item[icol]:
                    self.average_ratings[icol] =\
                        self.ratings_mat[:, icol][boolean_mat[:, icol]].mean()
                else: self.average_ratings[icol] = 0
            for irow in xrange(self.n_users):
                for icol in xrange(self.n_items):
                    if boolean_mat[irow, icol]:
                        self.ratings_mat[irow, icol] =\
                            self.ratings_mat[irow, icol] -\
                            self.average_ratings[icol]
        #print self.ratings_mat

        self.user_mat = np.matrix(
            np.random.rand(self.n_users*self.n_features)\
            .reshape([self.n_users, self.n_features]))
        self.item_mat = np.matrix(
            np.random.rand(self.n_items*self.n_features)\
            .reshape([self.n_features, self.n_items]))
        optimizer_iteration_count = 0
        pct_improvement = 0
        sse_accum = 0
        #print("Optimizaiton Statistics")
        #print("Iterations | Mean Squared Error  |  Percent Improvement")
        while ((optimizer_iteration_count < 2) or
               (pct_improvement > self.optimizer_pct_improvement_criterion)):
            old_sse = sse_accum
            sse_accum = 0
            for i in range(self.n_users):
                for j in range(self.n_items):
                    if boolean_mat[i, j]:
                        error = self.ratings_mat[i, j] -\
                            np.dot(self.user_mat[i, :], self.item_mat[:, j])
                        sse_accum += error**2
                        for k in range(self.n_features):
                            self.user_mat[i, k] = self.user_mat[i, k] +\
                                self.learn_rate * \
                                (2 * error * self.item_mat[k, j] -\
                                self.regularization_param * self.user_mat[i, k])
                            self.item_mat[k, j] = self.item_mat[k, j] +\
                                self.learn_rate * (2 * error *\
                                self.user_mat[i, k] - self.regularization_param\
                                * self.item_mat[k, j])
            pct_improvement = 100 * (old_sse - sse_accum) / old_sse
            print("%d \t\t %f \t\t %f" % (
                optimizer_iteration_count, sse_accum /\
                self.n_rated, pct_improvement))
            old_sse = sse_accum
            optimizer_iteration_count += 1
        self.prediction = np.dot(self.user_mat, self.item_mat)
        #print self.prediction
        if self.item_bias_correction:
            #for irow in xrange(self.n_users):
            #   self.prediction[irow] = self.prediction[irow] +\
            #   self.average_ratings
            self.prediction = self.prediction +\
                self.average_ratings.reshape(1, -1)
        #print self.average_ratings
        if self.saving_matrices:
            self.user_mat.dump(filename_u)
            self.item_mat.dump(filename_v)
        #print("Fitting of latent feature matrices completed")

    def pred_one_rating(self, user_id, item_id):
        return np.vdot(self.user_mat[user_id], self.item_mat[:,item_id])

    def pred_one_user(self, user_id, report_run_time=False):
        start_time = time()
        if self.prediction is None:
            self.prediction = np.dot(self.user_mat, self.item_mat)
        if report_run_time:
            print("Execution time: %f seconds" % (time()-start_time))
        return self.prediction[user_id]

    def pred_all_users(self, report_run_time=False):
        start_time = time()
        if self.prediction is None:
            self.prediction = np.dot(self.user_mat, self.item_mat)
        if report_run_time:
            print("Execution time: %f seconds" % (time()-start_time))
        return self.prediction


    def top_n_recs(self, user_id, n):
        pred_ratings = self.pred_one_user(user_id)
        item_index_sorted_by_pred_rating = list(np.argsort(pred_ratings))
        items_rated_by_this_user = self.ratings_mat[user_id].nonzero()[1]
        unrated_items_by_pred_rating = [item for item in
                                        item_index_sorted_by_pred_rating
                                        if item not in items_rated_by_this_user]
        return unrated_items_by_pred_rating[-n:]


    def top_n_recs2(self, user_id, num):
        pred_output = self.pred_one_user(user_id).reshape(1, self.n_items)
        items_not_rated_by_this_user = \
        ~(self.ratings_mat[user_id] > 0).todense().reshape(1, self.n_items)
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
