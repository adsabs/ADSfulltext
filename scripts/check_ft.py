"""
Check for the existance of the fulltext body and meta.json files

AA 11/1/16
"""
from __future__ import print_function

import json
import ptree
import fileinput
import os
from settings import config

if __name__ == '__main__':

    for line in fileinput.input():
        bibcode, fname, provider = line.strip().split()
        f = config['FULLTEXT_EXTRACT_PATH'] + ptree.id2ptree(bibcode)
        if not os.path.exists(f):
            print("{0}: missing_dir   {1}".format(bibcode, f))
        meta = f + 'meta.json'
        full = f + 'fulltext.txt'
        if not os.path.exists(meta):
            print("{0} : missing_meta {1}".format(bibcode, meta))
            continue
        if not os.path.exists(full):
            print("{0} : missing_ft   {1}".format(bibcode, full))
        try:
            d = json.load(open(meta))
            ts = d['index_date']
        except KeyError:
            print("{0}: missing_date  {1}".format(bibcode, meta))

