"""
Unit Test of the check records functions for the base class, CheckIfExtract
"""

import unittest
import utils
from settings import PROJ_HOME
from lib import CheckIfExtract as check

test_input = "2015MNRAS.446.4239E     " + PROJ_HOME + "/test/data/test.pdf     MNRAS"
test_input_wrong = "2015MNRAS.446.4239E     " + PROJ_HOME + "/test/data/test.pdf"
test_input_exists = "2015MNRAS.446.4239E     " + PROJ_HOME + "/tests"
test_stub = "test	" + PROJ_HOME + "/tests/test_unit/stub_data/te/st/test.pdf	TEST"
test_file = 'tests/test_integration/stub_data/fulltext.links'


class TestCheckIfExtracted(unittest.TestCase):

	def test_file_not_extracted_before(self):

		FileInputStream = utils.FileInputStream(test_input, stream_format='txt')
		FileInputStream.extract()
		exists = check.meta_output_exists(FileInputStream, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

		self.assertEqual(exists, False)

	def test_file_extracted_before(self):

		FileInputStream = utils.FileInputStream(test_stub, stream_format='txt')
		FileInputStream.extract()

		exists = check.meta_output_exists(FileInputStream, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

		self.assertEqual(exists, True, "Could not establish that this file has been extracted before")


	# def test_file_should_be_updated_exit_if_not_file(self):
	# 	FileInputStream = utils.FileInputStream(test_stub, stream_format='txt')
	# 	FileInputStream.extract()

	# 	try:
	# 		updated = check.meta_needs_update(FileInputStream, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")
	# 	except IOError:
	# 		updated = -1

	# 	self.assertEqual(updated, -1, "It should exit if the input is not a file")


	def test_file_extract_meta(self):

		FileInputStream = utils.FileInputStream(test_stub, stream_format='txt')
		FileInputStream.extract()

		content = check.load_meta_file(FileInputStream, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

		self.assertTrue(len(content)>0, "Did not extract the meta data correctly")

	def test_file_should_be_updated_if_missing_fulltext(self):

	 	FileInputStream = utils.FileInputStream(test_stub, stream_format='txt')
	 	FileInputStream.extract()

	 	meta_content = check.load_meta_file(FileInputStream, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")
	 	new_meta_content = {}

	 	for key in meta_content.keys():	
	 		if key != 'ft_source':	new_meta_content[key] = meta_content[key] 

	 	updated = check.meta_needs_update(FileInputStream, new_meta_content, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

	 	self.assertEqual(updated, 'MISSING_FULL_TEXT', "The ft_source should need updating, not %s" % updated)


	def test_file_should_be_updated_if_content_differs_to_input(self):
 		
 		FileInputStream = utils.FileInputStream(test_stub, stream_format='txt')
	 	FileInputStream.extract()

	 	meta_content = check.load_meta_file(FileInputStream, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

	 	meta_content['ft_source'] = ''
	 	updated = check.meta_needs_update(FileInputStream, meta_content, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

	 	self.assertEqual(updated, 'DIFFERING_FULL_TEXT', "The ft_source should need updating, not %s" % updated)

	def test_file_should_be_updated_if_content_is_stale(self):

 		FileInputStream = utils.FileInputStream(test_stub, stream_format='txt')
	 	FileInputStream.extract()

	 	meta_content = check.load_meta_file(FileInputStream, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

	 	updated = check.meta_needs_update(FileInputStream, meta_content, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

	 	self.assertEqual(updated, 'STALE_CONTENT', "The file content should be stale, not %s" % updated)

	def test_file_should_not_be_updated_if_everything_is_fine(self):

	# def test_file_should_not_be_updated(self):

	# 	FileInputStream = utils.FileInputStream(test_stub, stream_format='txt')
	# 	FileInputStream.extract()

	# 	updated = check.meta_needs_update(FileInputStream, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

	# 	self.assertEqual(updated, False, "It should not need updating")


	# def test_file_should_be_extracted(self):

	# 	FileInputStream = utils.FileInputStream(test_stub, stream_format='txt')
	# 	FileInputStream.extract()

	# 	extract = check.check_if_extract()

	# 	FileInputStream = chk.FileInputStream(test_input)
	# 	FileInputStream.extract()
	#  	extract = chk.check_if_extract(FileInputStream)




if __name__ == '__main__':
	unittest.main()