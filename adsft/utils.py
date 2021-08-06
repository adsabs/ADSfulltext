"""
Contains useful functions and utilities that are not neccessarily only useful
for this module. But are also used in differing modules insidide the same
project, and so do not belong to anything specific.
"""
from __future__ import print_function

import sys

from builtins import chr
from builtins import range
from builtins import object
if sys.version_info > (3,):
    from builtins import str
__author__ = 'J. Elliott'
__maintainer__ = 'J. Elliott'
__copyright__ = 'Copyright 2015'
__version__ = '1.0'
__email__ = 'ads@cfa.harvard.edu'
__status__ = 'Production'
__credit__ = ['V. Sudilovsky']
__license__ = 'GPLv3'

import os
import string
import unicodedata
import re
import json

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


# ================================ CLASSES ======================================== #

class FileInputStream(object):
    """
    A custom data format that handles all the file input/output in the
    ADSfulltext project.
    """

    def __init__(self, input_stream):
        """
        Initialisation (constructor) method of the class
        :param input_stream: the path to the file that needs to be loaded
        :return: no return
        """

        self.input_stream = input_stream
        self.bibcode = ''
        self.full_text_path = ''
        self.provider = ''
        self.payload = None

    def print_info(self):
        """
        Prints relevant information about the input stream
        :return: no return
        """

        print('Bibcode: {0}'.format(self.bibcode))
        print('Full text path: {0}'.format(self.full_text_path))
        print('Provider: {0}'.format(self.provider))
        print('Payload content: {0}'.format(self.payload))

    def extract(self, force_extract=False, force_send=False):
        """
        Opens the file and parses the content depending on the type of input
        :param force_extract: boolean decides if the normal checks should
        be ignored and extracted regardless
        :param force_send: boolean decides if the normal checks should
        be ignored and send regardless
        :return: the bibcode, full text path, provider, and payload content
        """

        in_file = self.input_stream
        try:
            with open(in_file, 'r') as f:

                    raw = []
                    bibcode, full_text_path, provider = [], [], []
                    for line in f:
                        try:
                            l = [i for i in line.strip().split('\t') if i != '']
                            if len(l) == 0:
                                continue
                            bibcode.append(l[0])
                            full_text_path.append(l[1])
                            provider.append(l[2])
                            payload_dictionary = {
                                'bibcode': bibcode[-1],
                                'ft_source': full_text_path[-1],
                                'provider': provider[-1]
                            }

                            if force_extract:
                                payload_dictionary['UPDATE'] = \
                                    'FORCE_TO_EXTRACT'

                            if force_send and not force_extract:
                                payload_dictionary['UPDATE'] = \
                                    'FORCE_TO_SEND'

                            raw.append(payload_dictionary)
                        except Exception as err:
                            logger.warning('Extraction failed for file %s, line: %s. Skipping', in_file, line)
                            continue
            self.bibcode = bibcode
            self.full_text_path = full_text_path
            self.provider = provider
            self.payload = raw

        except IOError as err:
            logger.warning('Exception in extracting file %s. Stacktrace: %s', in_file, sys.exc_info())

        return self.bibcode, self.full_text_path, self.provider, self.payload



class TextCleaner(object):
    """
    Class that contains methods to clean text.

    For Unicode character translation, the input is a dict where
    the keys are the code points to be replaced and the value is
    what to replace them with. Best practice is that some code
    points are replaced with spaces, some are deleted (replaced
    with '').

    """

    # WHITE_SPACE category here: http://www.unicode.org/Public/UCD/latest/ucd/PropList.txt
    replace_with_space = [(0x0B, 0x0D), (0xA0, 0xA0),
                          (0x1680, 0x1680), (0x2000, 0x200A),
                          (0x202F, 0x202F), (0x205F, 0x205F),
                          (0x3000, 0x3000)]
    map_replace_with_space = dict.fromkeys(
        (n for start, end in replace_with_space
         for n in range(start, end + 1)),
        ' '
    )

    # guidance from here: http://unicode.org/faq/unsup_char.html
    replace_with_none = [(0x00, 0x08), (0x0E, 0x1F),
                         (0x7F, 0x84), (0x86, 0x9F),
                         (0xAD, 0xAD),
                         (0x200B, 0x200E), (0x202A, 0x202E),
                         (0x2060, 0x2064), (0x206A, 0x206F),
                         (0xD800, 0xDFFF), (0xE000, 0xF8FF),
                         (0xFDD0, 0xFDDF), (0xFEFF, 0xFEFF),
                         (0xFFFE, 0xFFFF), (0x1FFFE, 0x1FFFF),
                         (0x2FFFE, 0x2FFFF), (0x3FFFE, 0x3FFFF),
                         (0x4FFFE, 0x4FFFF), (0x5FFFE, 0x5FFFF),
                         (0x6FFFE, 0x6FFFF), (0x7FFFE, 0x7FFFF),
                         (0x8FFFE, 0x8FFFF), (0x9FFFE, 0x9FFFF),
                         (0xAFFFE, 0xAFFFF), (0xBFFFE, 0xBFFFF),
                         (0xCFFFE, 0xCFFFF), (0xDFFFE, 0xDFFFF),
                         (0xEFFFE, 0xEFFFF), (0xFFFFE, 0xFFFFF),
                         (0x10FFFE, 0x10FFFF)]

    master_translate_map = dict.fromkeys(
        (n for start, end in replace_with_none
         for n in range(start, end + 1))
    )

    # merge the two translation maps, prioritizing the map to space translations
    tmp = master_translate_map.update(map_replace_with_space)

    def __init__(self, text):
        """
        Initialisation method (constructor) of the class

        For those interested:
        http://www.joelonsoftware.com/articles/Unicode.html

        unicodedata.normalize(unicode_string, 'NFKC'):

        https://docs.python.org/2/library/
            unicodedata.html#unicodedata.normalize

        http://stackoverflow.com/questions/14682397/can-somone-
            explain-how-unicodedata-normalizeform-unistr-work-with-examples

        NFKC = Normal Form K Composition

        'K' converts characters such as circle(1) to 1
        'C' composes characters such as C, to C+,

        :param text: input text to clean
        :return: no return
        """

        self.text = text

    def translate(self):
        """
        Removes escape characters whether the text is unicode or ASCII
        :return: no return
        """

        self.text = self.text.translate(self.master_translate_map)

    def decode(self):
        """
        Decodes the text into unicode expected UTF-8 encoding
        :return: no return
        """

        if sys.version_info > (3,):
            test_type = bytes
        else:
            test_type = str
        if isinstance(self.text, test_type):
            self.text = self.text.decode('utf-8', 'ignore')

    def normalise(self):
        """
        Normalises different combination of characters into a single chracter
        :return: no return
        """

        # Convert non-ASCII characters to closest ASCII equivalent
        #
        # In unicode, several characters can be expressed in different ways:
        # For instance, the character U+00C7 (latin capital letter c with cedilla)
        # can also be expressed as the sequence U+0043 (latin capital letter c) U+0327 (combining cedilla)
        #
        # For each character, there are two normal forms:
        # NFD (normal form D): translates each character into its decomposed form (aka canonical decomposition)
        # NFC (normal form C): applies a canonical decomposition, then composes pre-combined characters again
        #
        # In Unicode, certain characters are supported which normally would be unified with other characters
        # (e.g., non-breaking space '\xa0' with space ' ', Roman numeral one and latin capital letter I)
        # NFKD: apply the compatibility decomposition (i.e. replace all compatibility characters with their equivalents)
        # NFKC: applies the compatibility decomposition, followed by the canonical composition
        if sys.version_info > (3,):
            test_type = str
        else:
            test_type = unicode

        self.text = unicodedata.normalize('NFKC', test_type(self.text))

    def trimwords(self, maxlength=100):
        """
        Removes "words" longer than wordlength characters, which tend to be
        artifacts generated by the text extraction pipeline (typically tables).
        We do this because these huge words cause problems further down the line
        when they are indexed in SOLR
        :param maxlength: maximum length of words to keep
        :return: no return
        """
        self.text = " ".join([word for word in self.text.split() if len(word) < maxlength])

    def run(self, translate=True, decode=True, normalise=True, trim=True):
        """
        Wrapper method that can run all of the methods wanted by the user
        in one executable.

        :param translate: should it translate, boolean
        :param decode: should it decode, boolean
        :param normalise: should it normalise, boolean
        :param trimwords: remove long sequences of non-blank characters (usually garbage)
        :return: cleaned text
        """

        if translate:
            self.translate()
        if decode:
            self.decode()
        if normalise:
            self.normalise()
        if trim:
            self.trimwords()

        return self.text

def get_filenames(file_string):
    """convert passed string containing one or more files to an array of files

    file_string could be a sigle file, a simple comma separated list of files
    or it could include a comman in either the filename or the pathname
    we can't use a comma as a delimeter
    instead, since all paths are absolute, we use the first two directory names
    in the absolution path as a delimter
    example simple input:
    /proj/ads/fulltext/sources/A+A/backdata/2003/17/aah3724/aah3724.right.html,/proj/ads/fulltext/sources/A+A/backdata/2003/17/aah3724/tableE.1.html
    example input with comman in filename:
    /proj/ads/fulltext/sources/downloads/cache/POS/pos.sissa.it//archive/conferences/075/001/BHs,%20GR%20and%20Strings_001.pdf
    """
    if file_string[0] != '/':
        raise ValueError('expected absolute pathname to start with / character: {}'.format(file_string))
    second_slash_index = file_string.index('/', 1)
    third_slash_index = file_string.index('/', second_slash_index+1)
    prefix = file_string[:third_slash_index+1]

    # split input string over prefix delimeter, add prefix back to string
    files = [prefix+f for f in file_string.split(prefix) if f]
    # remove trailing commas, they are actual delimiters
    for i in range(0, len(files)):
        if files[i][-1] == ',':
            files[i] = files[i][:-1]

    return files
