"""
Contains useful functions and utilities that are not neccessarily only useful
for this module. But are also used in differing modules insidide the same
project, and so do not belong to anything specific.
"""

__author__ = 'J. Elliott'
__maintainer__ = 'J. Elliott'
__copyright__ = 'Copyright 2015'
__version__ = '1.0'
__email__ = 'ads@cfa.harvard.edu'
__status__ = 'Production'
__credit__ = ['V. Sudilovsky']
__license__ = 'GPLv3'

import sys
import os
import logging
import string
import unicodedata
import re
import json



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

        print 'Bibcode: {0}'.format(self.bibcode)
        print 'Full text path: {0}'.format(self.full_text_path)
        print 'Provider: {0}'.format(self.provider)
        print 'Payload content: {0}'.format(self.payload)

    def extract(self, force_extract=False):
        """
        Opens the file and parses the content depending on the type of input
        :param force_extract: boolean decides if the normal checks should
        be ignored and extracted regardless
        :return: the bibcode, full text path, provider, and payload content
        """

        in_file = self.input_stream
        try:
            with open(in_file, 'r') as f:

                raw = []
                bibcode, full_text_path, provider = [], [], []
                for line in f:

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

                    raw.append(payload_dictionary)

            self.bibcode = bibcode
            self.full_text_path = full_text_path
            self.provider = provider
            self.payload = raw

        except IOError:
            print in_file, sys.exc_info()

        return self.bibcode, self.full_text_path, self.provider, self.payload



class TextCleaner(object):
    """
    Class that contains methods to clean text.
    """

    def __init__(self, text):
        """
        Initialisation method (constructor) of the class

        For those interested:
        http://www.joelonsoftware.com/articles/Unicode.html

        Translation map (ASCII):
            This is used to replace the escape characters. There are 32 escape
            characters listed for example
            here: http://www.robelle.com/smugbook/ascii.html

            input_control_characters:
            This is a string that contains all the escape characters

            translated_control_characters:
            This is a string that is equal in length to input_control
            characters, where all the escape characters
            are replaced by an empty string ' '. The only escape characters
            kept are \n, \t, \r, (9, 10, 13)

            This map can then be given to the string.translate as the map for
            a string (ASCII encoded)
            e.g.,

            'jonny\x40myemail.com\n'.translate(dict.fromkeys(filter(lambda x:
             x not in [9,10,13], range(32))))
            'jonny@myemail.com\n'

        Translation map (Unicode):
            This has the same purpose as the previous map, except it works on
            text that is encoded in utf-8, or some other unicode encoding. The
            unicode_control_number array contains a list of tuples, that
            contain the range of numbers that want to be removed. i.e., 0x00,
            0x08 in unicode form is U+00 00 to U+00 08, which is just removing
            the e.g., Null characters, see
            http://www.fileformat.info/info/charset/UTF-8/list.htm
            for a list of unicode numberings.
            e.g.,

            This map can then be given to the string.translate as the map for
            a unicode type (e.g., UTF-8 encoded)

            u'jonny\x40myemail.com\n'.translate(dict.fromkeys(filter(lambda x:
            x not in [9,10,13], range(32))))
            u'jonny@myemail.com\n'


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

        translated_control_characters = ''.join(
            [chr(i) if i in [9, 10, 13] else ' ' for i in range(0, 32)])

        input_control_characters = "".join([chr(i) for i in range(0, 32)])

        self.ASCII_translation_map = string.maketrans(
            input_control_characters, translated_control_characters)

        unicode_control_numbers = [(0x00, 0x08), (0x0B, 0x1F), (0x7F, 0x84),
                                   (0x86, 0x9F), (0xD800, 0xDFFF), (0xFDD0,
                                                                    0xFDDF),
                                   (0xFFFE, 0xFFFF),
                                   (0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF),
                                   (0x3FFFE, 0x3FFFF), (0x4FFFE, 0x4FFFF),
                                   (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
                                   (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF),
                                   (0x9FFFE, 0x9FFFF), (0xAFFFE, 0xAFFFF),
                                   (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
                                   (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF),
                                   (0xFFFFE, 0xFFFFF), (0x10FFFE, 0x10FFFF)]

        self.Unicode_translation_map = dict.fromkeys(
            unicode_number
            for starting_unicode_number, ending_unicode_number
            in unicode_control_numbers
            for unicode_number
            in range(starting_unicode_number, ending_unicode_number+1)
        )

    def translate(self):
        """
        Removes escape characters whether the text is unicode or ASCII
        :return: no return
        """

        if type(self.text) == str:
            self.text = self.text.translate(self.ASCII_translation_map)
        else:
            self.text = self.text.translate(self.Unicode_translation_map)

    def decode(self):
        """
        Decodes the text into unicode expected UTF-8 encoding
        :return: no return
        """

        if type(self.text) == str:
            self.text = self.text.decode('utf-8', 'ignore')

    def normalise(self):
        """
        Normalises different combination of characters into a single chracter
        :return: no return
        """

        self.text = unicodedata.normalize('NFKC', unicode(self.text))
        self.text = re.sub('\s+', ' ', self.text)

    def trimwords(self, maxlength=200):
        """
        Removes "words" longer than wordlength characters, which tend to be
        artifacts generated by the text extraction pipeline (typically tables).
        We do this because these huge words cause problems further down the line
        when they are indexed in SOLR
        :param maxlength: maximum length of words to keep
        :return: no return
        """
        
        # note: we want to keep the original text in the proper sequence of lines 
        # to avoid messing up text analysis downstream
        buffer = []
        for line in self.text.splitlines():
            newline = ' '.join([word if len(word) <= maxlength else '' for word in line.split()])
            buffer.append(newline)

        self.text = '\n'.join(buffer)


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
