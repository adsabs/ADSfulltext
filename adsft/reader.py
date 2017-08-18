"""
ReadMetaFile Worker Functions

The function class for the ReadMetaFile workers. The aim of the worker is to
read previously extracted content.
"""
import os
import json

from adsft.app import logger


def read_file(input_filename, json_format=True):
    """
    Read file

    :param input_filename: File name to be read
    :param json_format: whether the given content is in json format
    :return: File content
    """

    input_file = open(input_filename, "r")
    if json_format:
        content = json.load(input_file)
    else:
        content = input_file.read()
    input_file.close()

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
    full_text_output_file_path = os.path.join(bibcode_pair_tree_path, 'fulltext.txt')
    grobid_full_text_output_file_path = os.path.join(bibcode_pair_tree_path, 'grobid_fulltext.xml')

    content = {}
    if os.path.exists(meta_output_file_path):
        meta_dict = read_file(meta_output_file_path, json_format=True)
        for key, value in meta_dict.iteritems():
            content[key] = value

        if os.path.exists(full_text_output_file_path):
            fulltext = read_file(full_text_output_file_path, json_format=False)
            content['fulltext'] = fulltext
        else:
            content['fulltext'] = ""

        if os.path.exists(grobid_full_text_output_file_path):
            fulltext = read_file(grobid_full_text_output_file_path, json_format=False)
            content['grobid_fulltext'] = grobid_fulltext
        else:
            content['grobid_fulltext'] = ""

        return content
    else:
        return None


