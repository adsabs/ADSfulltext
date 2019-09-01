import unittest
import os
import sys

#from adsft import extraction, rules, utils
from adsft import tasks
from adsft.tests import test_base
from datetime import datetime
import json
from mock import patch

class TestExtraAcknowledgment(test_base.TestGeneric):
    """
    Class for testing that the XML extraction results in an acknowledgements
    file being made.
    """

    def setUp(self):
        """
        Generic setup of the test class. Makes a dictionary item that the worker
        would expect to receive from the RabbitMQ instance. Loads the relevant
        worker as well into a class attribute so it is easier to access.
        :return:
        """
        super(TestExtraAcknowledgment, self).setUp()
        #self.dict_item = {'ft_source': self.test_stub_xml,
                          #'file_format': 'xml',
                          #'provider': 'MNRAS'}
        #self.extractor = extraction.EXTRACTOR_FACTORY['xml'](self.dict_item)
        self.test_publish = os.path.join(
            self.app.conf['PROJ_HOME'],
            'tests/test_integration/stub_data/'
            'fulltext_xml_doc_with_acknowledgement.links'
        )
        self.expected_paths = self.calculate_expected_folders(self.test_publish)

    def tearDown(self):
        """
        Generic tear down of the class. It removes the files and paths created
        in the test. It then calls the super class's tear down afterwards.

        :return: no return
        """

        self.clean_up_path(self.expected_paths)
        super(TestExtraAcknowledgment, self).tearDown()

    def test_extra_acknowledment(self):
        """
        Submits a file to the RabbitMQ that contains a bibcode that should
        result in an acknowlegements file is created. It checks that this file
        is created and then removes all the content created by the tests.

        :return: no return
        """
        sys.path.append(self.app.conf['PROJ_HOME'])
        from run import read_links_from_file

        # User loads the list of full text files and publishes them to the
        # first queue
        records = read_links_from_file(self.test_publish, force_extract=False, force_send=False)

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
            expected = {'UPDATE': 'NOT_EXTRACTED_BEFORE',
                         'bibcode': 'test1',
                         'file_format': 'xml',
                         'ft_source': '{}/tests/test_integration/stub_data/full_test_elsevier.xml'.format(self.app.conf['PROJ_HOME']),
                         #'index_date': '2017-07-07T14:39:11.271432Z',
                         'meta_path': '{}/tests/test_unit/stub_data/te/st/1/meta.json'.format(self.app.conf['PROJ_HOME']),
                         'provider': 'Elsevier'}
            actual = task_extract.call_args[0][0]
            self.assertDictContainsSubset(expected, actual)
            self.assertTrue('index_date' in actual)

        with patch.object(tasks.task_output_results, 'delay', return_value=None) as task_output_results:
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
                    'NOT_EXTRACTED_BEFORE' in meta_content,
                    'meta file does not contain the right extract keyword: {0}'
                    .format(meta_content)
                )

            fulltext_path = os.path.join(path, 'fulltext.txt')
            self.assertTrue(
                os.path.exists(fulltext_path),
                'Full text file not created: %s'.format(path)
            )

            # unless changed, tests/test_integration/stub_data/full_test_elsevier.xml
            if os.path.exists(fulltext_path):
                with open(fulltext_path, 'r') as fulltext_file:
                    fulltext_content = fulltext_file.read()
                self.assertEqual(fulltext_content,
                                 '1 Introduction JOURNAL CONTENT Acknowledgments THANK YOU Appendix A APPENDIX TITLE APPENDIX')

            acknowledgments_path = os.path.join(path, 'acknowledgements.txt')
            self.assertTrue(
                os.path.exists(acknowledgments_path),
                'Full text file not created: %s'.format(path)
            )

            if os.path.exists(acknowledgments_path):
                with open(acknowledgments_path, 'r') as acknowledgments_file:
                    acknowledgements_content = acknowledgments_file.read()
                self.assertEqual(acknowledgements_content,
                                 "Acknowledgments THANK YOU")



if __name__ == '__main__':
    unittest.main()
