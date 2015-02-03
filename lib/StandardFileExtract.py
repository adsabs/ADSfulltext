"""
StandardFileExtractor Worker Functions

These are the functions for the StandardFileExtractor class. This worker should be able to extract the contents of all
document types, excluding PDF. A lot of the source code has been ported from adsabs/adsdata
"""

import json
import re
import traceback
from lxml import etree
from lxml.html import soupparser
from lib import entitydefs as edef
from StringIO import StringIO

from settings import CONSTANTS, META_CONTENT


class StandardExtractorHTML(object):

    def __init__(self, dict_item):

        self.file_input = dict_item[CONSTANTS['FILE_SOURCE']]
        self.raw_html = None

    def open_html(self):
        import codecs
        with codecs.open(self.file_input, 'r', 'utf-8') as f:
            raw_html = f.read()

        # raw_html = raw_html.decode('utf-8', 'ignore')
        raw_html = edef.convertentities(raw_html)

        self.raw_html = raw_html
        return raw_html
        # parser = etree.HTMLParser()
        # tree = etree.parse(StringIO(html), parser)
        #
        # return tree.getroot()



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