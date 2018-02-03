import _pickle as pickle
from functools import reduce


def save_persistent_data(data, filename):
    data_file = open(filename, "wb")
    pickle.dump(data, data_file, protocol=4)
    data_file.close()
    print("Saved persistent data file.")


def import_persistent_data(filename):
    try:
        data_file = open(filename, "rb")
        persistent_data = pickle.load(data_file)
        print("Loaded persistent data file.")
        return persistent_data
    except FileNotFoundError:
        print("No data file found, cannot import data.")
        return {}


def read_persistent_data(d, path):
    if type(path) is str:
        path = path.split('/')
    return reduce(lambda d, k: d.setdefault(k, {}), path, d)


def write_persistent_data(d, path, value):
    if type(path) is str:
        path = path.split('/')
    read_persistent_data(d, path[:-1])[path[-1]] = value