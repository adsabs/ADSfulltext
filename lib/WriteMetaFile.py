"""
WriteMetaFile Worker Functions

These are the functions for the WriteMetaFile class. This worker should write the meta content to the
pair tree directory path.
"""

import os
import json
import tempfile
import shutil
from settings import CONSTANTS, META_CONTENT
from utils import setup_logging

logger = setup_logging(__file__, __name__)


def write_to_temp_file(payload, temp_path='/tmp/', json_format=True):

    with tempfile.NamedTemporaryFile(mode='w', dir=temp_path, delete=False) as temp_file:
        temp_file_name = temp_file.name
        if json_format:
            json.dump(payload, temp_file)
        else:
            temp_file.write(payload.encode('utf-8'))

    print 'Temp file name: %s' % temp_file_name
    return temp_file_name


def move_temp_file_to_file(temp_file_name, new_file_name):

    try:
        shutil.copy(temp_file_name, new_file_name)
    except Exception, err:
        logger.error('Unexpected error from shutil in copying temporary file to new file: %s' % err)

    try:
        os.remove(temp_file_name)
    except Exception, err:
        logger.error('Unexpected error from os removing a file: %s' % err)


def write_file(file_name, payload, json_format=True):

    temp_path = os.path.dirname(file_name)

    temp_file_name = write_to_temp_file(payload, temp_path=temp_path, json_format=json_format)
    move_temp_file_to_file(temp_file_name, file_name)


def write_content(payload_dictionary):

    meta_output_file_path = payload_dictionary[CONSTANTS['META_PATH']]
    bibcode_pair_tree_path = os.path.dirname(meta_output_file_path)
    full_text_output_file_path = os.path.join(bibcode_pair_tree_path, 'fulltext.txt')

    if not os.path.exists(bibcode_pair_tree_path):
        try:
            os.makedirs(bibcode_pair_tree_path)
        except OSError:
            raise OSError

    # Write everything but the full text content to the meta.json
    meta_dict = {}

    for const in CONSTANTS:
        if const in ["FULL_TEXT", "ACKNOWLEDGEMENTS", "DATASET"]: continue
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

            try:
                meta_constant_file_path = os.path.join(bibcode_pair_tree_path, meta_key_word) + '.txt'
                logger.info("Writing %s to file at: %s" % (meta_key_word, meta_constant_file_path))
                write_file(meta_constant_file_path, meta_key_word_value, json_format=False)
                logger.info("Writing complete.")
            except IOError:
                raise IOError

        except KeyError:
            logger.info("Does not contain the following meta data: %s" % meta_key_word)
            continue

    # Write the full text content to its own file fulltext.txt
    logger.info("Copying full text content")
    full_text_dict = {CONSTANTS['FULL_TEXT']: payload_dictionary[CONSTANTS['FULL_TEXT']]}

    try:
        logger.info("Writing to file: %s" % meta_output_file_path)
        logger.info("Content has keys: %s" % (meta_dict.keys()))
        write_file(meta_output_file_path, meta_dict, json_format=True)
        logger.info("Writing complete.")
    except IOError:
        raise IOError

    try:
        logger.info("Writing to file: %s" % full_text_output_file_path)
        logger.info("Content has length: %d" % (len(full_text_dict[CONSTANTS['FULL_TEXT']])))
        write_file(full_text_output_file_path, full_text_dict[CONSTANTS['FULL_TEXT']], json_format=False)
        logger.info("Writing complete.")
    except KeyError:
        KeyError(full_text_dict)
    except IOError:
        raise IOError


def extract_content(input_list, **kwargs):

    logger.info('WriteMetaFile: Beginning list with type: %s' % type(input_list))
    for dict_item in input_list:
        try:
            write_content(dict_item)
        except Exception:
            import traceback
            logger.info("Failed on dict item: %s" % dict_item)
            raise Exception(traceback.format_exc())

    return 1