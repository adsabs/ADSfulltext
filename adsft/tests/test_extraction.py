import sys
if sys.version_info > (3,):
    from builtins import chr
import unittest
import os
import re

from adsft import extraction, rules, utils
from adsft.tests import test_base
from adsputils import load_config
import unittest
import httpretty
from requests.exceptions import HTTPError

class TestXMLExtractorBase(test_base.TestUnit):
    """
    Base class for XML Extractor unit tests
    """

    def setUp(self):
        super(TestXMLExtractorBase, self).setUp()
        self.preferred_parser_names = load_config().get('PREFERRED_XML_PARSER_NAMES') # Iterate through all the parsers defined in config.py
        #self.preferred_parser_names = (None,) # Iterate through the parsers (as defined in config.py) until one succeeds

class TestXMLExtractor(TestXMLExtractorBase):
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
        super(TestXMLExtractor, self).setUp()
        self.dict_item = {'ft_source': self.test_stub_xml,
                          'file_format': 'xml',
                          'provider': 'MNRAS'}
        self.extractor = extraction.EXTRACTOR_FACTORY['xml'](self.dict_item)

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

        for parser_name in self.preferred_parser_names:
            self.extractor.parse_xml(preferred_parser_names=(parser_name,))
            journal_title = self.extractor.extract_string('//journal-title')
            self.assertEqual(journal_title, 'JOURNAL TITLE')

    def test_that_we_correctly_remove_inline_fomulas_from_the_xml_content(self):
        """
        Tests the parse_xml method. Checks that the parsed content allows access
        to the XML marked-up content, and that the content extracted matches
        what is expected.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()

        for parser_name in self.preferred_parser_names:
            self.extractor.parse_xml(preferred_parser_names=(parser_name,))
            section = self.extractor.extract_string('//body//sec[@id="s1"]//p')
            self.assertEqual(section, 'INTRODUCTION GOES HERE')


    def test_iso_8859_1_xml(self):
        """
        Test that we properly read iso 8859 formatted file.
        Since we are not reading the default file we must recreate the extractor object.

        :return: no return
        """

        self.dict_item['ft_source'] = self.test_stub_iso8859
        self.extractor = extraction.EXTRACTOR_FACTORY['xml'](self.dict_item)
        full_text_content = self.extractor.open_xml()

        for parser_name in self.preferred_parser_names:
            self.extractor.parse_xml(preferred_parser_names=(parser_name,))
            article_number = self.extractor.extract_string('//article-number')
            self.assertEqual(article_number, '483879')

    def test_multi_file(self):
        """
        some entries in fulltext/all.links specify multiple files

        typically the first has text from the article while the rest have the text from tables

        :return: no return
        """
        self.dict_item = {'ft_source': self.test_multi_file,
                          'file_format': 'xml',
                          'provider': 'MNRAS',
                          'bibcode': 'test'}

        content = extraction.extract_content([self.dict_item])
        # does the fulltext contain two copies of the file's contents
        self.assertEqual(2, content[0]['fulltext'].count('Entry 1'))


    def test_that_we_can_extract_using_settings_template(self):
        """
        Tests the extract_multi_content method. This checks that all the meta
        data extracted is what we expect. The expected meta data to be extracted
        is defined in settings.py by the user.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()
        for parser_name in self.preferred_parser_names:
            content = self.extractor.extract_multi_content(preferred_parser_names=(parser_name,))
            self.assertEqual(list(rules.META_CONTENT['xml'].keys()).sort(), list(content.keys()).sort())

    def test_that_we_can_extract_all_content_from_payload_input(self):
        """
        Tests the extract_content method. This checks that all of the XML meta
        data defined in settings.py is extracted from the stub XML data.

        :return: no return
        """

        file_path = u'{0}/{1}'.format(self.app.conf['FULLTEXT_EXTRACT_PATH'],
                                     self.test_stub_xml)
        pay_load = [self.dict_item]

        content = extraction.extract_content(pay_load)

        self.assertTrue(
            set(rules.META_CONTENT['xml'].keys()).issubset(content[0].keys())
        )

    def test_that_the_correct_extraction_is_used_for_the_datatype(self):
        """
        Ensure that the defined data type in the settings.py dictionary loads
        the correct method for extraction

        :return: no return
        """

        extract_string = self.extractor.data_factory['string']
        extract_list = self.extractor.data_factory['list']

        if sys.version_info > (3,):
            es_name = extract_string.__name__
            el_name = extract_list.__name__
        else:
            es_name = extract_string.func_name
            el_name = extract_list.func_name

        self.assertTrue(
            es_name == 'extract_string',
        )

        self.assertTrue(
            el_name == 'extract_list',
        )

    def test_that_we_can_extract_a_list_of_datasets(self):
        """
        Within an XML document there may exist more than one dataset. To
        ensure that they are all extracted, we should check that this works
        otherwise there will be missing content

        :return: no return
        """

        self.dict_item['bibcode'] = 'test'
        full_text_content = self.extractor.open_xml()

        for parser_name in self.preferred_parser_names:
            content = self.extractor.extract_multi_content(preferred_parser_names=(parser_name,))

            full_text = content['fulltext']
            acknowledgements = content['acknowledgements']
            data_set = content['dataset']
            data_set_length = len(data_set)

            if sys.version_info > (3,):
                test_type = str
            else:
                test_type = unicode

            self.assertIs(test_type, type(acknowledgements))

            self.assertIs(test_type, type(full_text))
            expected_full_text = 'INTRODUCTION'
            self.assertTrue(
                expected_full_text in full_text,
                u'Full text is wrong: {0} [expected: {1}, data: {2}]'
                .format(full_text,
                        expected_full_text,
                        full_text)
            )

            self.assertIs(list, type(data_set))
            expected_dataset = 2
            self.assertTrue(
                data_set_length == expected_dataset,
                u'Number of datasets is wrong: {0} [expected: {1}, data: {2}]'
                .format(data_set_length,
                        expected_dataset,
                        data_set)
            )

    def test_that_we_can_parse_html_entity_correctly(self):
        """
        Tests the parse_xml method. Checks that the HTML entities are parsed
        without errors caused by escaped ambersands.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()
        for parser_name in self.preferred_parser_names:
            self.extractor.parse_xml(preferred_parser_names=(parser_name,))
            section = self.extractor.extract_string('//body//sec[@id="s2"]//p')
            self.assertEqual(section, u'THIS SECTION TESTS HTML ENTITIES LIKE \xc5 >.')

    def test_that_the_tail_is_preserved(self):
        """
        Tests that when a tag is removed any trailing text is preserved by appending
        it to the previous or parent element.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()
        for parser_name in self.preferred_parser_names:
            self.extractor.parse_xml(preferred_parser_names=(parser_name,))
            section = self.extractor.extract_string('//body//sec[@id="s3"]//p')
            self.assertEqual(section, u'THIS SECTION TESTS THAT THE TAIL IS PRESERVED .')

    def test_that_comments_are_ignored(self):
        """
        Tests that parsing the xml file ignores any comments like <!-- example comment -->.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()
        for parser_name in self.preferred_parser_names:
            self.extractor.parse_xml(preferred_parser_names=(parser_name,))
            section = self.extractor.extract_string('//body//sec[@id="s4"]//p')
            self.assertEqual(section, u'THIS SECTION TESTS THAT COMMENTS ARE REMOVED.')

    def test_that_cdata_is_removed(self):
        """
        Tests that parsing the xml file either removes CDATA tags like in the case of
        <?CDATA some data?> where it is in the form of a "processing instruction" or ignores
        the cdata content when in this <![CDATA] some data]]> form, which BeautifulSoup
        calls a "declaration".

        :return: no return
        """

        full_text_content = self.extractor.open_xml()
        for parser_name in self.preferred_parser_names:
            self.extractor.parse_xml(preferred_parser_names=(parser_name,))
            section = self.extractor.extract_string('//body//sec[@id="s5"]//p')
            self.assertEqual(section, u'THIS SECTION TESTS THAT CDATA IS REMOVED.')

    def test_that_table_is_extracted_correctly(self):
        """
        Tests that the labels/comments for tables are kept while the content of
        the table is removed. Table footers are being removed in some cases where
        a graphic tag with no closing tag like <graphic xlink:href="example.gif">
        is reconciled with a closing tag that encompasses additonal content like the
        table footer. Since graphics are one of the tags we remove to avoid garbage
        text in our output, it correctly gets removed but takes content that should remain
        in the fulltext output with it (like the table footer).

        :return: no return
        """

        full_text_content = self.extractor.open_xml()

        s = u"TABLE I. TEXT a NOTES a TEXT"
        for parser_name in self.preferred_parser_names:
            self.extractor.parse_xml(preferred_parser_names=(parser_name,))
            section = self.extractor.extract_string('//body//table-wrap')
            self.assertEqual(section, s)

    def test_body_tag(self):

        """
        This tests that the parsers correctly extract the body tag.

        This is important for parsers lxml-xml and direct-lxml-xml
        which remove the body tag if they are not in the format:

        <html>
        <head></head>
        <body></body>
        </html>

        Also important for parsers lxml-xml and direct-lxml-xml, which are
        affected by namespaces in tags of the form namespace:name (e.g. ja:body).
        """

        full_text_content = self.extractor.open_xml()

        for parser_name in self.preferred_parser_names:
            self.extractor.parse_xml(preferred_parser_names=(parser_name,))
            section = self.extractor.extract_string('//body')

            self.assertEqual(section, u"I. INTRODUCTION INTRODUCTION GOES HERE "
                u"II. SECTION II THIS SECTION TESTS HTML ENTITIES LIKE \xc5 >. "
                u"III. SECTION III THIS SECTION TESTS THAT THE TAIL IS PRESERVED . "
                u"IV. SECTION IV THIS SECTION TESTS THAT COMMENTS ARE REMOVED. "
                u"V. SECTION V THIS SECTION TESTS THAT CDATA IS REMOVED. "
                u"Manual Entry 1 Manual Entry 2 TABLE I. TEXT a NOTES a TEXT"
            )


    def test_extraction_of_acknowledgments(self):

        """
        This tests that acknowledgments are extracted, acknowledgments should include the
        facilities as of issue #100 in github. There are cases in which the acknowledgments
        are found inside the body tag, but the body tag should not include the acknowledgments
        as of issue #18. An acknowledgement field is included in the body tag in test.xml to
        test that these are being moved outside of the body tag, which is why we see 'ACK
        INSIDE BODY TAG.' appended to this acknowledgment.

        :return: no return
        """
        full_text_content = self.extractor.open_xml()

        for parser_name in self.preferred_parser_names:
            content = self.extractor.extract_multi_content(preferred_parser_names=(parser_name,))
            self.assertEqual(content['acknowledgements'], u"Acknowledgments WE ACKNOWLEDGE. Facilities: FacilityName1 , "
                                                            "FacilityName2 , FacilityName3 , FacilityName4 , FacilityName5 , "
                                                            "FacilityName6 , FacilityName7\nACK INSIDE BODY TAG.")

    def test_extraction_of_facilities(self):

        """
        This tests that we can extract the faciltites field.The first facility is
        a test to make sure we are not extracting facilities where the xlink:href is
        missing, and the second facilities where xlink:href is empty. This is
        discussed here: https://github.com/adsabs/ADSfulltext/issues/107

        :return: no return
        """
        facilities = [u'FacilityID3',
                        u'FacilityID4',
                        u'FacilityID5',
                        u'FacilityID6',
                        u'FacilityID7']

        full_text_content = self.extractor.open_xml()

        for parser_name in self.preferred_parser_names:
            content = self.extractor.extract_multi_content(preferred_parser_names=(parser_name,))
            self.assertEqual(sorted(content['facility']), facilities)

    def test_removal_of_comment_syntax_around_body(self):

        """
        This tests the removal of comment syntax indicating the body of
        the article used by some publishers (AGU, sometimes Wiley).
        See https://github.com/adsabs/ADSfulltext/issues/104

        :return: no return
        """

        raw_xml = "<!-- body <body><p>body content</p></body> endbody -->"

        for parser_name in self.preferred_parser_names:
            self.assertEqual(self.extractor._remove_special_elements(raw_xml, parser_name), "<body><p>body content</p></body> ")


class TestNonStandardXMLExtractor(TestXMLExtractorBase):

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
            super(TestNonStandardXMLExtractor, self).setUp()
            self.dict_item = {'ft_source': self.test_stub_nonstandard_xml,
                              'file_format': 'xml',
                              'provider': 'MNRAS'}
            self.extractor = extraction.EXTRACTOR_FACTORY['xml'](self.dict_item)

        def test_failure_of_all_parsers_in_loop(self):
            """
            This ensures that articles that fail to get extracted by all of the parsers
            we loop through (defined in config) will return an empty body.

            See https://github.com/adsabs/ADSfulltext/issues/101
            """

            self.extractor.open_xml()

            for parser_name in self.preferred_parser_names:
                self.extractor.parse_xml(preferred_parser_names=(parser_name,))
                content = self.extractor.extract_string('//body')
                self.assertEqual(content, u'')

class TestTEIXMLExtractor(TestXMLExtractorBase):
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

        super(TestTEIXMLExtractor, self).setUp()
        self.dict_item = {'ft_source': self.test_stub_teixml,
                          'file_format': 'teixml',
                          'provider': 'A&A',
                          'bibcode': 'TEST'}
        self.extractor = extraction.EXTRACTOR_FACTORY['teixml'](self.dict_item)


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

        for parser_name in self.preferred_parser_names:
            self.extractor.parse_xml(preferred_parser_names=(parser_name,))
            journal_title = self.extractor.extract_string('//title')
            self.assertEqual(journal_title, 'ASTRONOMY AND ASTROPHYSICS The NASA Astrophysics Data System: Architecture')

    def test_that_we_can_extract_using_settings_template(self):
        """
        Tests the extract_multi_content method. This checks that all the meta
        data extracted is what we expect. The expected meta data to be extracted
        is defined in settings.py by the user.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()
        for parser_name in self.preferred_parser_names:
            content = self.extractor.extract_multi_content(preferred_parser_names=(parser_name,))

            self.assertEqual(rules.META_CONTENT['teixml'].keys(), content.keys())

    def test_that_we_can_extract_all_content_from_payload_input(self):
        """
        Tests the extract_content method. This checks that all of the XML meta
        data defined in settings.py is extracted from the stub XML data.

        :return: no return
        """

        pay_load = [self.dict_item]

        content = extraction.extract_content(pay_load)

        self.assertTrue(
            set(rules.META_CONTENT['teixml'].keys()).issubset(content[0].keys())
        )

    def test_that_we_can_extract_acknowledgments(self):
        """

        """
        ack = u"Acknowledgements. The usefulness of a bibliographic service is only as good as the quality and quantity of the data it contains . The ADS project has been lucky in benefitting from the skills and dedication of several people who have significantly contributed to the creation and management of the underlying datasets. In particular, we would like to acknowledge the work of Elizabeth Bohlen, Donna Thompson, Markus Demleitner, and Joyce Watson. Funding for this project has been provided by NASA under grant NCC5-189."

        full_text_content = self.extractor.open_xml()
        for parser_name in self.preferred_parser_names:
            content = self.extractor.extract_multi_content(preferred_parser_names=(parser_name,))

            self.assertEqual(content['acknowledgements'], ack)



class TestXMLElsevierExtractor(TestXMLExtractorBase):
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

        super(TestXMLElsevierExtractor, self).setUp()
        self.dict_item = {'ft_source': self.test_stub_exml,
                          'bibcode': 'TEST'
                          }
        self.extractor = extraction.EXTRACTOR_FACTORY['elsevier'](self.dict_item)


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

        for parser_name in self.preferred_parser_names:
            self.extractor.parse_xml(preferred_parser_names=(parser_name,))
            journal_title = self.extractor.extract_string('//*[local-name()=\'title\']')
            self.assertIn('JOURNAL TITLE', journal_title)

    def test_that_we_can_extract_using_settings_template(self):
        """
        Tests the extract_multi_content method. This checks that all the meta
        data keywords extracted are the same as those expected. The expected
        meta data to be extracted is defined in settings.py by the user.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()
        for parser_name in self.preferred_parser_names:
            content = self.extractor.extract_multi_content(preferred_parser_names=(parser_name,))

            if sys.version_info > (3,):
                func = self.assertCountEqual
            else:
                func = self.assertItemsEqual
            func(['fulltext', 'acknowledgements', 'dataset'],
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

        if sys.version_info > (3,):
            es_name = extract_string.__name__
            el_name = extract_list.__name__
        else:
            es_name = extract_string.func_name
            el_name = extract_list.func_name

        self.assertTrue(
            es_name == 'extract_string',
        )

        self.assertTrue(
            el_name == 'extract_list',
        )

    def test_that_we_can_extract_a_list_of_datasets(self):
        """
        Within an XML document there may exist more than one dataset. To
        ensure that they are all extracted, we should check that this works
        otherwise there will be missing content

        :return: no return
        """

        self.dict_item['bibcode'] = 'test'
        full_text_content = self.extractor.open_xml()

        for parser_name in self.preferred_parser_names:
            content = self.extractor.extract_multi_content(preferred_parser_names=(parser_name,))

            full_text = content['fulltext']
            acknowledgements = content['acknowledgements']
            data_set = content['dataset']
            data_set_length = len(data_set)

            if sys.version_info > (3,):
                test_type = str
            else:
                test_type = unicode

            self.assertIs(test_type, type(acknowledgements))

            self.assertIs(test_type, type(full_text))
            expected_full_text = 'CONTENT'
            self.assertTrue(
                expected_full_text in full_text,
                u'Full text is wrong: {0} [expected: {1}, data: {2}]'
                .format(full_text,
                        expected_full_text,
                        full_text)
            )

            self.assertIs(list, type(data_set))
            expected_dataset = 2
            self.assertTrue(
                data_set_length == expected_dataset,
                u'Number of datasets is wrong: {0} [expected: {1}, data: {2}]'
                .format(data_set_length,
                        expected_dataset,
                        data_set)
            )

    def test_that_we_can_parse_html_entity_correctly(self):
        """
        Tests the parse_xml method. Checks that the HTML entities are parsed
        without errors caused by escaped ambersands.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()

        for parser_name in self.preferred_parser_names:
            self.extractor.parse_xml(preferred_parser_names=(parser_name,))
            section = self.extractor.extract_string('//body//section[@id="s2"]//para')
            self.assertEqual(section, u'THIS SECTION TESTS HTML ENTITIES LIKE \xc5 >.')

    def test_that_the_tail_is_preserved(self):
        """
        Tests that when a tag is removed any trailing text is preserved by appending
        it to the previous or parent element.

        This test currently only works with the lxml-xml parser when extracting
        Elsevier XML data.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()

        for parser_name in self.preferred_parser_names:
            self.extractor.parse_xml(preferred_parser_names=(parser_name,))
            section = self.extractor.extract_string('//body//section[@id="s3"]//para')
            self.assertEqual(section, u'THIS SECTION TESTS THAT THE TAIL IS PRESERVED .')

    def test_that_comments_are_ignored(self):
        """
        Tests that parsing the xml file ignores any comments like <!-- example comment -->.

        :return: no return
        """

        full_text_content = self.extractor.open_xml()

        for parser_name in self.preferred_parser_names:
            self.extractor.parse_xml(preferred_parser_names=(parser_name,))
            section = self.extractor.extract_string('//body//section[@id="s4"]//para')
            self.assertEqual(section, u'THIS SECTION TESTS THAT COMMENTS ARE REMOVED.')



class TestHTMLExtractor(test_base.TestUnit):
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

        super(TestHTMLExtractor, self).setUp()
        self.dict_item = {
            'ft_source': u'{0},{1}'.format(self.test_stub_html,
                                           self.test_stub_html_table),
            'bibcode': 'TEST'
        }
        self.extractor = extraction.EXTRACTOR_FACTORY['html'](self.dict_item)

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
        self.assertIn('TITLE', header, self.app.conf['PROJ_HOME'])

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

        self.assertEqual(list(content.keys()), ['fulltext'])
        self.assertIn(
            'ONLY IN TABLE',
            content['fulltext'],
            u'Table is not in the fulltext: {0}'.format(content['fulltext'])
        )


class TestOCRandTXTExtractor(test_base.TestUnit):
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

        super(TestOCRandTXTExtractor, self).setUp()
        self.dict_item = {'ft_source': self.test_stub_text,
                          'bibcode': 'TEST'}
        self.dict_item_ocr = {'ft_source': self.test_stub_ocr,
                          'bibcode': 'TEST'}

        self.extractor = extraction.EXTRACTOR_FACTORY['txt'](self.dict_item)

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

        expected_out_string = 'Tab CarriageReturn New line Random Escape characters:'

        new_instring = self.extractor.parse_text(translate=True, decode=True)

        self.assertEqual(new_instring, expected_out_string)

    def test_Unicode_parsing(self):
        """
        Tests the parse_text method. Checks that escape characters are removed
        as expected for unicode characters.

        :return: no return
        """

        self.extractor.raw_text = \
            u'Tab\t CarriageReturn New line\n Random Escape characters:' \
            + u'\u0000'

        expected_out_string = u'Tab CarriageReturn New line Random Escape characters:'

        new_instring = self.extractor.parse_text(translate=True, decode=True)

        self.assertEqual(new_instring, expected_out_string)

    def test_translation_map_works(self):
        """
        Tests the translation map from the utils.py module. Ensures that
        escape characters are removed from the string.

        :return: no return
        """

        # test replace with spaces
        instring = \
            'Tab\t CarriageReturn\r New line\n Random Escape characters:'\
            + chr(0x0B) + chr(0xA0) + chr(0x1680)

        expected_out_string = \
            'Tab\t CarriageReturn  New line\n Random Escape characters:   '

        new_instring = instring.translate(self.TC.master_translate_map)

        self.assertEqual(new_instring, expected_out_string)

        # test replace with None
        instring = \
            'Tab\t CarriageReturn\r New line\n Random Escape characters:' \
            + chr(0x00) + chr(0xAD) + chr(0xE000)

        expected_out_string = \
            'Tab\t CarriageReturn  New line\n Random Escape characters:'

        new_instring = instring.translate(self.TC.master_translate_map)

        self.assertEqual(new_instring, expected_out_string)

        # test both
        instring = \
            'Tab\t CarriageReturn\r New line\n Random Escape characters:' \
            + chr(0x202F) + chr(0xFDD0)

        expected_out_string = \
            'Tab\t CarriageReturn  New line\n Random Escape characters: '

        new_instring = instring.translate(self.TC.master_translate_map)

        self.assertEqual(new_instring, expected_out_string)

    def test_extract_multi_content_on_text_data(self):
        """
        Tests the extract_multi_content method. Checks that the full text
        extracted matches what we expect it should extract.

        :return: no return
        """

        content = self.extractor.extract_multi_content()
        self.assertIn('introduction', content['fulltext'].lower())


class TestHTTPExtractor(test_base.TestUnit):
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

        super(TestHTTPExtractor, self).setUp()
        self.dict_item = {'ft_source': 'http://fake/http/address',
                          'bibcode': 'TEST'}
        self.extractor = extraction.EXTRACTOR_FACTORY['http'](self.dict_item)
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
                               self.dict_item['ft_source'],
                               body=self.body_content)

        response = self.extractor.open_http()

        self.assertEqual(
            response,
            self.body_content,
            u'Expected response: {0}\n but got: {1}'
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
                               self.dict_item['ft_source'],
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
                               self.dict_item['ft_source'],
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
                               self.dict_item['ft_source'],
                               body=self.body_content,
                               status=200)

        content = self.extractor.extract_multi_content()

        self.assertEqual(content['fulltext'], self.body_content)

if __name__ == '__main__':
    unittest.main()
