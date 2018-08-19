import os
from collections import OrderedDict
import time
from datetime import datetime
import hashlib
import math
import pandas as pd
import re


def convert_size(size_bytes):
    """
    Obtain human readable file sizes
    :param size_bytes: Size in bytes
    :return:
    """
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "{} {}".format(s, size_name[i])


def get_file_info(fname, compute_hash=False):
    """
    Get file meta information. Has an optional argument to compute a files md5 hash.
    :param fname:
    :param compute_hash: Defults to False. If true it will compute a files md5 hash. This can be expensive
    :return:
    """
    stat = os.stat(fname)
    return {
        'size': stat.st_size,
        'h_size': convert_size(stat.st_size),
        'creation': stat.st_ctime,
        'h_creation': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_ctime)),
        'modification': stat.st_mtime,
        'h_modification': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime)),
        'md5': md5(fname) if compute_hash else ''
    }


def md5(fname):
    """
    Compute an md5 hash - this is an expensive operation
    """
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_file_list(target, info_grabber=None, info_grabber_kwargs={}):
    """
    Get a list of files where `target` is the root directory.

    :param target: rood directory to walk into
    :param info_grabber: function used to obtain file information
    :param info_grabber_kwargs: optional arguments to provide to info_grabber function
    :return: Ordered Dict
    """
    files = OrderedDict()
    for r, d, fs in os.walk(target):
        for f in fs:
            if info_grabber is None:
                info = {}
            else:
                info = info_grabber(os.path.join(r, f), **info_grabber_kwargs)
            files[(os.path.join(r, f))] = info
    return files


def to_df(file_information, reset_index=True):
    """
    Takes the output of get_file_list and transposes that into a dataframe

    :param file_information:
    :param reset_index:
    :return:
    """
    df = pd.DataFrame(file_information).transpose()
    if reset_index:
        df.loc[:, 'file_name'] = df.index
        df.reset_index(drop=True, inplace=True)
    return df


def to_csv(df, _dir='file_reports', fname='', include_datetime=True):
    """
    Create a CSV file. This function handles naming conventions and file location. Otherwise just a wrapper for
    pd.DataFrame.to_csv

    :param df:
    :param _dir:
    :param fname:
    :param include_datetime:
    :return:
    """
    if not os.path.exists(_dir):
        os.makedirs(_dir)
    out_file = '{}_{}.csv'.format(datetime.now(), fname) if include_datetime else '{}.csv'.format(fname)
    # df.to_csv('{}/{}'.format(_dir,out_file))  #god damit windows... why can't you just be more like linux
    df.to_csv(re.sub(':', '', os.path.join(_dir, out_file)))

def create_baseline(target, save_baseline=to_csv, **kwargs):
    """
    Create a baseline and save it somewhere. The mechanism to save this information is determined by `save_baseline`.
    Right now this will go to a file.

    #TODO: Allow this to go to a database (probably sqlite but might use an ORM wrapper

    :param target:
    :param save_baseline:
    :return:
    """