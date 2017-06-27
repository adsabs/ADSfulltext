"""
CheckIfExtract Worker Functions

These are the functions for the CheckIfExtract class. This worker should
determine if the record selected by the given BibCode should be modified or not
based on a given timing criteria (or changleable if required).
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

PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(PROJECT_HOME)

import utils
import json
import ptree
import traceback

from stat import ST_MTIME
from datetime import datetime
from settings import config, CONSTANTS
from utils import setup_logging
from dateutil.parser import parse

logger = setup_logging(__file__, __name__)


def file_last_modified_time(file_input):
    """
    Stats the given file to find the last modified time

    :param file_input: path to file
    :return: date time object of the last modified time
    """

    mtime = os.stat(file_input)[ST_MTIME]
    return datetime.fromtimestamp(mtime)


def create_meta_path(dict_input, extract_key='FULLTEXT_EXTRACT_PATH'):
    """
    Converts the BibCode of the file into a pair tree path name. For example,
    2015TEST would be converted into '20/15/TE/ST/'.

    :param dict_input: meta-data content of the article given
    :param extract_key: path to extract the full text content to
    :return: BibCodes pair tree path
    """

    ptr = ptree.id2ptree(dict_input[CONSTANTS['BIBCODE']])
    extract_path = config[extract_key] + ptr + 'meta.json'
    logger.debug('extract_path: {0}'.format(extract_path))

    return extract_path


def meta_output_exists(file_input, extract_key='FULLTEXT_EXTRACT_PATH'):
    """
    Checks if there is already a meta-data json file on disk.

    :param file_input: dictionary containing article meta-data
    :param extract_key: path to extract the full text content to
    :return: boolean value; does the path exist or not
    """

    meta_full_path = create_meta_path(file_input, extract_key)

    if os.path.isfile(meta_full_path):
        return True
    else:
        return False


def load_meta_file(file_input, extract_key='FULLTEXT_EXTRACT_PATH'):
    """
    Loads the meta-data file using the python JSON library.

    :param file_input: dictionary containing article meta-data
    :param extract_key: path to extract the full text content to
    :return: the content of the meta-data file
    """

    meta_full_path = create_meta_path(file_input, extract_key)

    content = None

    try:
        with open(meta_full_path, 'r') as f:
            content = json.loads(f.read())

        logger.debug('Meta file already exists')

    except IOError:
        logger.warning('IOError: Json content could not be loaded: \n{0}, \n{1}'
                       .format(meta_full_path, file_input))
        raise IOError

    except Exception:
        logger.warning('Unexpected error')
        raise Exception

    return content


def meta_needs_update(dict_input, meta_content,
                      extract_key='FULLTEXT_EXTRACT_PATH'):
    """
    By examining the meta-data file and the relevant full text file, it checks
    if the full text should be extracted for the first time (or again). The
    relevant reasons for extraction are:
      1. MISSING_FULL_TEXT: There is no full texte
      2. DIFFERING_FULL_TEXT: The path in the meta.json differs to the one given
      3. STALE_CONTENT: the meta.json is older than the full text file
      4. STALE_META: the meta.json file does not all the required keys

    The return value is empty if none of the above are true.

    :param dict_input: dictionary containing article meta-data
    :param meta_content: the content in the old meta-data file
    :param extract_key: the content of the meta-data file
    :return: the keyword that describes why it should be extracted
    """

    # Obtain the indexed date within the meta file
    try:
        time_stamp = meta_content[CONSTANTS['TIME_STAMP']]
        meta_date = parse(time_stamp)
        bibcode = meta_content[CONSTANTS['BIBCODE']]
    except KeyError:
        logger.warning("Malformed meta-file: %s", traceback.format_exc())
        return 'STALE_META'
        #raise KeyError
    except Exception:
        logger.warning('Unexpected error {0}'.format(sys.exc_info()))
        raise Exception

    logger.debug('Opened existing meta to determine if an update is required.')

    # No extraction exists
    if CONSTANTS['FILE_SOURCE'] not in meta_content:
        return 'MISSING_FULL_TEXT'

    # Full text file path has changed
    if meta_content[CONSTANTS['FILE_SOURCE']] != \
            dict_input[CONSTANTS['FILE_SOURCE']]:
        return 'DIFFERING_FULL_TEXT'

    # Content is considered 'stale'
    delta_comp_time = datetime.utcnow() - datetime.now()

    ft_source_last_modified = \
        file_last_modified_time(meta_content[CONSTANTS['FILE_SOURCE']])
    ft_source_last_modified += delta_comp_time

    meta_path = create_meta_path(dict_input, extract_key=extract_key)

    meta_json_last_modified = file_last_modified_time(meta_path)

    # If the source content is more new than the last time it was extracted
    logger.debug(
        'FILE_SOUCE last modified: {0}'.format(ft_source_last_modified))
    logger.debug('META_PATH last modified: {0}'.format(meta_json_last_modified))
    if ft_source_last_modified > meta_json_last_modified:
        return 'STALE_CONTENT'


def check_if_extract(message_list, extract_key='FULLTEXT_EXTRACT_PATH'):
    """
    For each bibcode in the list, it is checked if it should be extracted by
    examining the meta-data supplied, the meta-data that exists in the current
    file on disk, and the full text content file on path. The possible option
    in this function are:

      1. NOT_EXTRACTED_BEFORE: has not been extracted

    The remaining possibilties come from meta_needs_update(). If the type of
    file is a PDF, it gets add to a different output list so that it can
    get passed to a different extraction queue not used by the other file types.

    :param message_list: list of dictionaries the aricles meta-data
    :param extract_key: the content of the meta-data file
    :return: dictionary containing two lists. One for PDF files and the other
    for normal files. It adds the extra keyword UPDATE which explains why the
    extraction of the full text is required.
    """

    NEEDS_UPDATE = ["MISSING_FULL_TEXT", "DIFFERING_FULL_TEXT", "STALE_CONTENT",
                    "STALE_META", "NOT_EXTRACTED_BEFORE", "FORCE_TO_EXTRACT"]

    publish_list_of_standard_dictionaries = []
    publish_list_of_pdf_dictionaries = []

    for message in message_list:

        # message should be a dictionary
        print(message.keys())
        if CONSTANTS['UPDATE'] in message.keys() \
                and message[CONSTANTS['UPDATE']] == 'FORCE_TO_EXTRACT':
            update = 'FORCE_TO_EXTRACT'

        elif meta_output_exists(message, extract_key=extract_key):
            meta_content = load_meta_file(message, extract_key=extract_key)
            update = meta_needs_update(message, meta_content,
                                       extract_key=extract_key)
        else:
            logger.debug('No existing meta file')
            update = 'NOT_EXTRACTED_BEFORE'

        logger.debug('Update required?: {0}'.format(update))
        logger.debug('Creating meta path')

        message[CONSTANTS['META_PATH']] = \
            create_meta_path(message, extract_key=extract_key)

        logger.debug('created: %s' % message[CONSTANTS['META_PATH']])

        format_ = os.path.splitext(
            message[CONSTANTS['FILE_SOURCE']])[-1].replace('.', '').lower()

        if not format_ and 'http://' in message[CONSTANTS['FILE_SOURCE']]:
            format_ = 'http'
        message[CONSTANTS['FORMAT']] = format_

        logger.debug('Format found: %s' % format_)
        if update in NEEDS_UPDATE and format_ == 'pdf':
            message[CONSTANTS['UPDATE']] = update

            logger.info('CheckIfExtract: needs update because {0}: {1}'.format(
                update, message[CONSTANTS['BIBCODE']]))

            publish_list_of_pdf_dictionaries.append(message)

        elif update in NEEDS_UPDATE:
            message[CONSTANTS['UPDATE']] = update

            logger.info('CheckIfExtract: needs update because {0}: {1}'.format(
                update, message[CONSTANTS['BIBCODE']]))

            publish_list_of_standard_dictionaries.append(message)

        # Wite a time stamp of this process
        message[CONSTANTS['TIME_STAMP']] = datetime.utcnow().isoformat() + 'Z'

        logger.debug('Adding timestamp: {0}'.format(
            message[CONSTANTS['TIME_STAMP']]))

        logger.debug('Returning dictionaries')

    if len(publish_list_of_pdf_dictionaries) == 0:
        publish_list_of_pdf_dictionaries = None
        logger.debug('PDF list is empty, setting to none')

    if len(publish_list_of_standard_dictionaries) == 0:
        publish_list_of_standard_dictionaries = None
        logger.debug('Standard list is empty, setting to none')

    return {'Standard': json.dumps(publish_list_of_standard_dictionaries),
            'PDF': json.dumps(publish_list_of_pdf_dictionaries)}
