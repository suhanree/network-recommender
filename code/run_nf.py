# To run the NF recommender.

# Filename: run_nf.py
# by Suhan Ree
# last edited on 06-27-2015

import sys
import numpy as np

from validator import Validator
from using_friends import Using_Friends


def main():
    """
    To run the UF model.
    """
    #ratings_filename = "sample_ratings"
    #network_filename = "sample_network"

    # k: number of folds for cross validation.
    k = 10

    input_filename = sys.argv[1]
    if_average = bool(int(sys.argv[2]))
    nums = []
    with open(input_filename, 'r') as f:
        for line in f:
            nums.append(line.strip().split(" "))

    for city in nums[0]:
        ratings_filename = "../data/reviews" + city
        network_filename = "../data/network" + city + "b.csv"
        # Creating an object for my model
        val = Validator(ratings_filename, network_filename, k, 0.)
        for llimit in map(int, nums[1]):
            for ulimit in map(int, nums[2]):
                uf = Using_Friends(val.get_network(),
                    n_ratings_lower_limit=llimit, n_ratings_upper_limit=ulimit,
                    if_average=if_average)
                (val_results, ratios) = val.validate(uf, run_all=True)
                print 'validation results: '
                print city, llimit, ulimit, ratios, val_results, \
                    np.mean(val_results)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Usage: python run_recommender2.py input 0"
        print "     input: filename for parameters"
        print "         first line: list of cities (separated by space)"
        print "         second line: list of lower limits (separated by space)"
        print "         third line: list of upper limits (separated by space)"
        print "     0: If this value is 0, there will be no prediction, when",\
        print "there are not enough ratings from friends.",\
        print "If 1, the item average will be used for prediction."
        sys.exit()
    main()
