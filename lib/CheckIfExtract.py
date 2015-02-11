"""
CheckIfExtract Worker Functions

These are the functions for the CheckIfExtract class. This worker should determine if the record selected by the given BibCode should be modified or not based on a given timing criteria (or changleable if required).
"""

import os
import utils
import json
from datetime import datetime
from settings import config, CONSTANTS
from utils import setup_logging
from dateutil.parser import parse

logger = setup_logging(__file__, __name__)


def file_last_modified_time(file_input):
    """
    stat a file to get last mod time
    """
    from stat import ST_MTIME
    mtime = os.stat(file_input)[ST_MTIME]
    return datetime.fromtimestamp(mtime)


def create_meta_path(dict_input, extract_key="FULLTEXT_EXTRACT_PATH"):

    import ptree
    ptr = ptree.id2ptree(dict_input[CONSTANTS['BIBCODE']])
    extract_path = config[extract_key] + ptr + "meta.json"

    return extract_path


def meta_output_exists(file_input, extract_key="FULLTEXT_EXTRACT_PATH"):

    meta_full_path = create_meta_path(file_input, extract_key)

    if os.path.isfile(meta_full_path):
        return True
    else:
        return False


def load_meta_file(file_input, extract_key="FULLTEXT_EXTRACT_PATH"):

    meta_full_path = create_meta_path(file_input, extract_key)

    content = None

    try:
        with open(meta_full_path) as f:
            content = json.loads(f.read())
    except IOError:
        raise IOError("IOError: Json content could not be loaded: \n%s, \n%s" % (meta_full_path, file_input))
    except Exception:
        logger.warning("Unexpected error")
        raise Exception
    return content


def meta_needs_update(dict_input, meta_content, extract_key="FULLTEXT_EXTRACT_PATH"):

    import sys

    # Obtain the indexed date within the meta file
    try:
        meta_date = parse(meta_content["index_date"])
    except KeyError:
        logger.warning("Malformed meta-file")
    except:
        logger.warning("Unexpected error %s" % sys.exc_info())

    # No extraction exists
    if CONSTANTS['FILE_SOURCE'] not in meta_content:
        return 'MISSING_FULL_TEXT'

    # Full text file path has changed
    if meta_content[CONSTANTS['FILE_SOURCE']] != dict_input[CONSTANTS['FILE_SOURCE']]:
        return 'DIFFERING_FULL_TEXT'

    # Content is considered 'stale'
    delta_comp_time = datetime.utcnow() - datetime.now()

    ft_source_last_modified = file_last_modified_time(meta_content[CONSTANTS['FILE_SOURCE']])
    ft_source_last_modified += delta_comp_time

    meta_path = create_meta_path(dict_input, extract_key=extract_key)

    meta_json_last_modified = file_last_modified_time(meta_path)

    # If the source content is more new than the last time it was extracted
    if ft_source_last_modified > meta_json_last_modified:
        return 'STALE_CONTENT'


def check_if_extract(message_list, extract_key="FULLTEXT_EXTRACT_PATH"):

    NEEDS_UPDATE = ["MISSING_FULL_TEXT", "DIFFERING_FULL_TEXT", "STALE_CONTENT", "NOT_EXTRACTED_BEFORE"]

    publish_list_of_standard_dictionaries = []
    publish_list_of_pdf_dictionaries = []

    for message in message_list:

        # message should be a dictionary
        if meta_output_exists(message, extract_key=extract_key):
            meta_content = load_meta_file(message, extract_key=extract_key)
            update = meta_needs_update(message, meta_content, extract_key=extract_key)
        else:
            update = "NOT_EXTRACTED_BEFORE"

        logger.info('Update required?: %s' % update)
        logger.info('Creating meta path')
        message[CONSTANTS['META_PATH']] = create_meta_path(message, extract_key=extract_key)
        logger.info('created: %s' % message[CONSTANTS['META_PATH']])

        message[CONSTANTS['FORMAT']] = format_ = message[CONSTANTS['FILE_SOURCE']].split(".")[-1].lower()
        logger.info('Format found: %s' % format_)
        if update in NEEDS_UPDATE and format_ == 'pdf':
            message[CONSTANTS['UPDATE']] = update

            publish_list_of_pdf_dictionaries.append(message)

        elif update in NEEDS_UPDATE:
            message[CONSTANTS['UPDATE']] = update
            publish_list_of_standard_dictionaries.append(message)


        # Wite a time stamp of this process
        message[CONSTANTS['TIME_STAMP']] = datetime.utcnow().isoformat() + 'Z'

        logger.info("Adding timestamp: %s" % message[CONSTANTS['TIME_STAMP']])o
        logger.info('Returning dictionaries')

        if len(publish_list_of_pdf_dictionaries) == 0:
            publish_list_of_pdf_dictionaries = None
            logger.info('PDF list is empty, setting to none')

        if len(publish_list_of_standard_dictionaries) == 0:
            publish_list_of_standard_dictionaries = None
            logger.info('Standard list is empty, setting to none')

    return {"Standard": json.dumps(publish_list_of_standard_dictionaries),
            "PDF": json.dumps(publish_list_of_pdf_dictionaries)}