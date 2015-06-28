# To run the CF recommender system.

# Filename: run_cf.py
# by Suhan Ree
# last edited on 06-26-2015

import sys
import pandas as pd
import numpy as np
from scipy import sparse
import itertools

from validator import Validator
from factorization import Matrix_Factorization  # , MetaPredictor
from my_utilities import read_dictlist_from_file, reindex_graph


def main():
    """
    To run the CF model.
    """
    #ratings_filename = "sample_ratings"
    #network_filename = "sample_network"

    input_filename = sys.argv[1]
    user_bias = bool(int(sys.argv[2]))
    item_bias = bool(int(sys.argv[3]))
    nums = []
    with open(input_filename, 'r') as f:
        for line in f:
            nums.append(line.strip().split(" "))

    for city in nums[0]:
        # Filenames needed.
        ratings_filename = "../data/reviews" + city
        network_filename = "../data/network" + city + "b.csv"
        # Create the Validator object.
        # k: number of folds for cross validation.
        k = 10
        # Creating an object for my model
        val = Validator(ratings_filename, network_filename, k, 0.)
        for nfeat in map(int, nums[1]):
            for lrate in map(float, nums[2]):
                for rparam in map(float, nums[3]):
                    my_rec = Matrix_Factorization(n_features = nfeat,
                                        learn_rate = lrate,
                                        regularization_param = rparam,
                                        optimizer_pct_improvement_criterion=2,
                                        user_bias_correction = user_bias,
                                        item_bias_correction = item_bias)
                    (val_results, ratios) = val.validate(my_rec, run_all=True)
                    print 'validation results: '
                    print city, nfeat, lrate, rparam, ratios, val_results, \
                        np.mean(val_results)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "Usage: python run_recommender.py input 0 1"
        print "     input: input filename"
        print "         first line: list of cities (separated by space)"
        print "         second line: list of n_feature's"
        print "         third line: list of learning rates"
        print "         fourth line: list of regularization parameter"
        print "     0: user_bias (1 if True)"
        print "     1: item_bias (1 if True)"
        sys.exit()
    main()
