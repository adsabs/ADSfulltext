"""
ReadMetaFile Worker Functions

The function class for the ReadMetaFile workers. The aim of the worker is to
read previously extracted content.
"""
import os
import json
import gzip
from adsft.rules import META_CONTENT

# ============================= INITIALIZATION ==================================== #
# - Use app logger:
#import logging
#logger = logging.getLogger('ads-fulltext')
# - Or individual logger for this file:
from adsputils import setup_logging, load_config
proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), '../'))
config = load_config(proj_home=proj_home)
logger = setup_logging(__name__, proj_home=proj_home,
                        level=config.get('LOGGING_LEVEL', 'INFO'),
                        attach_stdout=config.get('LOG_STDOUT', False))


# =============================== FUNCTIONS ======================================= #

def read_file(input_filename, json_format=True):
    """
    Read file

    :param input_filename: File name to be read
    :param json_format: whether the given content is in json format
    :return: File content
    """

    if input_filename.endswith('gz'):
        with gzip.open(input_filename, 'rb') as input_file:
            if json_format:
                content = json.load(input_file)
            else:
                content = input_file.read().decode('utf-8')
    else:
        with open(input_filename, 'r') as input_file:
            if json_format:
                content = json.load(input_file)
            else:
                content = input_file.read().decode('utf-8')

    logger.debug('Read file name: {0}'.format(input_filename))

    return content


def read_content(payload_dictionary):
    """
    Function that reads previously extracted data. It expects a json-type
    payload that has been converted into a Python dictionary.

    :param payload_dictionary: the complete extracted content and meta-data of
    the document payload
    :return: modified dictionary with recovered content or None if files do not exist
    """

    meta_output_file_path = payload_dictionary['meta_path']
    bibcode_pair_tree_path = os.path.dirname(meta_output_file_path)
    if payload_dictionary['file_format'] == "pdf-grobid":
        full_text_output_file_path = os.path.join(bibcode_pair_tree_path, 'grobid_fulltext.xml')
    else:
        full_text_output_file_path = os.path.join(bibcode_pair_tree_path, 'fulltext.txt.gz')

    content = {}
    if os.path.exists(meta_output_file_path):
        meta_dict = read_file(meta_output_file_path, json_format=True)
        for key, value in meta_dict.items():
            content[key] = value

        if os.path.exists(full_text_output_file_path):
            fulltext = read_file(full_text_output_file_path, json_format=False)
            content['fulltext'] = fulltext
        else:
            content['fulltext'] = ""

        # Read the custom extractions of content
        logger.debug('Copying extra meta content')
        for meta_key_word in META_CONTENT[payload_dictionary['file_format']]:
            if meta_key_word in ('dataset', 'fulltext') \
                    or meta_key_word in content.keys():
                continue

            logger.debug(meta_key_word)
            meta_constant_file_path = os.path.join(bibcode_pair_tree_path, meta_key_word) + '.txt.gz'
            logger.debug('Reading {0} from file at: {1}'.format(meta_key_word, meta_constant_file_path))
            if os.path.exists(meta_constant_file_path):
                try:
                    content[meta_key_word] = read_file(meta_constant_file_path, json_format=False)
                except IOError:
                    logger.exception('IO Error when readeing from file: %s', meta_constant_file_path)

        return content
    else:
        return None


