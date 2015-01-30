"""
StandardFileExtractor Worker Functions

These are the functions for the StandardFileExtractor class. This worker should be able to extract the contents of all
document types, excluding PDF. A lot of the source code has been ported from adsabs/adsdata
"""

import json
import re
from lxml.html import soupparser
from lib import entitydefs as edef


def open_xml(file_input):

    raw_xml = None

    with open(file_input, 'r') as f:
        raw_xml = f.read()
        raw_xml = re.sub('(<!-- body|endbody -->)', '', raw_xml)
        raw_xml = edef.convertentities(raw_xml.decode('utf-8', 'ignore'))
        raw_xml = re.sub('<\?CDATA.+?\?>', '', raw_xml)

    return raw_xml


def parse_xml(file_input):

    parsed_content = soupparser.fromstring(file_input.encode('utf-8'))

    # strip out the latex stuff (for now)
    for e in parsed_content.xpath('//inline-formula'):
        e.getparent().remove(e)

    return parsed_content


def extract_body(parsed_xml):

    for xpath in ['//body','//section[@type="body"]', '//journalarticle-body']:
        try:
            return parsed_xml.xpath(xpath)[0].text_content()
        except IndexError:
            pass
        except:
            raise KeyError


def extract_multi_content(parsed_xml):

    from settings import META_CONTENT

    meta_out = {}

    for content_name in META_CONTENT["XML"]:
        for static_xpath in META_CONTENT["XML"][content_name]:
            try:
                meta_out[content_name] = parsed_xml.xpath(static_xpath)[0].text_content()
                continue
            except IndexError:
                pass
            except:
                raise KeyError("You gave a malformed xpath call to HTMLElementTree: %s" % static_xpath)

    return meta_out

def extract_content(json_list):

    return 1
    # raw_content = open_xml()

    # return json.dumps(message)