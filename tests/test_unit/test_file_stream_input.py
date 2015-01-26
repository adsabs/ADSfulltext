"""
Unit Test of the file stream input base class, FileInputStream.
"""

import unittest
import utils
from settings import PROJ_HOME



class TestFileStreamInput(unittest.TestCase):

	def setUp(self):
		self.test_input = "2015MNRAS.446.4239E\t" + PROJ_HOME + "/test/data/test.pdf\tMNRAS"
		self.test_input_wrong = "2015MNRAS.446.4239E\t" + PROJ_HOME + "/test/data/test.pdf"
		self.test_file = "tests/test_integration/stub_data/fulltext.links"

	def test_file_stream_input_extract_string(self):
		FileInputStream = utils.FileInputStream(self.test_input, stream_format="txt")
		FileInputStream.extract()

		self.assertEqual(FileInputStream.bibcode, "2015MNRAS.446.4239E")
		self.assertEqual(FileInputStream.full_text_path, "/vagrant/test/data/test.pdf")
		self.assertEqual(FileInputStream.provider, "MNRAS")

	def test_file_stream_input_wrong_format(self):
		FileInputStream = utils.FileInputStream(self.test_input, stream_format="json")
		ret = FileInputStream.extract()

		self.assertEqual(FileInputStream.bibcode, "")
		self.assertEqual(FileInputStream.full_text_path, "")
		self.assertEqual(FileInputStream.provider, "")

	def test_file_stream_input_wrong_style(self):
		FileInputStream = utils.FileInputStream(self.test_input_wrong)
		ret = FileInputStream.extract()

		self.assertEqual(FileInputStream.bibcode, "")
		self.assertEqual(FileInputStream.full_text_path, "")
		self.assertEqual(FileInputStream.provider, "")

	# def test_file_stream_input_extract_file(self):

	# 	FileInputStream = utils.FileInputStream(self.test_file, stream_format="file")
	# 	ext = FileInputStream.extract()

	# 	self.assertEqual(len(FileInputStream.bibcode), 3, "Did not extract the correct number of records from the input file")
