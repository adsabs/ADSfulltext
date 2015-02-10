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

    # Write everything but the full text content to the meta.json
    meta_dict = {}

    for const in CONSTANTS:
        if const == "FULL_TEXT": continue
        try:
            meta_dict[CONSTANTS[const]] = payload_dictionary[CONSTANTS[const]]
            print("Adding meta content: %s" % const)
        except KeyError :
            print("Missing meta content: %s" % const)
            pass

    # Write the custom extractions of content to the meta.json
    for meta_key_word in META_CONTENT[payload_dictionary[CONSTANTS['FORMAT']]]:
        if meta_key_word == CONSTANTS['FULL_TEXT']: continue

        try:
            meta_key_word_value = payload_dictionary[meta_key_word]
            meta_dict[meta_key_word] = meta_key_word_value
        except KeyError:
            pass

    # Write the full text content to its own file fulltext.txt
    full_text_dict = {CONSTANTS['FULL_TEXT']: payload_dictionary[CONSTANTS['FULL_TEXT']]}

    with open(meta_output_file_path, 'w') as meta_output_file:
        try:
            print("Writing to file: %s" % meta_output_file_path)
            print("Content has keys: %s" % (meta_dict.keys()))
            json.dump(meta_dict, meta_output_file)
            print("Writing complete.")
        except IOError:
            raise IOError

    with open(full_text_output_file_path, 'w') as full_text_output_file:
        try:
            print("Writing to file: %s" % full_text_output_file_path)
            print("Content has length: %d" % (len(full_text_dict[CONSTANTS['FULL_TEXT']])))
            full_text_output_file.write(full_text_dict[CONSTANTS['FULL_TEXT']])
            print("Writing complete.")
        except IOError:
            raise IOError


def extract_content(input_list):

    for dict_item in input_list:
        try:
            write_content(dict_item)
        except Exception:
            import traceback
            raise Exception(traceback.print_exc())

    return 1