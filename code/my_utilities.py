# Utilities for the project.

# Filename: my_utilities.py
# by Suhan Ree

# import numpy as np
# import pandas as pd
import json


def read_json_file(filename):
    """
    To read the json file and return a json object.
    Input:
        filename: name of the file
    Output:
        user_json: json object for users.
    """
    data_json = []
    with open(filename) as f:
        for line in f:
            data_json.append(json.loads(line))
    return data_json
