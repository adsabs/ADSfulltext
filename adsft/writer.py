"""
WriteMetaFile Worker Functions

The function class for the WriteMetaFile workers. The aim of the worker is to
take the content delivered, and write it to a file on disk.
"""

__author__ = 'J. Elliott'
__maintainer__ = 'J. Elliott'
__copyright__ = 'Copyright 2015'
__version__ = '1.0'
__email__ = 'ads@cfa.harvard.edu'
__status__ = 'Production'
__credit__ = ['V. Sudilovsky', 'A. Accomazzi', 'J. Luker']
__license__ = 'GPLv3'

import sys
import os
import json
import tempfile
import shutil
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

def write_to_temp_file(payload, temp_path='/tmp/', json_format=True):
    """
    Writes the received payloadto a temporary file using the temporary file lib

    :param payload: text received from the pipeline
    :param temp_path: path to write the temporary file
    :param json_format: whether the given content is in json format
    :return: the temporary file name written to disk
    """

    with tempfile.NamedTemporaryFile(mode='w', dir=temp_path,
                                     delete=False) as temp_file:
        temp_file_name = temp_file.name
        temp_file_name_compress = temp_file_name + '.gz'
        if json_format:
            json.dump(payload, temp_file)
        else:
            if sys.version_info < (3,) and isinstance(payload, unicode):
                temp_file.write(payload.encode('utf-8'))
            else:
                temp_file.write(payload) # assuming this is already a bytecode
            temp_file.close()
            with open(temp_file_name, 'rb') as file_in:
                try:
                    with gzip.open(temp_file_name_compress, 'wb') as file_out:
                        shutil.copyfileobj(file_in, file_out)
                    os.chmod(temp_file_name_compress, 0o640)
                except Exception as err:
                    logger.error('Unexpected error from shutil in copying temp file to compressed temp file: %s', err)

            try:
                os.remove(temp_file_name)
            except Exception as err:
                logger.error('Unexpected error from os in removing non-compressed temp file: %s', err)

            temp_file_name = temp_file_name_compress

    logger.debug('Temp file name: %s', temp_file_name)

    return temp_file_name


def move_temp_file_to_file(temp_file_name, new_file_name):
    """
    Copies the temporary file to a new file with the wanted name. Removes the
    old  temporary file on success.

    :param temp_file_name: name of the temporary file
    :param new_file_name: name wanted for the final file
    :return: no return is given
    """

    try:
        shutil.copy(temp_file_name, new_file_name)
        # protect full-text from world access but keep it group-readable
        os.chmod(new_file_name, 0o640)
    except Exception as err:
        logger.error('Unexpected error from shutil in copying temporary file to new file: %s', err)

    try:
        os.remove(temp_file_name)
    except Exception as err:
        logger.error('Unexpected error from os removing a file: %s', err)

    logger.debug('Succeeded to copy: %s to %s', temp_file_name, new_file_name)

def write_file(file_name, payload, json_format=True):
    """
    A wrapper function for two separate functions, with the aim of:
      1. creating a temporary file with the payload as content
      2. moving the temporary file to the wanted file name

    This approach is used in case of a race-condition, where two workers
    have the same output path, and will stop the chance of corrupted files

    :param file_name: desired file name for output
    :param payload: the content to be written to disk
    :param json_format: whether or not the payload is in json format
    :return: no return
    """

    temp_path = os.path.dirname(file_name)
    temp_file_name = write_to_temp_file(payload, temp_path=temp_path,
                                        json_format=json_format)
    move_temp_file_to_file(temp_file_name, file_name)


def write_content(payload_dictionary):
    """
    Function that writes a single document to file. It expects a json-type
    payload that has been converted into a Python dictionary.
    A temporary file will be written to disk for:
      1. full text content
      2. acknowledgements
      3. dataset items
      4. a meta.json file containing relevant meta-data defined in settings.py

    The files are then moved to their expected names, and the temporary
    files removed.

    :param payload_dictionary: the complete extracted content and meta-data of
    the document payload
    :return: no return
    """

    meta_output_file_path = payload_dictionary['meta_path']
    bibcode_pair_tree_path = os.path.dirname(meta_output_file_path)
    if payload_dictionary['file_format'] == 'pdf-grobid':
        full_text_output_file_path = os.path.join(bibcode_pair_tree_path, 'grobid_fulltext.xml')
    else:
        full_text_output_file_path = os.path.join(bibcode_pair_tree_path, 'fulltext.txt.gz')

    if 'UPDATE' in payload_dictionary and \
        payload_dictionary['UPDATE'] == 'FORCE_TO_SEND' and \
        os.path.exists(meta_output_file_path) and os.path.exists(full_text_output_file_path):
            # Data was already extracted and saved
            return

    if not os.path.exists(bibcode_pair_tree_path):
        try:
            os.makedirs(bibcode_pair_tree_path)
        except OSError:
            raise OSError

    # Write everything but the full text content to the meta.json
    meta_dict = {}

    for const in ('meta_path', 'ft_source', 'bibcode', 'provider', 'UPDATE', 'file_format', 'index_date', 'dataset', 'facility'):
        try:
            meta_dict[const] = payload_dictionary[const]
            logger.debug('Adding meta content: %s', const)
        except KeyError:
            #print('Missing meta content: {0}'.format(const))
            continue

    # Write the custom extractions of content to the meta.json
    logger.debug('Copying extra meta content')
    for meta_key_word in META_CONTENT[payload_dictionary['file_format']]:
        if meta_key_word in ('dataset', 'fulltext', 'facility'):
            continue

        logger.debug(meta_key_word)
        try:
            meta_key_word_value = payload_dictionary[meta_key_word]
            meta_dict[meta_key_word] = meta_key_word_value

            try:
                meta_constant_file_path = os.path.join(bibcode_pair_tree_path,
                                                       meta_key_word) + '.txt.gz'
                logger.debug('Writing %s to file at: %s', meta_key_word, meta_constant_file_path)
                write_file(meta_constant_file_path, meta_key_word_value,
                           json_format=False)
                logger.info('WriteMetaFile: completed bibcode: %s', payload_dictionary['bibcode'])
            except IOError:
                logger.error('IO Error when writing to file.')
                raise IOError

        except KeyError:
            logger.debug('Does not contain the following meta data: %s', meta_key_word)
            continue

    # Write the full text content to its own file fulltext.txt.gz
    logger.debug('Copying full text content')

    if 'fulltext' in payload_dictionary and payload_dictionary['fulltext'] != "":
        try:
            logger.debug('Writing to file: %s', full_text_output_file_path)
            logger.debug('Content has length: %s', len(payload_dictionary['fulltext']))
            write_file(full_text_output_file_path, payload_dictionary['fulltext'], json_format=False)
            logger.debug('Writing complete.')
        except IOError:
            logger.exception('IO Error when writing to file %s', payload_dictionary['bibcode'])
            raise IOError
    #else:
        #logger.warning('No fulltext found for dictionary {0}'.format(payload_dictionary['bibcode']))

    if payload_dictionary['file_format'] != "pdf-grobid":
        # Do not write meta-data if it is a grobid extraction, only grobid_fulltext.xml is required
        # and we avoid over-writting valid meta-data from the regular PDF extraction
        try:
            logger.debug('Writing to file: %s', meta_output_file_path)
            logger.debug('Content has keys: %s', meta_dict.keys())
            write_file(meta_output_file_path, meta_dict, json_format=True)
            logger.debug('Writing complete.')
        except IOError:
            logger.exception('IO Error when writing to file.')
            raise IOError


def extract_content(input_list, **kwargs):
    """
    Loops through each document received from the upstream queue, and writes
    them to file using the modularised function for single documents. A list
    of all the successfully documents written to disk is created, which will
    be passed on to an external pipeline.

    :param input_list: containing a dictionary for each article extracted
    :param kwargs: currently redundant
    :return: list of bibcodes written to disk and converted to json format
    """

    logger.debug('WriteMetaFile: Beginning list with type: %s', input_list)
    bibcode_list = []
    for dict_item in input_list:
        try:
            write_content(dict_item)
            bibcode_list.append(dict_item['bibcode'])
        except Exception:
            import traceback

            logger.error('Failed on dict item: %s (%s)', dict_item, traceback.format_exc())
            raise Exception

    return json.dumps(bibcode_list)
