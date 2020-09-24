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
import httpretty
import pdb

class TestFullRangeFormatExtraction(test_base.TestGeneric):
    """
    Class that tests all format types that are expected to be sent to the
    RabbitMQ instance.
    """

    def setUp(self):
        """
        Generic setup of the test class. Makes a dictionary item that the worker
        would expect to receive from the RabbitMQ instance. Loads the relevant
        worker as well into a class attribute so it is easier to access.
        :return:
        """
        super(TestFullRangeFormatExtraction, self).setUp()
        #self.dict_item = {'ft_source': self.test_stub_xml,
                          #'file_format': 'xml',
                          #'provider': 'MNRAS'}
        #self.extractor = extraction.EXTRACTOR_FACTORY['xml'](self.dict_item)
        self.grobid_service = tasks.app.conf['GROBID_SERVICE']
        self.test_publish = os.path.join(
            self.app.conf['PROJ_HOME'],
            'tests/test_integration/stub_data/fulltext_range_of_formats.links'
        )
        self.expected_paths = self.calculate_expected_folders(self.test_publish)

    def tearDown(self):
        """
        Generic tear down of the class. It removes the files and paths created
        in the test. It then calls the super class's tear down afterwards.

        :return: no return
        """

        self.clean_up_path(self.expected_paths)
        super(TestFullRangeFormatExtraction, self).tearDown()

    def test_full_range_of_file_format_extraction(self):
        """
        Submits a file containing all the relevant document types to the
        RabbitMQ instance. Runs all the relevant workers, and then checks that
        content was extracted. Finally, it cleans up any files or paths created.

        :return: no return
        """
        sys.path.append(self.app.conf['PROJ_HOME'])
        from run import read_links_from_file

        if self.grobid_service is not None:
            httpretty.enable()
            expected_grobid_fulltext = "<hello/>"
            httpretty.register_uri(httpretty.POST, self.grobid_service,
                           body=expected_grobid_fulltext,
                           status=200)

        # User loads the list of full text files and publishes them to the
        # first queue
        records = read_links_from_file(self.test_publish, force_extract=False, force_send=False)

        self.helper_get_details(self.test_publish)
        self.assertEqual(
            len(records.bibcode), self.nor,
            'The number of records should match'
            ' the number of lines. It does not: '
            '{0} [{1}]'.format(len(records.bibcode), self.nor))

        self.assertTrue(len(records.payload) == 6)

        # Make the fake data to use
        if not os.path.exists(self.meta_path):
            os.makedirs(self.meta_path)

        # Call the task to check if it should be extracted but mock the extraction task
        with patch.object(tasks.task_extract, 'delay', return_value=None) as task_extract:
            extraction_arguments_set = []
            expected_update = 'NOT_EXTRACTED_BEFORE'
            for message in records.payload:
                tasks.task_check_if_extract(message)
                self.assertTrue(task_extract.called)
                actual = task_extract.call_args[0][0]
                self.assertEqual(actual['UPDATE'], expected_update,
                        'This should be %s, but is in fact: {0}'
                        .format(expected_update, actual['UPDATE']))
                extraction_arguments_set.append(actual)

        with patch.object(tasks.task_output_results, 'delay', return_value=None) as task_output_results:
            with patch.object(tasks.task_identify_facilities, 'delay', return_value=None) as task_identify_facilities:
                # Now we do call the extraction task with the proper arguments
                for arguments in extraction_arguments_set:
                    #if arguments['ft_source'].endswith('.pdf') is False:
                    tasks.task_extract(arguments)
                    self.assertTrue(task_output_results.called)

        # After the extractor, the meta writer should write all the payloads to
        # disk in the correct folders
        for i, path in enumerate(self.expected_paths):
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

            fulltext_path = os.path.join(path, 'fulltext.txt.gz')
            self.assertTrue(
                os.path.exists(fulltext_path),
                'Full text file not created: %s'.format(path)
            )

            if os.path.exists(fulltext_path):
                fulltext_content = reader.read_file(fulltext_path, json_format=False)
                expected_fulltext_content = (
                        u"Introduction THIS IS AN INTERESTING TITLE",
                        u"Introduction THIS IS AN INTERESTING TITLE",
                        u"I. INTRODUCTION INTRODUCTION GOES HERE Manual Entry TABLE I. TEXT a NOTES a TEXT\nAPPENDIX: APPENDIX TITLE GOES HERE APPENDIX CONTENT",
                        u'1 Introduction JOURNAL CONTENT Acknowledgments THANK YOU Appendix A APPENDIX TITLE APPENDIX',
                        u"No Title AA 999, 999-999 (1999) DOI: 99.9999/9999-9999:99999999 TITLE AUTHOR AFFILIATION Received 99 MONTH 1999 / Accepted 99 MONTH 1999 Abstract ABSTRACT Key words: KEYWORD INTRODUCTION SECTION Table 1: TABLE TABLE (1) COPYRIGHT",
                        #u"Introduction\nTHIS IS AN INTERESTING TITLE\n", # PDFBox
                        u"Introduction THIS IS AN INTERESTING TITLE", # pdftotext
                        )

                self.assertEqual(fulltext_content, expected_fulltext_content[i])

            grobid_fulltext_path = os.path.join(path, 'grobid_fulltext.xml')
            if os.path.exists(grobid_fulltext_path):
                with open(grobid_fulltext_path, 'r') as grobid_fulltext_file:
                    grobid_fulltext_content = grobid_fulltext_file.read()
                self.assertEqual(grobid_fulltext_content, expected_grobid_fulltext)



if __name__ == '__main__':
    unittest.main()
