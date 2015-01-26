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

	# 	FileInputStream = chk.FileInputStream(test_input)
	# 	FileInputStream.extract()
	#  	extract = chk.check_if_extract(FileInputStream)




if __name__ == '__main__':
	unittest.main()