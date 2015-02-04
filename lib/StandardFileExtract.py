"""
StandardFileExtractor Worker Functions

These are the functions for the StandardFileExtractor class. This worker should be able to extract the contents of all
document types, excluding PDF. A lot of the source code has been ported from adsabs/adsdata
"""

import json
import re
import traceback
import utils
import os
from lxml.html import soupparser, document_fromstring
from lib import entitydefs as edef
from settings import CONSTANTS, META_CONTENT

logger = utils.setup_logging(__file__, __name__)


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
        num = 1
        logger.info("%d. %s" % (num, self.parsed_html))
        num += 1
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
        logger.info("%d. %s" % (num, self.parsed_html))
        num += 1
        self.collate_tables()
        logger.info("%d. %s" % (num, self.parsed_html))
        num += 1
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

        for content_name in META_CONTENT["XML"]:
            for static_xpath in META_CONTENT["XML"][content_name]:
                try:

                    meta_out[content_name] = self.parsed_xml.xpath(static_xpath)[0].text_content()
                    continue
                except IndexError:
                    pass
                except KeyError:
                    raise KeyError("You gave a malformed xpath call to HTMLElementTree: %s" % static_xpath)
                except Exception:
                    raise Exception(traceback.format_exc())

        return meta_out


EXTRACTOR_FACTORY = {
    "xml": StandardExtractorXML,
    "html": StandardExtractorHTML,
}



def extract_content(input_list):

    import json
    output_list = []

    ACCEPTED_FORMATS = ["xml", "html"]

    for dict_item in input_list:

        try:
            ExtractorClass = EXTRACTOR_FACTORY[dict_item[CONSTANTS['FILE_SOURCE']].lower().split(".")[-1]]
            Extractor = ExtractorClass(dict_item)
            parsed_content = Extractor.extract_multi_content()
            output_list.append(parsed_content)
        except KeyError:
            raise KeyError("You gave a format not currently supported for extraction",traceback.format_exc())
        except Exception:
            raise Exception(traceback.format_exc())
            #
            #
            # opened_XML = open_xml(dict_item[CONSTANTS['FILE_SOURCE']])
            # parsed_XML = parse_xml(opened_XML)
            # parsed_content = extract_multi_content(parsed_XML)

    return json.dumps(output_list)
    # raw_content = open_xml()

    # return json.dumps(message)