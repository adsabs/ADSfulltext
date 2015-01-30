"""
Unit Test of the check records functions for the base class, CheckIfExtract
"""

import unittest
import utils
from settings import PROJ_HOME
from lib import CheckIfExtract as check

test_file = 'tests/test_integration/stub_data/fulltext.links'
test_file_stub = 'tests/test_integration/stub_data/fulltext_stub.links'
test_file_wrong = 'tests/test_integration/stub_data/fulltext_wrong.links'
test_file_exists = 'tests/test_integration/stub_data/fulltext_exists.links'


class TestCheckIfExtracted(unittest.TestCase):


	def test_file_not_extracted_before(self):

		FileInputStream = utils.FileInputStream(test_file_stub)
		FileInputStream.extract()

		payload = FileInputStream.raw[0]

		exists = check.meta_output_exists(payload, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

		self.assertEqual(exists, False)


	def test_file_extracted_before(self):

		FileInputStream = utils.FileInputStream(test_file_exists)
		FileInputStream.extract()
		
		payload = FileInputStream.raw[0]
		
		exists = check.meta_output_exists(payload, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

		self.assertEqual(exists, True, "Could not establish that this file has been extracted before")


	def test_file_extract_meta(self):

		FileInputStream = utils.FileInputStream(test_file_exists)
		FileInputStream.extract()

		payload = FileInputStream.raw[0]

		content = check.load_meta_file(payload, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")
		

		self.assertTrue(len(content)>0, "Did not extract the meta data correctly")


	def test_file_should_be_updated_if_missing_fulltext(self):

	 	FileInputStream = utils.FileInputStream(test_file_exists)
	 	FileInputStream.extract()

	 	meta_content = check.load_meta_file(FileInputStream.raw[0], extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")
	 	new_meta_content = {}

	 	for key in meta_content.keys():	
	 		if key != 'ft_source':	new_meta_content[key] = meta_content[key] 

	 	updated = check.meta_needs_update(FileInputStream, new_meta_content, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

	 	self.assertEqual(updated, 'MISSING_FULL_TEXT', "The ft_source should need updating, not %s" % updated)



	def test_file_should_be_updated_if_content_differs_to_input(self):
 		
 		FileInputStream = utils.FileInputStream(test_file_exists)
	 	FileInputStream.extract()
	 	payload = FileInputStream.raw[0]

	 	meta_content = check.load_meta_file(payload, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

	 	meta_content['ft_source'] = ''
	 	updated = check.meta_needs_update(payload, meta_content, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

	 	self.assertEqual(updated, 'DIFFERING_FULL_TEXT', "The ft_source should need updating, not %s" % updated)


	def test_file_should_be_updated_if_content_is_stale(self):

 		FileInputStream = utils.FileInputStream(test_file_exists)
	 	FileInputStream.extract()

	 	payload = FileInputStream.raw[0]

	 	meta_content = check.load_meta_file(payload, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

	 	updated = check.meta_needs_update(payload, meta_content, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

	 	self.assertEqual(updated, 'STALE_CONTENT', "The file content should be stale, not %s" % updated)


	def test_file_should_be_extracted(self):

	 	import json
	 	FileInputStream = utils.FileInputStream(test_file)
	 	FileInputStream.extract()
	 	
	 	rabbitmq_input = []

	 	for b, f, p in zip(FileInputStream.bibcode, FileInputStream.full_text_path, FileInputStream.provider):
	 		rabbitmq_input.append({"bibcode": b, "ft_source": f, "provider": p, "UPDATE": "DIFFERING_FULL_TEXT"})

	 	payload = check.check_if_extract(FileInputStream.raw, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")
		rabbitmq_input = json.dumps(rabbitmq_input)

		self.assertEqual(payload, rabbitmq_input)


class TestFileStreamInput(unittest.TestCase):


	def test_file_stream_input_extract_file(self):

		FileInputStream = utils.FileInputStream(test_file)
		ext = FileInputStream.extract()

		self.assertEqual(len(FileInputStream.bibcode), 3, "Did not extract the correct number of records from the input file")


	def test_file_stream_input_extract_list(self):

		FileInputStream = utils.FileInputStream(test_file_stub)
		ext = FileInputStream.extract()

		self.assertIn("2015MNRAS.446.4239E", FileInputStream.bibcode)
		self.assertIn("/vagrant/test/data/test.pdf", FileInputStream.full_text_path)
		self.assertIn("MNRAS", FileInputStream.provider)


if __name__ == '__main__':
	unittest.main()