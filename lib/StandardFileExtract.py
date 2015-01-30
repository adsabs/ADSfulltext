"""
StandardFileExtractor Worker Functions

These are the functions for the StandardFileExtractor class. This worker should be able to extract the contents of all
document types, excluding PDF. A lot of the source code has been ported from adsabs/adsdata
"""

import json


def extract_content(message, extract_key):

    return json.dumps(message)