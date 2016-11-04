"""
Unit tests of the project. Each function related to the workers individual tools
are tested in this suite. There is no communication. Unit Test of the check
records functions for the base class, CheckIfExtract.
"""

__author__ = 'J. Elliott'
__maintainer__ = 'J. Elliott'
__copyright__ = 'Copyright 2015'
__version__ = '1.0'
__email__ = 'ads@cfa.harvard.edu'
__status__ = 'Production'
__license__ = 'GPLv3'

import sys
import os

PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)

import unittest
import utils
import json
import re
import os
import httpretty
import math

from settings import PROJ_HOME, config, CONSTANTS, META_CONTENT
from lib import CheckIfExtract as check
from lib import StandardFileExtract as std_extract
from lib import WriteMetaFile as writer
from lib import test_base
from requests.exceptions import HTTPError

test_file = \
    os.path.join(PROJ_HOME,
                 'tests/test_integration/stub_data/fulltext.links')
test_file_stub = \
    os.path.join(PROJ_HOME,
                 'tests/test_integration/stub_data/fulltext_stub.links')
test_file_wrong = \
    os.path.join(PROJ_HOME,
                 'tests/test_integration/stub_data/fulltext_wrong.links')
test_file_exists = \
    os.path.join(PROJ_HOME,
                 'tests/test_integration/stub_data/fulltext_exists.links')
test_single_document =\
    os.path.join(PROJ_HOME,
                 'tests/test_integration/stub_data/fulltext_single_document'
                 '.links')

test_stub_xml = \
    os.path.join(PROJ_HOME,
                 'tests/test_unit/stub_data/test.xml')
test_stub_exml = \
    os.path.join(PROJ_HOME,
                 'tests/test_unit/stub_data/test_elsevier.xml')
test_stub_teixml = \
    os.path.join(PROJ_HOME,
                 'tests/test_unit/stub_data/test.astro-ph-0002105.tei.xml')
test_stub_html = \
    os.path.join(PROJ_HOME,
                 'tests/test_unit/stub_data/test.html')
test_stub_html_table = \
    os.path.join(PROJ_HOME,
                 'tests/test_unit/stub_data/test_table.html')
test_stub_text = \
    os.path.join(PROJ_HOME,
                 'tests/test_unit/stub_data/test.txt')
test_stub_ocr = \
    os.path.join(PROJ_HOME,
                 'tests/test_unit/stub_data/test.ocr')

test_functional_stub =\
    os.path.join(PROJ_HOME,
                 'tests/test_functional/stub_data/fulltext_functional_tests'
                 '.links')


class TestCheckIfExtracted(test_base.TestUnit):
    """
    Tests the CheckIfExtract worker's methods, i.e., the unit functions.
    """

    def test_file_not_extracted_before(self):
        """
        Tests the meta_output_exists function. It should find that there is not
        already a meta file that exists, which is defined in test_file_stub.

        :return: no return
        """
        FileInputStream = utils.FileInputStream(test_file_stub)
        FileInputStream.extract()

        payload = FileInputStream.raw[0]

        exists = check.meta_output_exists(
            payload,
            extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST"
        )

        self.assertEqual(exists, False)

    def test_file_extracted_before(self):
        """
        Tests the meta_output_exists function. It should find that there is
        already a meta file that exists, which is defined in test_file_exists.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(test_file_exists)
        FileInputStream.extract()

        payload = FileInputStream.raw[0]

        exists = check.meta_output_exists(
            payload,
            extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST'
        )

        self.assertEqual(
            exists,
            True,
            'Could not establish that this file has been extracted before'
        )

    def test_file_extract_meta(self):
        """
        Tests the load_meta_file function. Should load the meta file that exists
        on disk and checks that there is actually some content extracted.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(test_file_exists)
        FileInputStream.extract()

        payload = FileInputStream.raw[0]

        content = check.load_meta_file(
            payload,
            extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST'
        )

        self.assertTrue(
            len(content) > 0,
            'Did not extract the meta data correctly'
        )

    def test_file_should_be_updated_if_missing_fulltext(self):
        """
        Tests the meta_needs_update function. Loads some meta content from disk,
        and then copies everything but the full text path to a new meta content
        dictionary. The meta_needs_update function should then determine that
        there is no full text content and supply the MISSING_FULL_TEXT flag.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(test_file_exists)
        FileInputStream.extract()

        meta_content = check.load_meta_file(
            FileInputStream.raw[0],
            extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST'
        )

        new_meta_content = {}

        for key in meta_content.keys():
            if key != 'ft_source':
                new_meta_content[key] = meta_content[key]

        updated = check.meta_needs_update(
            FileInputStream,
            new_meta_content,
            extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST'
        )

        self.assertEqual(updated,
                         'MISSING_FULL_TEXT',
                         'The ft_source should need updating, not {0}'
                         .format(updated))

    def test_file_should_be_updated_if_content_differs_to_input(self):
        """
        Tests the meta_needs_update function. Loads some meta content from disk,
        and then modifies the full text path to be different. The meta_needs_
        update function should then determine that the full text content differs
        and supply the DIFFERING_FULL_TEXT flag.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(test_file_exists)
        FileInputStream.extract()
        payload = FileInputStream.raw[0]

        meta_content = check.load_meta_file(
            payload,
            extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST'
        )

        meta_content['ft_source'] = ''

        updated = check.meta_needs_update(
            payload,
            meta_content,
            extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST'
        )

        self.assertEqual(updated,
                         'DIFFERING_FULL_TEXT',
                         'The ft_source should need updating, not {0}'
                         .format(updated)
        )

    def test_file_should_be_updated_if_content_is_stale(self):
        """
        Tests the meta_needs_update function. Loads meta data from the disk, and
        finds the full text path. Opens the full text file and writes some fresh
        content so that it is more new than the meta data file. This will result
        in the meta_needs_update supplying the STALE_CONTENT flag.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(test_file_exists)
        FileInputStream.extract()
        FileInputStream.make_payload()

        # Ensure the PDF more new than the meta.json
        payload = FileInputStream.raw[0]
        with open(payload[CONSTANTS['FILE_SOURCE']], 'w') as not_stale:
            not_stale.write('PDF')

        # Not a nicer way to do this without cleaning up some tests
        meta_content = check.load_meta_file(
            payload,
            extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST'
        )

        meta_content[CONSTANTS['FILE_SOURCE']] \
            = os.path.join(PROJ_HOME, meta_content[CONSTANTS['FILE_SOURCE']])

        updated = check.meta_needs_update(
            payload,
            meta_content,
            extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST"
        )

        self.assertEqual(updated,
                         'STALE_CONTENT',
                         'The file content should be stale, not {0} ({1}\n{2})'
                         .format(updated, payload, meta_content)
                         )

    def test_file_should_be_extracted(self):
        """
        Tests the check_if_extract function. Calculates how many references
        there are to PDFs, and the remainder are 'Standard files', e.g., XML,
        HTTP, HTML, etc. From this payload, it runs check_if_extract and ensures
        that all of the outputs contain an expected UPDATE flag, and that there
        are the correct number of PDFs in the PDF queue, and the right number of
        StandardFiles in the StandardFiles queue.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(test_file)
        FileInputStream.extract()

        with open(test_file, 'r') as in_f:
            text = in_f.read()
        pdf_re = re.compile('pdf')
        pdf_number = len(pdf_re.findall(text))
        standard_number = \
            len([i for i in text.split('\n') if i != '']) - pdf_number

        payload = check.check_if_extract(
            FileInputStream.raw, extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST'

        )
        pdf_payload = json.loads(payload['PDF'])
        standard_payload = json.loads(payload['Standard'])

        if pdf_payload:

            pdf_compare = [
                content for content in json.loads(payload['PDF'])
                if content['UPDATE']
                in [u'STALE_CONTENT',
                    u'DIFFERING_FULL_TEXT',
                    u'MISSING_FULL_TEXT"'
                    u'NOT_EXTRACTED_BEFORE']
            ]

        else:
            pdf_compare = []

        if standard_payload:

            standard_compare = [
                content for content in json.loads(payload['Standard'])
                if content['UPDATE']
                in [u'STALE_CONTENT',
                    u'DIFFERING_FULL_TEXT',
                    u'MISSING_FULL_TEXT',
                    u'NOT_EXTRACTED_BEFORE']
            ]

        else:
            standard_compare = []

        self.assertTrue(len(pdf_compare) == pdf_number, pdf_number)
        self.assertTrue(len(standard_compare) == standard_number)

    def test_output_dictionary_contains_everything_we_need(self):
        """
        Tests the check_if_extract function. Runs the function on a stub file
        that contains one document and then ensures that the output dictionary
        contains all the expected meta data. It also checks that the correct
        file format has been associated to it.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(test_single_document)
        FileInputStream.extract()

        payload = check.check_if_extract(
            FileInputStream.raw, extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST'
        )

        expected_content = [CONSTANTS['FILE_SOURCE'], CONSTANTS['BIBCODE'],
                            CONSTANTS['PROVIDER'], CONSTANTS['FORMAT'],
                            CONSTANTS['UPDATE'], CONSTANTS['META_PATH'],
                            CONSTANTS['TIME_STAMP']]
        expected_content = [unicode(i) for i in expected_content]
        expected_content.sort()

        actual_content = json.loads(payload['Standard'])[0].keys()
        actual_format = json.loads(payload['Standard'])[0][CONSTANTS['FORMAT']]

        actual_content.sort()
        self.assertListEqual(actual_content, expected_content)
        self.assertEqual(actual_format, 'txt')

    def test_that_no_payload_gets_sent_if_there_is_no_content(self):
        """
        Tests check_if_extract function. The stub data contains no PDF files.
        This means there should be nothing inside the PDF list returned within
        the payload. If there is, there is a problem.

        :return: no return
        """
        FileInputStream = utils.FileInputStream(test_single_document)
        FileInputStream.extract()

        payload = check.check_if_extract(
            FileInputStream.raw, extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST'
        )

        self.assertFalse(json.loads(payload['PDF']))
        self.assertTrue(len(json.loads(payload['Standard'])) != 0)

    def test_that_file_should_be_updated_if_forced(self):
        """
        If the dictionary contains a force value in the update keyword, then
        the worker should pass on the content regardless of whether it passes
        any other checks
        :return: no return
        """

        FileInputStream_true = utils.FileInputStream(test_file_exists)
        FileInputStream_true.extract(force_extract=True)

        FileInputStream_false = utils.FileInputStream(test_file_exists)
        FileInputStream_false.extract(force_extract=False)

        payload_true = check.check_if_extract(
            FileInputStream_true.raw,
            extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST'
        )
        first_doc_true = json.loads(payload_true['PDF'])[0]

        payload_false = check.check_if_extract(
            FileInputStream_false.raw,
            extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST'
        )
        first_doc_false = json.loads(payload_true['PDF'])[0]


        self.assertTrue(first_doc_true['UPDATE'],
                        'FORCE_TO_EXTRACT')
        self.assertTrue(len(json.loads(payload_false['PDF'])) != 0)

        self.assertTrue(first_doc_false['UPDATE'],
                        'DIFFERING_FULL_TEXT')
        self.assertTrue(len(json.loads(payload_false['PDF'])) != 0)


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

        FileInputStream = utils.FileInputStream(test_file)
        FileInputStream.extract()

        with open(test_file, 'r') as f:
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

        FileInputStream = utils.FileInputStream(test_file_stub)
        ext = FileInputStream.extract()

        self.assertIn('2015MNRAS.446.4239E', FileInputStream.bibcode)
        self.assertIn(
            os.path.join(PROJ_HOME, 'test.pdf'),
            FileInputStream.full_text_path
        )
        self.assertIn('MNRAS', FileInputStream.provider)

    def test_split_payload_into_packet_sizes(self):
        """
        Tests the make_payload method. It checks that when the packet size is
        given by the user, that the ones returned by the method match the
        number specified by the user.

        :return: no return
        """
        FileInputStream = utils.FileInputStream(test_functional_stub)
        FileInputStream.extract()
        FileInputStream.make_payload(packet_size=10)

        num_packets = int(math.ceil(len(FileInputStream.raw) / 10.0))

        self.assertTrue(
            len(FileInputStream.payload) == num_packets,
            'Found {0:d} packets'.format(num_packets)
        )


class TestXMLExtractor(unittest.TestCase):
    """
    Checks the basic functionality of the XML extractor. The content that is to
    be extracted is defined within a dictionary inside settings.py. If this is
    modified, these tests should first be changed to reflect the needed updates.
    """

    def setUp(self):
        """
        Generic setup of the test class. Makes a dictionary item that the worker
        would expect to receive from the RabbitMQ instance. Loads the relevant
        worker as well into a class attribute so it is easier to access.
        :return:
        """
        self.dict_item = {CONSTANTS['FILE_SOURCE']: test_stub_xml,
                          CONSTANTS['FORMAT']: 'xml',
                          CONSTANTS['PROVIDER']: 'MNRAS'}
        self.extractor = std_extract.EXTRACTOR_FACTORY['xml'](self.dict_item)

    def test_that_we_can_open_an_xml_file(self):
        """
        Tests the open_xml method. Checks that it opens and reads the XML file
        correctly by comparing with the expected content of the file.

        :return: no return
        """
        full_text_content = self.extractor.open_xml()

        self.assertIn(
            '<journal-title>JOURNAL TITLE</journal-title>',
            full_text_content
        )

    def test_that_we_can_parse_the_xml_content(self):
        """
        Tests the parse_xml method. Checks that the parsed content allows access
        to the XML marked-up content, and that the content extracted matches
        what is expected.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()
        content = self.extractor.parse_xml()
        journal_title = content.xpath('//journal-title')[0].text_content()

        self.assertEqual(journal_title, 'JOURNAL TITLE')

    def test_that_we_can_extract_using_settings_template(self):
        """
        Tests the extract_multi_content method. This checks that all the meta
        data extracted is what we expect. The expected meta data to be extracted
        is defined in settings.py by the user.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()
        parsed_xml = self.extractor.parse_xml()
        content = self.extractor.extract_multi_content()

        self.assertEqual(META_CONTENT['xml'].keys(), content.keys())

    def test_that_we_can_extract_all_content_from_payload_input(self):
        """
        Tests the extract_content method. This checks that all of the XML meta
        data defined in settings.py is extracted from the stub XML data.

        :return: no return
        """

        file_path = '{0}/{1}'.format(config['FULLTEXT_EXTRACT_PATH'],
                                     test_stub_xml)
        pay_load = [self.dict_item]

        content = json.loads(std_extract.extract_content(pay_load))

        self.assertTrue(
            set(META_CONTENT['xml'].keys()).issubset(content[0].keys())
        )

    def test_that_the_correct_extraction_is_used_for_the_datatype(self):
        """
        Ensure that the defined data type in the settings.py dictionary loads
        the correct method for extraction

        :return: no return
        """

        extract_string = self.extractor.data_factory['string']
        extract_list = self.extractor.data_factory['list']

        self.assertTrue(
            extract_string.func_name == 'extract_string',
        )

        self.assertTrue(
            extract_list.func_name == 'extract_list',
        )

    def test_that_we_can_extract_a_list_of_datasets(self):
        """
        Within an XML document there may exist more than one dataset. To
        ensure that they are all extracted, we should check that this works
        otherwise there will be missing content

        :return: no return
        """

        self.dict_item[CONSTANTS['BIBCODE']] = 'test'
        full_text_content = self.extractor.open_xml()
        parsed_xml = self.extractor.parse_xml()
        content = self.extractor.extract_multi_content()

        full_text = content[CONSTANTS['FULL_TEXT']]
        acknowledgements = content[CONSTANTS['ACKNOWLEDGEMENTS']]
        data_set = content[CONSTANTS['DATASET']]
        data_set_length = len(data_set)

        self.assertIs(unicode, type(acknowledgements))

        self.assertIs(unicode, type(full_text))
        expected_full_text = 'INTRODUCTION'
        self.assertTrue(
            expected_full_text in full_text,
            'Full text is wrong: {0} [expected: {1}, data: {2}]'
            .format(full_text,
                    expected_full_text,
                    full_text)
        )

        self.assertIs(list, type(data_set))
        expected_dataset = 2
        self.assertTrue(
            data_set_length == expected_dataset,
            'Number of datasets is wrong: {0} [expected: {1}, data: {2}]'
            .format(data_set_length,
                    expected_dataset,
                    data_set)
        )


class TestTEIXMLExtractor(unittest.TestCase):
    """
    Checks the basic functionality of the TEI XML extractor (content generated by Grobid).
    """

    def setUp(self):
        """
        Generic setup of the test class. Makes a dictionary item that the worker
        would expect to receive from the RabbitMQ instance. Loads the relevant
        worker as well into a class attribute so it is easier to access.
        :return:
        """
        self.dict_item = {CONSTANTS['FILE_SOURCE']: test_stub_teixml,
                          CONSTANTS['FORMAT']: 'teixml',
                          CONSTANTS['BIBCODE']: 'TEST',
                          CONSTANTS['PROVIDER']: 'A&A'}
        self.extractor = std_extract.EXTRACTOR_FACTORY['teixml'](self.dict_item)
        self.maxDiff = None

    def test_that_we_can_open_an_xml_file(self):
        """
        Tests the open_xml method. Checks that it opens and reads the XML file
        correctly by comparing with the expected content of the file.

        :return: no return
        """
        full_text_content = self.extractor.open_xml()

        self.assertIn(
            '<title level="a" type="main">ASTRONOMY AND ASTROPHYSICS The NASA Astrophysics Data System: Architecture</title>',
            full_text_content
        )

    def test_that_we_can_parse_the_xml_content(self):
        """
        Tests the parse_xml method. Checks that the parsed content allows access
        to the XML marked-up content, and that the content extracted matches
        what is expected.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()
        content = self.extractor.parse_xml()
        journal_title = content.xpath('//title')[0].text_content()

        self.assertEqual(journal_title, 'ASTRONOMY AND ASTROPHYSICS The NASA Astrophysics Data System: Architecture')

    def test_that_we_can_extract_using_settings_template(self):
        """
        Tests the extract_multi_content method. This checks that all the meta
        data extracted is what we expect. The expected meta data to be extracted
        is defined in settings.py by the user.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()
        parsed_xml = self.extractor.parse_xml()
        content = self.extractor.extract_multi_content()

        self.assertEqual(META_CONTENT['teixml'].keys(), content.keys())

    def test_that_we_can_extract_all_content_from_payload_input(self):
        """
        Tests the extract_content method. This checks that all of the XML meta
        data defined in settings.py is extracted from the stub XML data.

        :return: no return
        """

        pay_load = [self.dict_item]

        content = json.loads(std_extract.extract_content(pay_load))

        self.assertTrue(
            set(META_CONTENT['teixml'].keys()).issubset(content[0].keys())
        )

    def test_that_we_can_extract_acknowledgments(self):
        """
        
        """
        ack = u" Acknowledgements. The usefulness of a bibliographic service is only as good as the quality and quantity of the data it contains . The ADS project has been lucky in benefitting from the skills and dedication of several people who have significantly contributed to the creation and management of the underlying datasets. In particular, we would like to acknowledge the work of Elizabeth Bohlen, Donna Thompson, Markus Demleitner, and Joyce Watson. Funding for this project has been provided by NASA under grant NCC5-189. "
        
        full_text_content = self.extractor.open_xml()
        parsed_xml = self.extractor.parse_xml()
        content = self.extractor.extract_multi_content()

        self.assertEqual(content['acknowledgements'], ack)


class TestXMLElsevierExtractor(unittest.TestCase):
    """
    Checks the basic functionality of the Elsevier XML extractor.
    The content that is to be extracted is defined within a dictionary inside
    settings.py. This does inherit from the normal XML extractor, but has
    different requirements for extraction XPATHs due to the name spaces
    used within the XML.
    """

    def setUp(self):
        """
        Generic setup of the test class. Makes a dictionary item that the worker
        would expect to receive from the RabbitMQ instance. Loads the relevant
        worker as well into a class attribute so it is easier to access.
        :return:
        """

        self.dict_item = {CONSTANTS["FILE_SOURCE"]: test_stub_exml,
                          CONSTANTS['BIBCODE']:  'TEST'}
        self.extractor = \
            std_extract.EXTRACTOR_FACTORY['elsevier'](self.dict_item)

    def test_that_we_can_open_an_xml_file(self):
        """
        Tests the open_xml method. Checks that it opens and reads the XML file
        correctly by comparing with the expected content of the file. This is
        different to opening a normal XML file.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()
        self.assertIn('JOURNAL CONTENT', full_text_content)

    def test_that_we_can_parse_the_xml_content(self):
        """
        Tests the parse_xml method. Checks that the parsed content allows access
        to the XML marked-up content, and that the content extracted matches
        what is expected.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()
        content = self.extractor.parse_xml()
        journal_title = \
            content.xpath('//*[local-name()=\'title\']')[0].text_content()
        self.assertIn('JOURNAL TITLE', journal_title)

    def test_that_we_can_extract_using_settings_template(self):
        """
        Tests the extract_multi_content method. This checks that all the meta
        data keywords extracted are the same as those expected. The expected
        meta data to be extracted is defined in settings.py by the user.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()
        parsed_xml = self.extractor.parse_xml()
        content = self.extractor.extract_multi_content()

        self.assertItemsEqual(['fulltext', 'acknowledgements', 'dataset'],
                              content.keys(),
                              content.keys())

        self.assertIn('JOURNAL CONTENT', content['fulltext'])

    def test_that_the_correct_extraction_is_used_for_the_datatype(self):
        """
        Ensure that the defined data type in the settings.py dictionary loads
        the correct method for extraction

        :return: no return
        """

        extract_string = self.extractor.data_factory['string']
        extract_list = self.extractor.data_factory['list']

        self.assertTrue(
            extract_string.func_name == 'extract_string',
        )

        self.assertTrue(
            extract_list.func_name == 'extract_list',
        )

    def test_that_we_can_extract_a_list_of_datasets(self):
        """
        Within an XML document there may exist more than one dataset. To
        ensure that they are all extracted, we should check that this works
        otherwise there will be missing content

        :return: no return
        """

        self.dict_item[CONSTANTS['BIBCODE']] = 'test'
        full_text_content = self.extractor.open_xml()
        parsed_xml = self.extractor.parse_xml()
        content = self.extractor.extract_multi_content()

        full_text = content[CONSTANTS['FULL_TEXT']]
        acknowledgements = content[CONSTANTS['ACKNOWLEDGEMENTS']]
        data_set = content[CONSTANTS['DATASET']]
        data_set_length = len(data_set)

        self.assertIs(unicode, type(acknowledgements))

        self.assertIs(unicode, type(full_text))
        expected_full_text = 'CONTENT'
        self.assertTrue(
            expected_full_text in full_text,
            'Full text is wrong: {0} [expected: {1}, data: {2}]'
            .format(full_text,
                    expected_full_text,
                    full_text)
        )

        self.assertIs(list, type(data_set))
        expected_dataset = 2
        self.assertTrue(
            data_set_length == expected_dataset,
            'Number of datasets is wrong: {0} [expected: {1}, data: {2}]'
            .format(data_set_length,
                    expected_dataset,
                    data_set)
        )


class TestHTMLExtractor(unittest.TestCase):
    """
    Tests class to ensure the methods for opening and extracting content from
    HTML files works correctly.
    """

    def setUp(self):
        """
        Generic setup of the test class. Makes a dictionary item that the worker
        would expect to receive from the RabbitMQ instance. Loads the relevant
        worker as well into a class attribute so it is easier to access.

        :return: no return
        """

        self.dict_item = {
            CONSTANTS['FILE_SOURCE']: '{0},{1}'.format(test_stub_html,
                                                       test_stub_html_table),
            CONSTANTS['BIBCODE']: 'TEST'
        }
        self.extractor = std_extract.EXTRACTOR_FACTORY['html'](self.dict_item)

    def test_that_we_can_open_an_html_file(self):
        """
        Tests the open_html method. Checks the content loaded matches what is
        inside the file.

        :return: no return
        """

        full_text_content = self.extractor.open_html()
        self.assertIn('TITLE', full_text_content)

    def test_can_parse_an_html_file(self):
        """
        Tests the parse_html method. Checks that the HTML is parsed correctly,
        and that it allows relevant content to be extracted in the way we expect
        it to be.

        :return: no return
        """

        raw_html = self.extractor.open_html()
        parsed_html = self.extractor.parse_html()
        header = parsed_html.xpath('//h2')[0].text
        self.assertIn('TITLE', header, PROJ_HOME)

    def test_that_we_can_extract_table_contents_correctly(self):
        """
        Tests the collate_tables method. This checks that the tables linked
        inside the HTML file are found and aggregated into a dictionary, where
        each entry in the dictionary has the table name as the keyword and the
        table content as the value. This just ensures they exist and that they
        can be searched as expect.

        :return: no return
        """

        raw_html = self.extractor.open_html()
        parsed_html = self.extractor.parse_html()
        table_content = self.extractor.collate_tables()

        for key in table_content.keys():
            self.assertTrue(table_content[key].xpath('//table'))
            self.assertTrue(self.extractor.parsed_html.xpath('//h2'))

    def test_that_we_can_extract_using_settings_template(self):
        """
        Tests the extract_mutli_content. This checks that the full text that was
        extracted from the HTML document includes the content of the HTML tables
        that are linked from within the parent HTML document.

        :return: no return
        """

        content = self.extractor.extract_multi_content()

        self.assertEqual(content.keys(), ['fulltext'])
        self.assertIn(
            'ONLY IN TABLE',
            content['fulltext'],
            'Table is not in the fulltext: {0}'.format(content['fulltext'])
        )


class TestOCRandTXTExtractor(unittest.TestCase):
    """
    Class that test the methods of loading and extracting full text content
    from text and optical character recognition files.
    """

    def setUp(self):
        """
        Generic setup of the test class. Makes a dictionary item that the worker
        would expect to receive from the RabbitMQ instance. Loads the relevant
        worker as well into a class attribute so it is easier to access.

        :return: no return
        """

        self.dict_item = {CONSTANTS['FILE_SOURCE']: test_stub_text,
                          CONSTANTS['BIBCODE']: 'TEST'}
        self.dict_item_ocr = {CONSTANTS['FILE_SOURCE']: test_stub_ocr,
                          CONSTANTS['BIBCODE']: 'TEST'}

        self.extractor = std_extract.EXTRACTOR_FACTORY['txt'](self.dict_item)

        self.TC = utils.TextCleaner(text='')

    def test_open_txt_file(self):
        """
        Tests the open_text method. Checks that the content loaded matches what
        is in the file.

        :return: no return
        """

        raw_text = self.extractor.open_text()
        self.assertIn('Introduction', raw_text)

    def test_parse_txt_file(self):
        """
        Tests the parse_text method. Checks that the text is parsed correctly,
        specifically, it should be decoded, translated, and normalised, so it
        should not contain certain escape characters. This checks it does not
        have strange escape characters. This is for a 'txt' file.

        :return: no return
        """

        raw_text = self.extractor.open_text()
        parsed_text = self.extractor.parse_text(translate=True, decode=True)
        self.assertIn('Introduction', parsed_text)
        self.assertNotIn("\x00", parsed_text)

    def test_parse_ocr_file(self):
        """
        Tests the parse_text method. Checks that the text is parsed correctly,
        specifically, it should be decoded, translated, and normalised, so it
        should not contain certain escape characters. This checks it does not
        have strange escape characters. This is for a 'ocr' file.

        :return: no return
        """

        self.extractor.dict_item = self.dict_item_ocr
        raw_text = self.extractor.open_text()
        parsed_text = self.extractor.parse_text(translate=True, decode=True)
        self.assertIn('introduction', parsed_text.lower())
        self.assertIn('THIS IS AN INTERESTING TITLE', parsed_text)
        self.assertNotIn("\x00", parsed_text)

    def test_ASCII_parsing(self):
        """
        Tests the parse_text method. Checks that escape characters are removed
        as expected for ASCII characters.

        :return: no return
        """

        self.extractor.raw_text \
            = 'Tab\t CarriageReturn\r New line\n Random Escape characters:' \
              + chr(1) + chr(4) + chr(8)

        expected_out_string = re.sub(
            '\s+',
            ' ',
            'Tab\t CarriageReturn\r New line\n Random Escape characters:   '
        )

        new_instring = self.extractor.parse_text(translate=True, decode=True)

        self.assertEqual(new_instring, expected_out_string)

    def test_Unicode_parsing(self):
        """
        Tests the parse_text method. Checks that escape characters are removed
        as expected for unicode characters.

        :return: no return
        """

        self.extractor.raw_text = \
            u'Tab\t CarriageReturn\r New line\n Random Escape characters:' \
            + u'\u0000'

        expected_out_string = re.sub(
            '\s+',
            ' ',
            u'Tab\t CarriageReturn\r New line\n Random Escape characters:'
        )

        new_instring = self.extractor.parse_text(translate=True, decode=True)

        self.assertEqual(new_instring, expected_out_string)

    def test_ASCII_translation_map_works(self):
        """
        Tests the ASCII translation maps from the utils.py module. Ensures that
        escape characters are removed from the ASCII encoded string.

        :return: no return
        """

        instring = \
            'Tab\t CarriageReturn\r New line\n Random Escape characters:'\
            + chr(1) + chr(4) + chr(8)

        expected_out_string = \
            'Tab\t CarriageReturn\r New line\n Random Escape characters:   '

        new_instring = instring.translate(self.TC.ASCII_translation_map)

        self.assertEqual(new_instring, expected_out_string)

    def test_Unicode_translation_map_works(self):
        """
        Tests the unicode translation maps from the utils.py module. Ensures
        that escape characters are removed from the ASCII encoded string.

        :return: no return
        """

        instring = \
            u'Tab\t CarriageReturn\r New line\n Random Escape characters:' \
            + u'\u0000'

        expected_out_string = \
            u'Tab\t CarriageReturn New line\n Random Escape characters:'

        new_instring = instring.translate(self.TC.Unicode_translation_map)

        self.assertEqual(new_instring, expected_out_string)

    def test_extract_multi_content_on_text_data(self):
        """
        Tests the extract_multi_content method. Checks that the full text
        extracted matches what we expect it should extract.

        :return: no return
        """

        content = self.extractor.extract_multi_content()
        self.assertIn('introduction', content['fulltext'].lower())


class TestHTTPExtractor(unittest.TestCase):
    """
    Class that tests the methods used to extract full text content from HTTP
    sources behaves as expected.
    """

    def setUp(self):
        """
        Generic setup of the test class. Makes a dictionary item that the worker
        would expect to receive from the RabbitMQ instance. Loads the relevant
        worker as well into a class attribute so it is easier to access.

        :return: no return
        """

        self.dict_item = {CONSTANTS['FILE_SOURCE']: 'http://fake/http/address',
                          CONSTANTS['BIBCODE']: 'TEST'}

        self.extractor = std_extract.EXTRACTOR_FACTORY['http'](self.dict_item)

        self.body_content = 'Full text extract'

    def tearDown(self):
        """
        Generic teardown of the test class. It closes down all the instances of
        HTTPretty that is used to mock HTTP responses.

        :return: no return
        """

        # disable afterwards, so that you will have no problems in code that
        # uses that socket module
        httpretty.disable()
        # reset HTTPretty state (clean up registered urls and request history)
        httpretty.reset()

    @httpretty.activate
    def test_http_can_be_open(self):
        """
        Tests the open_http method. Checks that the HTTP content is loaded
        correctly.

        :return: no return
        """
        httpretty.register_uri(httpretty.GET,
                               self.dict_item[CONSTANTS['FILE_SOURCE']],
                               body=self.body_content)

        response = self.extractor.open_http()

        self.assertEqual(
            response,
            self.body_content,
            'Expected response: {0}\n but got: {1}'
                .format(self.body_content, response)
        )

    @httpretty.activate
    def test_http_response_not_200(self):
        """
        Tests the open_http method. Checks that an HTTPError is thrown if it
        receives a response from the server that is not equal to 200.

        :return: no return
        """

        httpretty.register_uri(httpretty.GET,
                               self.dict_item[CONSTANTS['FILE_SOURCE']],
                               body=self.body_content,
                               status=304)

        self.assertRaises(HTTPError, self.extractor.open_http)

    @httpretty.activate
    def test_http_parses(self):
        """
        Tests the parse_http method. Checks that the content received from the
        server is parsed as we expect it to be. The result is compared to the
        expected output.

        :return: no return
        """

        httpretty.register_uri(httpretty.GET,
                               self.dict_item[CONSTANTS['FILE_SOURCE']],
                               body=self.body_content,
                               status=200)

        self.extractor.open_http()
        parsed_content = self.extractor.parse_http()

        self.assertEqual(parsed_content, self.body_content)

    @httpretty.activate
    def test_http_multi_content(self):
        """
        Tests the extract_multi_content method. Checks that the full text
        content is extracted from the HTTP resource correctly, by comparin to
        what we expect the content to be.

        :return: no return
        """

        httpretty.register_uri(httpretty.GET,
                               self.dict_item[CONSTANTS['FILE_SOURCE']],
                               body=self.body_content,
                               status=200)

        content = self.extractor.extract_multi_content()

        self.assertEqual(content[CONSTANTS['FULL_TEXT']], self.body_content)


class TestWriteMetaFileWorker(unittest.TestCase):
    """
    Class that tests the methods used to write meta files and the full text
    content to disk, and pass on to other relevant RabbitMQ queues.
    """

    def setUp(self):
        """
        Generic setup of the test class. Makes a dictionary item that the worker
        would expect to receive from the RabbitMQ instance. Loads the relevant
        worker as well into a class attribute so it is easier to access.

        :return: no return
        """

        self.dict_item = {
            CONSTANTS['META_PATH']: os.path.join(
                PROJ_HOME, 'tests/test_unit/stub_data/te/st/1/meta.json'
            ),
            CONSTANTS['FULL_TEXT']: 'hehehe I am the full text',
            CONSTANTS['FORMAT']: 'xml',
            CONSTANTS['FILE_SOURCE']: '/vagrant/source.txt',
            CONSTANTS['BIBCODE']: 'MNRAS2014',
            CONSTANTS['PROVIDER']: 'MNRAS',
            CONSTANTS['UPDATE']: 'MISSING_FULL_TEXT'
        }

        self.meta_file = self.dict_item[CONSTANTS['META_PATH']]

        self.bibcode_pair_tree = \
            self.dict_item[CONSTANTS['META_PATH']].replace('meta.json', '')

        self.full_text_file = self.bibcode_pair_tree + 'fulltext.txt'

        self.acknowledgement_file = \
            self.bibcode_pair_tree + 'acknowledgements.txt'

    def tearDown(self):
        """
        Generic tear down of the test class. It deletes the meta.json file, the
        full text file, and the root directory that contains these files.

        :return: no return
        """
        try:
            os.remove(self.meta_file)
        except OSError:
            pass

        try:
            os.remove(self.full_text_file)
        except OSError:
            pass

        try:
            os.rmdir(self.bibcode_pair_tree)
        except OSError:
            pass

    def test_loads_the_content_correctly_and_makes_folders(self):
        """
        Tests the write_content method. Checks that the folder to contain the
        full text and meta data is created.

        :return: no return
        """

        content = writer.write_content(self.dict_item)

        self.assertTrue(os.path.exists(self.bibcode_pair_tree),
                        msg=os.path.exists(self.bibcode_pair_tree))

    def test_loads_the_content_correctly_and_makes_meta_file(self):
        """
        Tests the write_content method. Checks that the meta_file is created and
        is saved to disk.

        :return: no return
        """

        content = writer.write_content(self.dict_item)

        self.assertTrue(os.path.exists(self.meta_file),
                        msg=os.path.exists(self.meta_file))

    def test_loads_the_content_correctly_and_makes_full_text_file(self):
        """
        Tests the write_content method. Checks that the full text file is
        created and saved to disk.

        :return: no return
        """

        content = writer.write_content(self.dict_item)

        self.assertTrue(os.path.exists(self.full_text_file),
                        msg=os.path.exists(self.full_text_file))

    def test_pipeline_extract_content_extracts_fulltext_correctly(self):
        """
        Tests the extract_content method. Checks that the full text written to
        disk matches the ful text that we expect to be written to disk.

        N. B.
        Do not let the name extract_content portray anything. It is simply to
        keep the same naming convention as the other workers. extract_content
        is the main method the worker will run.

        :return: no return
        """

        self.dict_item[CONSTANTS['FORMAT']] = 'txt'
        pipeline_payload = [self.dict_item]

        return_payload = writer.extract_content(pipeline_payload)

        self.assertTrue(return_payload, 1)

        full_text = ''
        with open(
                self.dict_item[CONSTANTS['META_PATH']]
                        .replace('meta.json', 'fulltext.txt'), 'r'
        ) as full_text_file:

            full_text = full_text_file.read()

        self.assertEqual(self.dict_item[CONSTANTS['FULL_TEXT']], full_text)

    def test_pipeline_extract_content_extracts_meta_text_correctly(self):
        """
        Tests the extract_content method. Checks that the meta.json file written
        to disk contains the content that we expect to be there.

        N. B.
        Do not let the name extract_content portray anything. It is simply to
        keep the same naming convention as the other workers. extract_content
        is the main method the worker will run.

        :return: no return
        """

        self.dict_item[CONSTANTS['FORMAT']] = 'txt'
        pipeline_payload = [self.dict_item]

        return_payload = writer.extract_content(pipeline_payload)

        self.assertTrue(return_payload, 1)

        meta_dict = {}
        with open(self.dict_item[CONSTANTS['META_PATH']], 'r') as meta_file:
            meta_dict = json.load(meta_file)

        self.assertEqual(
            self.dict_item[CONSTANTS['FILE_SOURCE']],
            meta_dict[CONSTANTS['FILE_SOURCE']]
        )
        self.assertEqual(
            self.dict_item[CONSTANTS['BIBCODE']],
            meta_dict[CONSTANTS['BIBCODE']]
        )
        self.assertEqual(
            self.dict_item[CONSTANTS['PROVIDER']],
            meta_dict[CONSTANTS['PROVIDER']]
        )
        self.assertEqual(
            self.dict_item[CONSTANTS['UPDATE']],
            meta_dict[CONSTANTS['UPDATE']]
        )

    def pipeline_extract(self, format_):
        """
        Helper function that writes a meta.json and checks that the content on
        disk matches what we expect to be there.

        N. B.
        Do not let the name extract_content portray anything. It is simply to
        keep the same naming convention as the other workers. extract_content
        is the main method the worker will run.

        :param format_: file format to be in the meta.json
        :return: no return
        """

        self.dict_item[CONSTANTS['FORMAT']] = format_
        pipeline_payload = [self.dict_item]

        return_payload = writer.extract_content(pipeline_payload)

        self.assertTrue(return_payload == '["MNRAS2014"]')

        meta_dict = {}
        with open(self.dict_item[CONSTANTS['META_PATH']], 'r') as meta_file:
            meta_dict = json.load(meta_file)

        self.assertEqual(
            self.dict_item[CONSTANTS['FILE_SOURCE']],
            meta_dict[CONSTANTS['FILE_SOURCE']]
        )
        self.assertEqual(
            self.dict_item[CONSTANTS['BIBCODE']],
            meta_dict[CONSTANTS['BIBCODE']]
        )
        self.assertEqual(
            self.dict_item[CONSTANTS['PROVIDER']],
            meta_dict[CONSTANTS['PROVIDER']]
        )
        self.assertEqual(
            self.dict_item[CONSTANTS['UPDATE']],
            meta_dict[CONSTANTS['UPDATE']]
        )

    def test_pipeline_extract_works_for_all_formats(self):
        """
        Tests the extract_content method. Runs the extract_content method on all
        the possible types of extensions to ensure that no strange behaviour
        occurs.

        :return: no return
        """

        for format_ in ['txt', 'xml', 'xmlelsevier', 'ocr', 'html', 'http']:
            try:
                self.pipeline_extract(format_)
            except Exception:
                raise Exception

    def test_acknowledgements_file_is_created(self):
        """
        Tests the extract_content method. Checks that both a fulltext.txt and a
        acknowledgements.txt file is created (if there is actual content for the
        acknowledgements).

        N. B.
        Do not let the name extract_content portray anything. It is simply to
        keep the same naming convention as the other workers. extract_content
        is the main method the worker will run.

        :return: no return
        """

        self.dict_item[CONSTANTS['ACKNOWLEDGEMENTS']] = "Thank you"
        return_payload = writer.extract_content([self.dict_item])

        self.assertTrue(os.path.exists(self.full_text_file),
                        msg=os.path.exists(self.full_text_file))
        self.assertTrue(os.path.exists(self.acknowledgement_file),
                        msg=os.path.exists(self.acknowledgement_file))

    def test_temporary_file_is_made_and_moved(self):
        """
        Tests the extract_content method. Checks that when the worker writes to
        disk, that it first generates a temporary output file, and then moves
        that file to the expected output name.

        N. B.
        Do not let the name extract_content portray anything. It is simply to
        keep the same naming convention as the other workers. extract_content
        is the main method the worker will run.

        :return: no return
        """

        writer.extract_content([self.dict_item])
        os.remove(self.meta_file)

        temp_path = self.meta_file.replace('meta.json', '')
        temp_file_name = writer.write_to_temp_file(self.dict_item, temp_path)
        self.assertTrue(os.path.exists(temp_file_name))

        writer.move_temp_file_to_file(temp_file_name, self.meta_file)
        self.assertFalse(os.path.exists(temp_file_name))
        self.assertTrue(os.path.exists(self.meta_file))

    def test_write_worker_returns_content(self):
        """
        Tests the extract_content method. Checks that the payload that the
        worker returns, that will go on to another RabbitMQ queue, is in the
        format that we expect.

        N. B.
        Do not let the name extract_content portray anything. It is simply to
        keep the same naming convention as the other workers. extract_content
        is the main method the worker will run.

        :return: no return
        """

        payload = writer.extract_content([self.dict_item])
        self.assertTrue(
            payload == '["MNRAS2014"]', 'Length does not match: {0}'
            .format(payload)
        )

if __name__ == '__main__':
    unittest.main()
