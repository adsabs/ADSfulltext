"""
Unit Test of the check records functions for the base class, CheckIfExtract
"""

import unittest
from settings import PROJ_HOME
from lib import CheckIfExtract as chk

test_input = "2015MNRAS.446.4239E     " + PROJ_HOME + "/test/data/test.pdf     MNRAS"
test_input_wrong = "2015MNRAS.446.4239E     " + PROJ_HOME + "/test/data/test.pdf"
test_input_exists = "2015MNRAS.446.4239E     " + PROJ_HOME + "/tests"
test_stub = PROJ_HOME + "test     " + PROJ_HOME + "/tests/test_unit/te/st/test.pdf	TEST"

class TestFileStreamInput(unittest.TestCase):
	
	def test_file_stream_input_extract_string(self):
		FileInputStream = chk.FileInputStream(test_input, stream_format="txt")
		FileInputStream.extract()

		self.assertEqual(FileInputStream.bibcode, "2015MNRAS.446.4239E")
		self.assertEqual(FileInputStream.full_text_path, "/vagrant/test/data/test.pdf")
		self.assertEqual(FileInputStream.provider, "MNRAS")

	def test_file_stream_input_wrong_format(self):
		FileInputStream = chk.FileInputStream(test_input, stream_format="json")
		ret = FileInputStream.extract()

		self.assertEqual(FileInputStream.bibcode, "")
		self.assertEqual(FileInputStream.full_text_path, "")
		self.assertEqual(FileInputStream.provider, "")

	def test_file_stream_input_wrong_style(self):
		FileInputStream = chk.FileInputStream(test_input_wrong)
		ret = FileInputStream.extract()

		self.assertEqual(FileInputStream.bibcode, "")
		self.assertEqual(FileInputStream.full_text_path, "")
		self.assertEqual(FileInputStream.provider, "")

class TestCheckIfExtracted(unittest.TestCase):

	def test_file_not_extracted_before(self):

		FileInputStream = chk.FileInputStream(test_input)
		FileInputStream.extract()
		exists = chk.meta_output_exists(FileInputStream)

		self.assertEqual(exists, False)

	def test_file_extracted_before(self):

		FileInputStream = chk.FileInputStream(test_stub)
		FileInputStream.extract()
		exists = chk.meta_output_exists(FileInputStream)

		self.assertEqual(exists, True)

	# def test_file_should_be_extracted(self):
	# 	chk.extract_file()

if __name__ == '__main__':
	unittest.main()