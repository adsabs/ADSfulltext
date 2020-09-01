import sys
from builtins import chr
import unittest
import os
import re

from adsft import utils
from adsft.tests import test_base
import math

class TestFileStreamInput(test_base.TestUnit):
    """
    Class that tests the FileStreamInput class and its methods.
    """

    def test_file_stream_input_extract_file(self):
        """
        Tests the extract method. It checks that the number of rows extracted
        by the class is actually the number of rows inside the file by
        explicitly opening the file and reading the number of lines.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(self.test_file)
        FileInputStream.extract()

        with open(self.test_file, 'r') as f:
            nor = len(f.readlines())

        self.assertEqual(
            len(FileInputStream.bibcode),
            nor,
            'Did not extract the correct number of records from the input file'
        )

    def test_file_stream_input_extract_list(self):
        """
        Tests the extract method. It checks that it parses the content of the
        file correctly by checking each of the attributes set in the class.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(self.test_file_stub)
        ext = FileInputStream.extract()

        self.assertIn('2015MNRAS.446.4239E', FileInputStream.bibcode)
        self.assertIn(
            os.path.join(self.app.conf['PROJ_HOME'], 'test.pdf'),
            FileInputStream.full_text_path
        )
        self.assertIn('MNRAS', FileInputStream.provider)

    
    def test_trim(self):
        """
        Tests that the trim normalizes the text.
        """
        # non-breakable space
        if sys.version_info > (3,):
            a = b'a\xc2\xa0b'.decode('utf8')
            b = b'a' + b'\xc2\xa0' + b'b'  # utf-8 bytecode
        else:
            a = 'a\xc2\xa0b'.decode('utf8')
            b = 'a' + b'\xc2\xa0' + 'b' #utf-8 bytecode
        c = u'a' + u'\xa0' + u'b' # unicode
        d = u'a' + chr(160) + u'b'
        # string with a large token representing table data
        e = u'a ' + ('123%5.7890' * 100) + u' b' 
        for x in (a, b, c, d, e):
            r = utils.TextCleaner(x).run(translate=False, decode=True, normalise=True, trim=True)
            self.assertEqual(r, u'a b')

    def test_get_filenames(self):
        """test code that breaks up file name strings"""

        file_string = '/proj/ads/foo'
        files = utils.get_filenames(file_string)
        self.assertEqual([file_string], files)

        file_string = '/proj/ads/foo,/proj/ads/bar'
        files = utils.get_filenames(file_string)
        self.assertEqual(['/proj/ads/foo', '/proj/ads/bar'], files)

        file_string = '/proj/ads/foo,/proj/ads/,,/bar'
        files = utils.get_filenames(file_string)
        self.assertEqual(['/proj/ads/foo', '/proj/ads/,,/bar'], files)

        file_string = '/proj/ads/foo,/proj/ads/ba,r'
        files = utils.get_filenames(file_string)
        self.assertEqual(['/proj/ads/foo', '/proj/ads/ba,r'], files)

        file_string = '/proj/ads/foo,/proj/ads/ba,r,/proj/ads/baz/,,/qu,ux'
        files = utils.get_filenames(file_string)
        self.assertEqual(['/proj/ads/foo', '/proj/ads/ba,r', '/proj/ads/baz/,,/qu,ux'], files)


if __name__ == '__main__':
    unittest.main()
