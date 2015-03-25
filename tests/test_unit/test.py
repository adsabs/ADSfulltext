"""
Unit Test of the check records functions for the base class, CheckIfExtract
"""
import sys, os
PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__),'../../'))
sys.path.append(PROJECT_HOME)

import unittest
import utils
import json
import re
import os
import httpretty

from settings import PROJ_HOME, config, CONSTANTS, META_CONTENT
from lib import CheckIfExtract as check
from lib import StandardFileExtract as std_extract
from lib import WriteMetaFile as writer
from lib import test_base
from requests.exceptions import HTTPError


test_file = os.path.join(PROJ_HOME, 'tests/test_integration/stub_data/fulltext.links')
test_file_stub = os.path.join(PROJ_HOME, 'tests/test_integration/stub_data/fulltext_stub.links')
test_file_wrong = os.path.join(PROJ_HOME, 'tests/test_integration/stub_data/fulltext_wrong.links')
test_file_exists = os.path.join(PROJ_HOME, 'tests/test_integration/stub_data/fulltext_exists.links')
test_single_document = os.path.join(PROJ_HOME, 'tests/test_integration/stub_data/fulltext_single_document.links')

test_stub_xml = os.path.join(PROJ_HOME, 'tests/test_unit/stub_data/test.xml')
test_stub_exml = os.path.join(PROJ_HOME, 'tests/test_unit/stub_data/test_elsevier.xml')
test_stub_html = os.path.join(PROJ_HOME, 'tests/test_unit/stub_data/test.html')
test_stub_html_table = os.path.join(PROJ_HOME, 'tests/test_unit/stub_data/test_table.html')
test_stub_text = os.path.join(PROJ_HOME, 'tests/test_unit/stub_data/test.txt')
test_stub_ocr = os.path.join(PROJ_HOME, 'tests/test_unit/stub_data/test.ocr')

test_functional_stub = os.path.join(PROJ_HOME, 'tests/test_functional/stub_data/fulltext_functional_tests.links')


class TestCheckIfExtracted(test_base.TestUnit):

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
        FileInputStream.make_payload()

        # Ensure the PDF more new than the meta.json
        payload = FileInputStream.raw[0]
        with open(payload[CONSTANTS['FILE_SOURCE']], 'w') as not_stale:
            not_stale.write("PDF")

        # Not a nicer way to do this without cleaning up some tests
        meta_content = check.load_meta_file(payload, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")
        meta_content[CONSTANTS['FILE_SOURCE']] = os.path.join(PROJ_HOME, meta_content[CONSTANTS['FILE_SOURCE']])

        updated = check.meta_needs_update(payload, meta_content, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

        self.assertEqual(updated, 'STALE_CONTENT', "The file content should be stale, not %s (%s\n%s)" % (updated, payload, meta_content))

    def test_file_should_be_extracted(self):

        FileInputStream = utils.FileInputStream(test_file)
        FileInputStream.extract()

        with open(test_file, 'r') as in_f:
            text = in_f.read()
        pdf_re = re.compile('pdf')
        pdf_number = len(pdf_re.findall(text))
        standard_number = len([i for i in text.split('\n') if i!= '']) - pdf_number

        payload = check.check_if_extract(FileInputStream.raw, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")
        pdf_payload = json.loads(payload["PDF"])
        standard_payload = json.loads(payload["Standard"])

        if pdf_payload:
            pdf_compare = [content for content in json.loads(payload["PDF"]) if content["UPDATE"] in
            [u"STALE_CONTENT", u"DIFFERING_FULL_TEXT", u"MISSING_FULL_TEXT", u"NOT_EXTRACTED_BEFORE"]]
        else:
            pdf_compare = []

        if standard_payload:
            standard_compare = [content for content in json.loads(payload["Standard"]) if content["UPDATE"] in
            [u"STALE_CONTENT", u"DIFFERING_FULL_TEXT", u"MISSING_FULL_TEXT", u"NOT_EXTRACTED_BEFORE"]]
        else:
            standard_compare = []

        self.assertTrue(len(pdf_compare) == pdf_number, pdf_number)
        self.assertTrue(len(standard_compare) == standard_number)

    def test_output_dictionary_contains_everything_we_need(self):

        FileInputStream = utils.FileInputStream(test_single_document)
        FileInputStream.extract()

        payload = check.check_if_extract(FileInputStream.raw, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

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
        FileInputStream = utils.FileInputStream(test_single_document)
        FileInputStream.extract()

        payload = check.check_if_extract(FileInputStream.raw, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

        self.assertFalse(json.loads(payload['PDF']))
        self.assertTrue(len(json.loads(payload['Standard'])) != 0)


class TestFileStreamInput(test_base.TestUnit):

    def test_file_stream_input_extract_file(self):

        FileInputStream = utils.FileInputStream(test_file)
        ext = FileInputStream.extract()

        with open(test_file, 'r') as f:
            nor = len(f.readlines())

        self.assertEqual(len(FileInputStream.bibcode), nor, "Did not extract the correct number of records from the input file")

    def test_file_stream_input_extract_list(self):

        FileInputStream = utils.FileInputStream(test_file_stub)
        ext = FileInputStream.extract()

        self.assertIn("2015MNRAS.446.4239E", FileInputStream.bibcode)
        self.assertIn(os.path.join(PROJ_HOME, "test.pdf"), FileInputStream.full_text_path)
        self.assertIn("MNRAS", FileInputStream.provider)

    def test_split_payload_into_packet_sizes(self):

        FileInputStream = utils.FileInputStream(test_functional_stub)
        FileInputStream.extract()
        FileInputStream.make_payload(packet_size=10)

        import math
        num_packets = int(math.ceil(len(FileInputStream.raw) / 10.0))

        self.assertTrue(len(FileInputStream.payload) == num_packets, "Found %d packets" % num_packets)


class TestXMLExtractor(unittest.TestCase):

    def setUp(self):
        self.dict_item = {CONSTANTS["FILE_SOURCE"]: test_stub_xml,
                          CONSTANTS['FORMAT']: 'xml', CONSTANTS['PROVIDER']: 'MNRAS'}
        self.extractor = std_extract.EXTRACTOR_FACTORY['xml'](self.dict_item)

    def test_that_we_can_open_an_xml_file(self):
        full_text_content = self.extractor.open_xml()

        self.assertIn("<journal-title>JOURNAL TITLE</journal-title>", full_text_content)

    def test_that_we_can_parse_the_xml_content(self):
        full_text_content = self.extractor.open_xml()
        content = self.extractor.parse_xml()
        journal_title = content.xpath('//journal-title')[0].text_content()

        self.assertEqual(journal_title, "JOURNAL TITLE")

    def test_that_we_can_extract_using_settings_template(self):

        full_text_content = self.extractor.open_xml()
        parsed_xml = self.extractor.parse_xml()
        content = self.extractor.extract_multi_content()

        self.assertEqual(META_CONTENT["xml"].keys(), content.keys())

    def test_that_we_can_extract_all_content_from_payload_input(self):

        file_path = "%s/%s" % (config["FULLTEXT_EXTRACT_PATH"], test_stub_xml)
        pay_load = [self.dict_item]

        content = json.loads(std_extract.extract_content(pay_load))

        self.assertTrue(set(META_CONTENT['xml'].keys()).issubset(content[0].keys()))


class TestXMLElsevierExtractor(unittest.TestCase):

    def setUp(self):
        self.dict_item = {CONSTANTS["FILE_SOURCE"]: test_stub_exml,
                          CONSTANTS['BIBCODE']:  'TEST'}
        self.extractor = std_extract.EXTRACTOR_FACTORY['elsevier'](self.dict_item)

    def test_that_we_can_open_an_xml_file(self):
        full_text_content = self.extractor.open_xml()
        self.assertIn("JOURNAL CONTENT", full_text_content)

    def test_that_we_can_parse_the_xml_content(self):
        full_text_content = self.extractor.open_xml()
        content = self.extractor.parse_xml()
        journal_title = content.xpath("//*[local-name()='title']")[0].text_content()
        self.assertIn("JOURNAL TITLE", journal_title)

    def test_that_we_can_extract_using_settings_template(self):

        full_text_content = self.extractor.open_xml()
        parsed_xml = self.extractor.parse_xml()
        content = self.extractor.extract_multi_content()

        self.assertItemsEqual(['fulltext', 'acknowledgements'], content.keys(), content.keys())
        self.assertIn("JOURNAL CONTENT", content["fulltext"])


class TestHTMLExtractor(unittest.TestCase):

    def setUp(self):
        self.dict_item = {CONSTANTS["FILE_SOURCE"]: "%s,%s" % (test_stub_html, test_stub_html_table),
                          CONSTANTS['BIBCODE']: "TEST"}

        self.extractor = std_extract.EXTRACTOR_FACTORY['html'](self.dict_item)

    def test_that_we_can_open_an_html_file(self):

        full_text_content = self.extractor.open_html()
        self.assertIn("TITLE", full_text_content)

    def test_can_parse_an_html_file(self):

        raw_html = self.extractor.open_html()
        parsed_html = self.extractor.parse_html()
        header = parsed_html.xpath('//h2')[0].text
        self.assertIn("TITLE", header, PROJ_HOME)

    def test_that_we_can_extract_table_contents_correctly(self):

        from lxml.etree import Element
        raw_html = self.extractor.open_html()
        parsed_html = self.extractor.parse_html()
        table_content = self.extractor.collate_tables()

        for key in table_content.keys():
            self.assertTrue(table_content[key].xpath('//table'))
            self.assertTrue(self.extractor.parsed_html.xpath('//h2'))

    def test_that_we_can_extract_using_settings_template(self):

        content = self.extractor.extract_multi_content()

        self.assertEqual(content.keys(), ["fulltext"])

        self.assertIn("ONLY IN TABLE", content['fulltext'],
                      "Table is not in the fulltext: %s" % content['fulltext'])


class TestOCRandTXTExtractor(unittest.TestCase):

    def setUp(self):
        self.dict_item = {CONSTANTS["FILE_SOURCE"]: test_stub_text,
                          CONSTANTS['BIBCODE']: "TEST"}
        self.dict_item_ocr = {CONSTANTS["FILE_SOURCE"]: test_stub_ocr,
                          CONSTANTS['BIBCODE']: "TEST"}

        self.extractor = std_extract.EXTRACTOR_FACTORY['txt'](self.dict_item)

    def test_open_txt_file(self):
        raw_text = self.extractor.open_text()
        self.assertIn("Introduction", raw_text)

    def test_parse_txt_file(self):
        raw_text = self.extractor.open_text()
        parsed_text = self.extractor.parse_text(translate=True, decode=True)
        self.assertIn("Introduction", parsed_text)
        self.assertNotIn("\x00", parsed_text)

    def test_parse_ocr_file(self):
        self.extractor.dict_item = self.dict_item_ocr
        raw_text = self.extractor.open_text()
        parsed_text = self.extractor.parse_text(translate=True, decode=True)
        self.assertIn("introduction", parsed_text.lower())
        self.assertIn("THIS IS AN INTERESTING TITLE", parsed_text)
        self.assertNotIn("\x00", parsed_text)

    def test_ASCII_parsing(self):

        self.extractor.raw_text = "Tab\t CarriageReturn\r New line\n Random Escape characters:" + chr(1) + chr(4) + chr(8)
        expected_out_string = re.sub('\s+', ' ', "Tab\t CarriageReturn\r New line\n Random Escape characters:   ")
        new_instring = self.extractor.parse_text(translate=True, decode=True)

        self.assertEqual(new_instring, expected_out_string)

    def test_Unicode_parsing(self):
        self.extractor.raw_text = u"Tab\t CarriageReturn\r New line\n Random Escape characters:" + u'\u0000'
        expected_out_string = re.sub('\s+', ' ', u"Tab\t CarriageReturn\r New line\n Random Escape characters:")

        new_instring = self.extractor.parse_text(translate=True, decode=True)

        self.assertEqual(new_instring, expected_out_string)

    def test_ASCII_translation_map_works(self):
        instring = "Tab\t CarriageReturn\r New line\n Random Escape characters:" + chr(1) + chr(4) + chr(8)
        expected_out_string = "Tab\t CarriageReturn\r New line\n Random Escape characters:   "
        new_instring = instring.translate(self.extractor.ASCII_translation_map)

        self.assertEqual(new_instring, expected_out_string)

    def test_Unicode_translation_map_works(self):
        instring = u"Tab\t CarriageReturn\r New line\n Random Escape characters:" + u'\u0000'
        expected_out_string = u"Tab\t CarriageReturn\r New line\n Random Escape characters:"
        new_instring = instring.translate(self.extractor.Unicode_translation_map)

        self.assertEqual(new_instring, expected_out_string)

    def test_extract_multi_content_on_text_data(self):
        content = self.extractor.extract_multi_content()
        self.assertIn('introduction', content['fulltext'].lower())


class TestHTTPExtractor(unittest.TestCase):
    def setUp(self):
        self.dict_item = {CONSTANTS["FILE_SOURCE"]: "http://fake/http/address",
                          CONSTANTS['BIBCODE']: "TEST"}

        self.extractor = std_extract.EXTRACTOR_FACTORY['http'](self.dict_item)

        self.body_content = "Full text extract"

    def tearDown(self):
        httpretty.disable()  # disable afterwards, so that you will have no problems in code that uses that socket module
        httpretty.reset()    # reset HTTPretty state (clean up registered urls and request history)

    @httpretty.activate
    def test_http_can_be_open(self):
        httpretty.register_uri(httpretty.GET,
                               self.dict_item[CONSTANTS['FILE_SOURCE']],
                               body=self.body_content)

        response = self.extractor.open_http()

        self.assertEqual(response, self.body_content,
                         'Expected response: %s\n but got: %s' % (self.body_content, response))

    @httpretty.activate
    def test_http_response_not_200(self):
        httpretty.register_uri(httpretty.GET,
                               self.dict_item[CONSTANTS['FILE_SOURCE']],
                               body=self.body_content,
                               status=304)

        self.assertRaises(HTTPError, self.extractor.open_http)

    @httpretty.activate
    def test_http_parses(self):
        httpretty.register_uri(httpretty.GET,
                               self.dict_item[CONSTANTS['FILE_SOURCE']],
                               body=self.body_content,
                               status=200)

        self.extractor.open_http()
        parsed_content = self.extractor.parse_http()

        self.assertEqual(parsed_content, self.body_content)

    @httpretty.activate
    def test_http_multi_content(self):
        httpretty.register_uri(httpretty.GET,
                               self.dict_item[CONSTANTS['FILE_SOURCE']],
                               body=self.body_content,
                               status=200)

        content = self.extractor.extract_multi_content()

        self.assertEqual(content[CONSTANTS['FULL_TEXT']], self.body_content)


class TestWriteMetaFileWorker(unittest.TestCase):

    def setUp(self):
        self.dict_item = {CONSTANTS['META_PATH']: os.path.join(PROJ_HOME, 'tests/test_unit/stub_data/te/st/1/meta.json'),
                          CONSTANTS['FULL_TEXT']: 'hehehe I am the full text',
                          CONSTANTS['FORMAT']: 'xml',
                          CONSTANTS['FILE_SOURCE']: '/vagrant/source.txt',
                          CONSTANTS['BIBCODE']: "MNRAS2014",
                          CONSTANTS['PROVIDER']: "MNRAS",
                          CONSTANTS['UPDATE']: "MISSING_FULL_TEXT"}

        self.meta_file = self.dict_item[CONSTANTS['META_PATH']]
        self.bibcode_pair_tree = self.dict_item[CONSTANTS['META_PATH']].replace('meta.json', '')
        self.full_text_file = self.bibcode_pair_tree + 'fulltext.txt'
        self.acknowledgement_file = self.bibcode_pair_tree + 'acknowledgements.txt'

    def tearDown(self):
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

        content = writer.write_content(self.dict_item)

        self.assertTrue(os.path.exists(self.bibcode_pair_tree),
                            msg=os.path.exists(self.bibcode_pair_tree))

    def test_loads_the_content_correctly_and_makes_meta_file(self):

        content = writer.write_content(self.dict_item)

        self.assertTrue(os.path.exists(self.meta_file),
                            msg=os.path.exists(self.meta_file))

    def test_loads_the_content_correctly_and_makes_full_text_file(self):

        content = writer.write_content(self.dict_item)

        self.assertTrue(os.path.exists(self.full_text_file),
                            msg=os.path.exists(self.full_text_file))

    def test_pipeline_extract_content_extracts_fulltext_correctly(self):

        self.dict_item[CONSTANTS['FORMAT']] = 'txt'
        pipeline_payload = [self.dict_item]

        return_payload = writer.extract_content(pipeline_payload)

        self.assertTrue(return_payload, 1)

        full_text = ""
        with open(self.dict_item[CONSTANTS['META_PATH']].replace('meta.json', 'fulltext.txt'), 'r') as full_text_file:
            full_text = full_text_file.read()

        self.assertEqual(self.dict_item[CONSTANTS['FULL_TEXT']], full_text)

    def test_pipeline_extract_content_extracts_meta_text_correctly(self):
        self.dict_item[CONSTANTS['FORMAT']] = 'txt'
        pipeline_payload = [self.dict_item]

        return_payload = writer.extract_content(pipeline_payload)

        self.assertTrue(return_payload, 1)

        meta_dict = {}
        with open(self.dict_item[CONSTANTS['META_PATH']], 'r') as meta_file:
            meta_dict = json.load(meta_file)

        self.assertEqual(self.dict_item[CONSTANTS['FILE_SOURCE']], meta_dict[CONSTANTS['FILE_SOURCE']])
        self.assertEqual(self.dict_item[CONSTANTS['BIBCODE']], meta_dict[CONSTANTS['BIBCODE']])
        self.assertEqual(self.dict_item[CONSTANTS['PROVIDER']], meta_dict[CONSTANTS['PROVIDER']])
        self.assertEqual(self.dict_item[CONSTANTS['UPDATE']], meta_dict[CONSTANTS['UPDATE']])

    def pipeline_extract(self, format):
        self.dict_item[CONSTANTS['FORMAT']] = format
        pipeline_payload = [self.dict_item]

        return_payload = writer.extract_content(pipeline_payload)

        self.assertTrue(return_payload == '["MNRAS2014"]')

        meta_dict = {}
        with open(self.dict_item[CONSTANTS['META_PATH']], 'r') as meta_file:
            meta_dict = json.load(meta_file)

        self.assertEqual(self.dict_item[CONSTANTS['FILE_SOURCE']], meta_dict[CONSTANTS['FILE_SOURCE']])
        self.assertEqual(self.dict_item[CONSTANTS['BIBCODE']], meta_dict[CONSTANTS['BIBCODE']])
        self.assertEqual(self.dict_item[CONSTANTS['PROVIDER']], meta_dict[CONSTANTS['PROVIDER']])
        self.assertEqual(self.dict_item[CONSTANTS['UPDATE']], meta_dict[CONSTANTS['UPDATE']])

    def test_pipeline_extract_works_for_all_formats(self):

        for format_ in ['txt', 'xml', 'xmlelsevier', 'ocr', 'html', 'http']:
            try:
                self.pipeline_extract(format_)
            except Exception:
                raise Exception

    def test_acknowledgements_file_is_created(self):

        self.dict_item[CONSTANTS['ACKNOWLEDGEMENTS']] = "Thank you"
        return_payload = writer.extract_content([self.dict_item])

        self.assertTrue(os.path.exists(self.full_text_file),
                            msg=os.path.exists(self.full_text_file))
        self.assertTrue(os.path.exists(self.acknowledgement_file),
                            msg=os.path.exists(self.acknowledgement_file))

    def test_temporary_file_is_made_and_moved(self):

        writer.extract_content([self.dict_item])
        os.remove(self.meta_file)

        temp_path = self.meta_file.replace('meta.json', '')
        temp_file_name = writer.write_to_temp_file(self.dict_item, temp_path)
        self.assertTrue(os.path.exists(temp_file_name))

        writer.move_temp_file_to_file(temp_file_name, self.meta_file)
        self.assertFalse(os.path.exists(temp_file_name))
        self.assertTrue(os.path.exists(self.meta_file))

    def test_write_worker_returns_content(self):
        payload = writer.extract_content([self.dict_item])
        self.assertTrue(payload == '["MNRAS2014"]', 'Length does not match: %s' % payload)

if __name__ == '__main__':
    unittest.main()
