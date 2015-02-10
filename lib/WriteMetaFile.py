"""
WriteMetaFile Worker Functions

These are the functions for the WriteMetaFile class. This worker should write the meta content to the
pair tree directory path.
"""

import os
import json
from settings import CONSTANTS, META_CONTENT
from utils import setup_logging

logger = setup_logging(__file__, __name__)


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
            logger.info("Adding meta content: %s" % const)
        except KeyError :
            print("Missing meta content: %s" % const)
            continue



    # Write the custom extractions of content to the meta.json
    logger.info("Copying extra meta content")
    for meta_key_word in META_CONTENT[payload_dictionary[CONSTANTS['FORMAT']]]:
        if meta_key_word == CONSTANTS['FULL_TEXT']:
            continue

        logger.info(meta_key_word)
        try:
            meta_key_word_value = payload_dictionary[meta_key_word]
            meta_dict[meta_key_word] = meta_key_word_value
        except KeyError:
            logger.info("Does not contain the following meta data: %s" % meta_key_word)
            continue

    # Write the full text content to its own file fulltext.txt
    logger.info("Copying full text content")
    full_text_dict = {CONSTANTS['FULL_TEXT']: payload_dictionary[CONSTANTS['FULL_TEXT']]}

    with open(meta_output_file_path, 'w') as meta_output_file:
        try:
            logger.info("Writing to file: %s" % meta_output_file_path)
            logger.info("Content has keys: %s" % (meta_dict.keys()))
            json.dump(meta_dict, meta_output_file)
            logger.info("Writing complete.")
        except IOError:
            raise IOError

    with open(full_text_output_file_path, 'w') as full_text_output_file:
        try:
            logger.info("Writing to file: %s" % full_text_output_file_path)
            logger.info("Content has length: %d" % (len(full_text_dict[CONSTANTS['FULL_TEXT']])))
            full_text_output_file.write(full_text_dict[CONSTANTS['FULL_TEXT']])
            logger.info("Writing complete.")
        except IOError:
            raise IOError


def extract_content(input_list):

    for dict_item in input_list:
        try:
            write_content(dict_item)
        except Exception:
            import traceback
            raise Exception(traceback.format_exc())

    return 1