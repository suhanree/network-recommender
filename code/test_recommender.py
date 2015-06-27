# To run the recommender system using UsingFriends class.

# by Suhan Ree
# last edited on 06-26-2015

import sys
import pandas as pd
import numpy as np
from scipy import sparse
import itertools

from factorization import Matrix_Factorization  # , MetaPredictor
from using_friends import Using_Friends
from my_utilities import read_dictlist_from_file, reindex_graph
from run_recommender import *


def main():
    """
    To run the recommender model.
    """
    #ratings_filename = "sample_ratings"
    #network_filename = "sample_network"

    # Create the Validator object.
    # k: number of folds for cross validation.
    k = 10


    # Creating an object for my model
    input_filename = sys.argv[1]
    if_average = bool(sys.argv[2])
    nums = []
    with open(input_filename, 'r') as f:
        for line in f:
            nums.append(line.strip().split(" "))

    for city in nums[0]:
        ratings_filename = "../data/reviews" + city
        network_filename = "../data/network" + city + "b.csv"
        val = Validator(ratings_filename, network_filename, k, 0.)
        for llimit in map(int, nums[1]):
            for ulimit in map(int, nums[2]):
                uf = Using_Friends(val.get_network(),
                    n_ratings_lower_limit=llimit, n_ratings_upper_limit=ulimit,
                    if_average=if_average)
                (val_results, ratios) = val.validate(uf, run_all=True)
                print 'validation results: '
                print 'r', city, llimit, ulimit, ratios, np.mean(ratios)
                print 'e', city, llimit, ulimit, val_results, np.mean(val_results)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Usage: python run_recommender2.py input 0"
        print "     input: filename for parameters"
        print "     0 if no prediction, and 1 if average will be used, when", \
            "there are not enough friends."
        sys.exit()
    main()
