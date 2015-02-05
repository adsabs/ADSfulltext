# -*- coding: UTF-8 -*-
"""
StandardFileExtractor Worker Functions

These are the functions for the StandardFileExtractor class. This worker should be able to extract the contents of all
document types, excluding PDF. A lot of the source code has been ported from adsabs/adsdata
"""

import json
import re
import traceback
import os
import unicodedata
from utils import setup_logging, overrides
from lxml.html import soupparser, document_fromstring, fromstring
from lib import entitydefs as edef
from settings import CONSTANTS, META_CONTENT

logger = setup_logging(__file__, __name__)


class StandardExtractorBasicText(object):

    def __init__(self, dict_item):

        # For those interested: http://www.joelonsoftware.com/articles/Unicode.html
        # Translation map (ASCII):
        #     This is used to replace the escape characters. There are 32 escape characters listed for example
        #     here: http://www.robelle.com/smugbook/ascii.html
        #
        #     input_control_characters:
        #     This is a string that contains all the escape characters
        #
        #     translated_control_characters:
        #     This is a string that is equal in length to input_control_characters, where all the escape characters
        #     are replaced by an empty string ' '. The only escape characters kept are \n, \t, \r, (9, 10, 13)
        #
        #     This map can then be given to the string.translate as the map for a string (ASCII encoded)
        #     e.g.,
        #
        #     'jonny\x40myemail.com\n'.translate(dict.fromkeys(filter(lambda x: x not in [9,10,13], range(32))))
        #     'jonny@myemail.com\n'
        #
        # Translation map (Unicode):
        #     This has the same purpose as the previous map, except it works on text that is encoded in utf-8, or some
        #     other unicode encoding. The unicode_control_number array contains a list of tuples, that contain the range
        #     of numbers that want to be removed. i.e., 0x00, 0x08 in unicode form is U+00 00 to U+00 08, which is
        #     just removing the e.g., Null characters, see http://www.fileformat.info/info/charset/UTF-8/list.htm
        #     for a list of unicode numberings.
        #     e.g.,
        #
        #     This map can then be given to the string.translate as the map for a unicode type (e.g., UTF-8 encoded)
        #
        #     u'jonny\x40myemail.com\n'.translate(dict.fromkeys(filter(lambda x: x not in [9,10,13], range(32))))
        #     u'jonny@myemail.com\n'
        #
        #
        #     unicodedata.normalize(unicode_string, 'NFKC'):
        #
        #         https://docs.python.org/2/library/unicodedata.html#unicodedata.normalize
        #         http://stackoverflow.com/questions/14682397/can-somone-explain-how-unicodedata-normalizeform-unistr-work-with-examples
        #         NFKC = Normal Form K Composition
        #
        #         'K' converts characters such as ① to 1
        #         'C' composes characters such as C, to Ç

        import string

        self.dict_item = dict_item
        self.raw_text = None
        self.parsed_text = None

        translated_control_characters = "".join([chr(i) if i in [9, 10, 13] else ' ' for i in range(0,32)])
        input_control_characters = "".join([chr(i) for i in range(0,32)])
        self.ASCII_translation_map = string.maketrans(input_control_characters, translated_control_characters)

        unicode_control_numbers = [(0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F), (0x7F, 0x84), (0x86, 0x9F),
                                    (0xD800, 0xDFFF), (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF),
                                    (0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF), (0x3FFFE, 0x3FFFF),
                                    (0x4FFFE, 0x4FFFF), (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
                                    (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF), (0x9FFFE, 0x9FFFF),
                                    (0xAFFFE, 0xAFFFF), (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
                                    (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF), (0xFFFFE, 0xFFFFF),
                                    (0x10FFFE, 0x10FFFF)]
        self.Unicode_translation_map = dict.fromkeys(unicode_number
                                                     for starting_unicode_number, ending_unicode_number
                                                     in unicode_control_numbers
                                                     for unicode_number
                                                     in range(starting_unicode_number, ending_unicode_number+1))

    def open_text(self):

        with open(self.dict_item[CONSTANTS['FILE_SOURCE']], 'r') as f:
            raw_text = f.read()

        self.raw_text = raw_text
        return self.raw_text

    def parse_text(self, translate=False, decode=False):

        raw_text = self.raw_text
        if translate:
            if type(raw_text) == str:
                raw_text = raw_text.translate(self.ASCII_translation_map)
            else:
                raw_text = raw_text.translate(self.Unicode_translation_map)

        if decode and type(raw_text) == str:
            raw_text = raw_text.decode('utf-8', 'ignore')

        raw_text = unicodedata.normalize('NFKC', unicode(raw_text))
        raw_text = re.sub('\s+', ' ', raw_text) # remove duplicated spaces?

        self.parsed_text = raw_text
        return self.parsed_text

    def extract_multi_content(self, translate=True, decode=True):
        self.open_text()
        self.parse_text(translate=translate, decode=decode)

        meta_out = {}
        meta_out["fulltext"] = self.parsed_text
        return meta_out


class StandardExtractorHTML(object):

    def __init__(self, dict_item):
        self.dict_item = dict_item
        self.file_input = self.dict_item[CONSTANTS['FILE_SOURCE']].split(",")[0]
        self.raw_html = None
        self.parsed_html = None
        self.dictionary_of_tables = None

    def open_html(self, in_html=False):
        import codecs

        if not in_html:
            html_file = self.file_input
        else:
            html_file = in_html

        with codecs.open(html_file, 'r', 'utf-8') as f:
            raw_html = f.read()

        # raw_html = raw_html.decode('utf-8', 'ignore')
        raw_html = edef.convertentities(raw_html)

        if not in_html:
            self.raw_html = raw_html

        return raw_html

    def parse_html(self, in_html=False):

        if not in_html:
            parsed_html = document_fromstring(self.raw_html)
            self.parsed_html = parsed_html
        else:
            parsed_html = document_fromstring(in_html)

        logger.info("Parsed HTML. %s" % parsed_html)

        return parsed_html

        # Alternative used etree HTMLParser, but this requires an extra two calls, one making
        # it a StringIO, and then acquiring the root element tree, but I don't see a difference?
        # parser = etree.HTMLParser()
        # tree = etree.parse(StringIO(html), parser)
        #
        # return tree.getroot()

    def collate_tables(self):
        table_source_files = re.split('\s*,\s*', self.dict_item[CONSTANTS['FILE_SOURCE']])
        table_source_files.reverse()
        file_source = table_source_files.pop()

        dictionary_of_tables = {}
        for table_file_path in filter(lambda x: re.search('table', x), table_source_files):
            table_name = os.path.basename(table_file_path)

            table_raw_html = self.open_html(table_file_path)
            dictionary_of_tables[table_name] = self.parse_html(table_raw_html)

        self.dictionary_of_tables = dictionary_of_tables

        logger.info("Collated %d tables" % len(self.dictionary_of_tables))

        return self.dictionary_of_tables

    def extract_multi_content(self):

        self.open_html()
        self.parse_html()

        removed_content = None

        # Remove anything before introduction
        for xpath in META_CONTENT['HTML']['introduction']:
            try:
                removed_content = self.parsed_html.xpath(xpath)[0]
                break
            except Exception:
                print Exception(traceback.format_exc())

        if removed_content is None:
            print "Could not find intro for %s (last xpath: %s)" % \
                  (self.dict_item[CONSTANTS['BIBCODE']], xpath)
        else:
            first_position_index = removed_content.getparent().index(removed_content)
            for element_tree_node in removed_content.getchildren()[:first_position_index]:
                element_tree_node.getparent().remove(element_tree_node)

        # Remove the references
        for xpath in META_CONTENT['HTML']['references']:
            removed_content = None
            try:
                removed_content = self.parsed_html.xpath(xpath)[0]
                html_ul_element = removed_content.getnext()
                html_ul_element.getparent().remove(html_ul_element)
                removed_content.getparent().remove(removed_content)
                break
            except Exception:
                print "Could not find references for %s (last xpath: %s)" % \
                      (self.dict_item[CONSTANTS['BIBCODE']], xpath)

        # Insert tables from external files
        first_parsed_html = self.parsed_html
        self.collate_tables()
        for table_name, table_root_node in self.dictionary_of_tables.items():

            table_node_to_insert = None
            logger.debug("Attempting to find table contents: %s" % table_name)
            for xpath in META_CONTENT['HTML']['table']:

                try:
                    table_node_to_insert = table_root_node.xpath(xpath)[0].getparent()
                    break
                except AttributeError:
                    raise AttributeError("You used an incorrect method")
                except Exception:
                    # print traceback.format_exc()
                    raise Exception("Could not find table content for %s (last xpath: %s)" %
                                    (table_name, xpath))

            logger.debug("Attempting to find table links: %s" % table_name)
            for xpath in META_CONTENT['HTML']['table_links']:
                try:
                    logger.info(self.parsed_html)
                    table_nodes_in_file_source = self.parsed_html.xpath(xpath.replace('TABLE_NAME', table_name))
                    break
                except AttributeError:
                    raise AttributeError("You used an incorrect method", traceback.format_exc(),
                                         table_name, self.parsed_html)
                except Exception:
                    # print traceback.format_exc()
                    raise Exception("Could not find table links for %s (last xpath: %s)" % (table_name, xpath.replace('TABLE_NAME', table_name)))

            logger.debug("Attempting to replace table at table links: %s" % table_name)
            if table_nodes_in_file_source:
                parent_node_of_table_link = table_nodes_in_file_source[0].getparent()
                parent_node_of_table_link.replace(table_nodes_in_file_source[0], table_node_to_insert)
                [remaining_node.getparent().remove(remaining_node) for remaining_node in table_nodes_in_file_source[1:]]
        try:
            for xpath in META_CONTENT['HTML']['head']:
                try:
                    self.parsed_html.xpath(xpath)
                    break
                except Exception:
                    continue
        except Exception:
            pass


        string_of_all_html = " ".join([individual_element_tree_node for individual_element_tree_node
                                       in self.parsed_html.itertext()
                                       if individual_element_tree_node
                                       and not individual_element_tree_node.isspace()])

        meta_out = {"fulltext": string_of_all_html}

        return meta_out


class StandardExtractorXML(object):

    def __init__(self, dict_item):

        self.file_input = dict_item[CONSTANTS['FILE_SOURCE']]
        self.raw_xml = None
        self.parsed_xml = None
        self.meta_name = "XML"

    def open_xml(self):

        raw_xml = None
        with open(self.file_input, 'r') as f:
            raw_xml = f.read()
            raw_xml = re.sub('(<!-- body|endbody -->)', '', raw_xml)
            raw_xml = edef.convertentities(raw_xml.decode('utf-8', 'ignore'))
            raw_xml = re.sub('<\?CDATA.+?\?>', '', raw_xml)
            self.raw_xml = raw_xml
        return raw_xml

    def parse_xml(self):

        parsed_content = soupparser.fromstring(self.raw_xml.encode('utf-8'))

        # strip out the latex stuff (for now)
        for e in parsed_content.xpath('//inline-formula'):
            e.getparent().remove(e)

        self.parsed_xml = parsed_content
        return parsed_content

    def extract_multi_content(self):

        meta_out = {}
        self.open_xml()
        self.parse_xml()

        for content_name in META_CONTENT[self.meta_name]:
            logger.info("Trying meta content: %s" % content_name)
            for static_xpath in META_CONTENT[self.meta_name][content_name]:
                logger.info("Trying xpath: %s" % static_xpath)
                try:
                    meta_out[content_name] = self.parsed_xml.xpath(static_xpath)[0].text_content()
                    logger.info("Successful")
                    break
                except IndexError:
                    pass
                except KeyError:
                    raise KeyError("You gave a malformed xpath call to HTMLElementTree: %s" % static_xpath)
                except Exception:
                    raise Exception(traceback.format_exc())

        return meta_out


class StandardElsevierExtractorXML(StandardExtractorXML):

    def __init__(self, dict_item):
        StandardExtractorXML.__init__(self, dict_item)
        self.meta_name = "XMLElsevier"

    def parse_xml(self):
        self.parsed_xml = fromstring(self.raw_xml.encode('utf-8'))
        return self.parsed_xml

    @overrides(StandardExtractorXML)
    def extract_multi_content(self):
        content = super(StandardElsevierExtractorXML, self).extract_multi_content()
        return content


EXTRACTOR_FACTORY = {
    "xml": StandardExtractorXML,
    "html": StandardExtractorHTML,
    "txt": StandardExtractorBasicText,
    "ocr": StandardExtractorBasicText,
    "elsevier": StandardElsevierExtractorXML,
}
# Elsevier
# HTTP
#-----
# PDF


def extract_content(input_list):

    import json
    output_list = []

    ACCEPTED_FORMATS = ["xml", "html"]

    for dict_item in input_list:

        try:
            ExtractorClass = EXTRACTOR_FACTORY[dict_item[CONSTANTS['FILE_SOURCE']].lower().split(".")[-1]]
        except KeyError:
            raise KeyError("You gave a format not currently supported for extraction",traceback.format_exc())

        try:
            Extractor = ExtractorClass(dict_item)
            parsed_content = Extractor.extract_multi_content()
            output_list.append(parsed_content)
        except Exception:
            raise Exception(traceback.format_exc())

        del Extractor, parsed_content

            #
            #
            # opened_XML = open_xml(dict_item[CONSTANTS['FILE_SOURCE']])
            # parsed_XML = parse_xml(opened_XML)
            # parsed_content = extract_multi_content(parsed_XML)

    return json.dumps(output_list)
    # raw_content = open_xml()

    # return json.dumps(message)