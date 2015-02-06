"""
WriteMetaFile Worker Functions

These are the functions for the WriteMetaFile class. This worker should write the meta content to the
pair tree directory path.
"""

import os
import json
from settings import CONSTANTS, META_CONTENT


def write_content(payload_dictionary):

    meta_output_file_path = payload_dictionary[CONSTANTS['META_PATH']]
    full_text_output_file_path = payload_dictionary[CONSTANTS['META_PATH']].replace(
            'meta.json', '%s.txt' % CONSTANTS['FULL_TEXT'])
    bibcode_pair_tree_path = meta_output_file_path.replace('meta.json', '')

    if not os.path.exists(bibcode_pair_tree_path):
        try:
            os.makedirs(bibcode_pair_tree_path)
        except OSError:
            raise OSError

    meta_dict = {}
    for meta_key_word in META_CONTENT[payload_dictionary[CONSTANTS['FORMAT']]]:
        if meta_key_word == CONSTANTS['FULL_TEXT']: continue

        try:
            meta_key_word_value = payload_dictionary[meta_key_word]
            meta_dict[meta_key_word] = meta_key_word_value
        except KeyError:
            pass

    full_text_dict = {CONSTANTS['FULL_TEXT']: payload_dictionary[CONSTANTS['FULL_TEXT']]}

    with open(meta_output_file_path, 'w') as meta_output_file:
        try:
            json.dump(meta_dict, meta_output_file)
        except IOError:
            raise IOError

    with open(full_text_output_file_path, 'w') as full_text_output_file:
        try:
            json.dump(full_text_dict, full_text_output_file)
        except IOError:
            raise IOError



def extract_content():
    pass