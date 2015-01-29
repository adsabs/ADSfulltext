"""
Unit Test of the check records functions for the base class, CheckIfExtract
"""

import unittest
import utils
from settings import PROJ_HOME
from lib import CheckIfExtract as check

test_input = "2015MNRAS.446.4239E\t" + PROJ_HOME + "/test/data/test.pdf\tMNRAS"
test_input_wrong = "2015MNRAS.446.4239E\t" + PROJ_HOME + "/test/data/test.pdf"
test_input_exists = "2015MNRAS.446.4239E\t" + PROJ_HOME + "/tests"
test_stub = "test\t" + PROJ_HOME + "/tests/test_unit/stub_data/te/st/test.pdf\tTEST"
test_file = 'tests/test_integration/stub_data/fulltext.links'
test_list = test_input.split("\t")


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


	def test_file_should_be_extracted(self):

	 	FileInputStream = utils.FileInputStream(test_file, stream_format='file')
	 	FileInputStream.extract()
	 	rabbitmq_input = zip(FileInputStream.bibcode, FileInputStream.full_text_path, FileInputStream.provider)
	 	FileInputStream.make_payload()

	 	payload = check.check_if_extract(rabbitmq_input, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

		self.assertEqual(payload, FileInputStream.payload)


class TestFileStreamInput(unittest.TestCase):


	def test_file_stream_input_extract_string(self):
		FileInputStream = utils.FileInputStream(test_input, stream_format="txt")
		FileInputStream.extract()

		self.assertEqual(FileInputStream.bibcode, "2015MNRAS.446.4239E")
		self.assertEqual(FileInputStream.full_text_path, "/vagrant/test/data/test.pdf")
		self.assertEqual(FileInputStream.provider, "MNRAS")


	def test_file_stream_input_wrong_style(self):
		FileInputStream = utils.FileInputStream(test_input_wrong)
		ret = FileInputStream.extract()

		self.assertEqual(FileInputStream.bibcode, "")
		self.assertEqual(FileInputStream.full_text_path, "")
		self.assertEqual(FileInputStream.provider, "")


	def test_file_stream_input_extract_file(self):

		FileInputStream = utils.FileInputStream(test_file, stream_format="file")
		ext = FileInputStream.extract()

		self.assertEqual(len(FileInputStream.bibcode), 3, "Did not extract the correct number of records from the input file")


	def test_file_stream_input_extract_list(self):

		FileInputStream = utils.FileInputStream(test_list, stream_format='list')
		ext = FileInputStream.extract()

		self.assertEqual(FileInputStream.bibcode, "2015MNRAS.446.4239E")
		self.assertEqual(FileInputStream.full_text_path, "/vagrant/test/data/test.pdf")
		self.assertEqual(FileInputStream.provider, "MNRAS")


if __name__ == '__main__':
	unittest.main()