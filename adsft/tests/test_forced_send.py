import unittest
import os
import sys

#from adsft import extraction, rules, utils
from mock import patch
from adsft import tasks, reader
from adsft.tests import test_base
from datetime import datetime
import json
from mock import patch

class TestForcedExtractor(test_base.TestGeneric):
    """
    Class for testing that a file is force send if specified by the user.
    """

    def setUp(self):
        """
        Generic setup of the test class. Makes a dictionary item that the worker
        would expect to receive from the RabbitMQ instance. Loads the relevant
        worker as well into a class attribute so it is easier to access.
        :return:
        """
        super(TestForcedExtractor, self).setUp()
        self.test_publish = os.path.join(
            self.app.conf['PROJ_HOME'],
            'tests/test_integration/stub_data/fulltext_exists_txt.links'
        )
        self.expected_paths = self.calculate_expected_folders(self.test_publish)

    def tearDown(self):
        """
        Generic tear down of the class. It removes the files and paths created
        in the test. It then calls the super class's tear down afterwards.

        :return: no return
        """

        self.clean_up_path(self.expected_paths)
        super(TestForcedExtractor, self).tearDown()

    def test_forced_send(self):
        """
        Tests that when a user specifies 'force_extract' that the full text
        is extracted regardless of its underlying reason for being or not
        being extracted.

        :return: no return
        """
        sys.path.append(self.app.conf['PROJ_HOME'])
        from run import read_links_from_file

        # User loads the list of full text files and publishes them to the
        # first queue
        records = read_links_from_file(self.test_publish, force_extract=False, force_send=True)

        self.helper_get_details(self.test_publish)
        self.assertEqual(
            len(records.bibcode), self.nor,
            'The number of records should match'
            ' the number of lines. It does not: '
            '{0} [{1}]'.format(len(records.bibcode), self.nor))

        self.assertTrue(len(records.payload) == 1)

        # Call the task to check if it should be extracted but mock the extraction task
        with patch.object(tasks.task_extract, 'delay', return_value=None) as task_extract:
            message = records.payload[0]
            tasks.task_check_if_extract(message)
            self.assertTrue(task_extract.called)
            expected = {'UPDATE': 'FORCE_TO_SEND',
                         'bibcode': 'test4',
                         'file_format': 'txt',
                         'ft_source': '{}/tests/test_unit/stub_data/test.txt'.format(self.app.conf['PROJ_HOME']),
                         #'index_date': '2017-07-07T14:39:11.271432Z',
                         'meta_path': '{}/tests/test_unit/stub_data/te/st/4/meta.json'.format(self.app.conf['PROJ_HOME']),
                         'provider': 'TEST'}
            actual = task_extract.call_args[0][0]
            self.assertTrue(set(expected).issubset(actual))
            self.assertTrue('index_date' in actual)

        with patch.object(tasks.task_output_results, 'delay', return_value=None) as task_output_results:
            with patch.object(tasks.task_identify_facilities, 'delay', return_value=None) as task_identify_facilities:
                # Now we do call the extraction task with the proper arguments
                tasks.task_extract(actual)
                self.assertTrue(task_output_results.called)

        # After the extractor, the meta writer should write all the payloads to
        # disk in the correct folders
        for path in self.expected_paths:
            meta_path = os.path.join(path, 'meta.json')

            self.assertTrue(
                os.path.exists(meta_path),
                'Meta file not created: {0}'.format(path)
            )

            if os.path.exists(meta_path):
                with open(meta_path, 'r') as meta_file:
                    meta_content = meta_file.read()
                self.assertTrue(
                    'FORCE_TO_SEND' in meta_content,
                    'meta file does not contain the right extract keyword: {0}'
                    .format(meta_content)
                )

            fulltext_path = os.path.join(path, 'fulltext.txt.gz')
            self.assertTrue(
                os.path.exists(fulltext_path),
                'Full text file not created: %s'.format(path)
            )

            if os.path.exists(fulltext_path):
                fulltext_content = reader.read_file(fulltext_path, json_format=False)
                self.assertEqual(fulltext_content, "Introduction THIS IS AN INTERESTING TITLE")




if __name__ == '__main__':
    unittest.main()
