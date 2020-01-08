"""
StandardFileExtractor Worker Functions

Functions for the StandardFileExtractor worker. The sub classes implement
different extractors for different file types. Primarily; text, ocr, XML,
HTML, and HTTP. For information on the PDF extraction, look at the relevant
Java pipeline.

Credits: repository adsabs/adsdata by Jay Luke
"""


__author__ = 'J. Elliott'
__maintainer__ = ''
__copyright__ = 'Copyright 2015'
__version__ = '1.0'
__email__ = 'ads@cfa.harvard.edu'
__status__ = 'Production'
__credit__ = ['V. Sudilovsky', 'A. Accomazzi', 'J. Luker']
__license__ = 'GPLv3'

import sys
import os
import random
import string

from bs4 import UnicodeDammit
import lxml
import lxml.html
import lxml.etree
import lxml.objectify
import lxml.html.soupparser
import requests
from adsputils import load_config
from adsputils import overrides
from adsputils import setup_logging
from adsft.utils import TextCleaner, get_filenames
from adsft import reader
import re
import traceback
import unicodedata
from adsft import entitydefs as edef
from adsft.rules import META_CONTENT
from requests.exceptions import HTTPError
from subprocess import Popen, PIPE, STDOUT

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), '../'))
logger = setup_logging(__name__)


class StandardExtractorBasicText(object):
    """
    Class for extracting text from a text file. Essentialy used to clean the
    text rather than perform major extraction.
    Output is encoded in UTF-8.
    """

    def __init__(self, dict_item):
        """
        Initialisation funuction (constructor) of the class

        :param dict_item: dictionary containing meta-data of the article
        :return: no return
        """
        self.dict_item = dict_item
        self.raw_text = None
        self.parsed_text = None
        self.meta_name = 'txt'

    def open_text(self):
        """
        Opens the text file and reads the content

        :return: content of the file
        """

        with open(self.dict_item['ft_source'], 'r') as f:
            raw_text = f.read()

        self.raw_text = raw_text
        return self.raw_text

    def parse_text(self, translate=False, decode=False, normalise=True, trim=True):
        """
        Cleans the text:
          1. Translates: removes escape characters if ASCII or unicode
          2. Decode: decodes Python string to unicode type, assuming UTF-8
          3. Normalise: convert u" to u-umlaut

        :param translate: boolean, should it translate the text (see utils.py)
        :param decode: boolean, should it decode to UTF-8 (see utils.py)
        :param normalise: boolean, should it convert text, i.e., u" to u-umlaut
        (see utils.py)
        :return: the parsed/modified text
        """

        raw_text = self.raw_text
        raw_text = TextCleaner(text=raw_text).run(translate=translate,
                                                  decode=decode,
                                                  normalise=normalise,
                                                  trim=trim)

        self.parsed_text = raw_text
        return self.parsed_text

    def extract_multi_content(self, translate=True, decode=True):
        """
        Runs the functions to open, extract and clean the text of the given
        article. Returns the meta-data dictionary.

        :param translate: boolean, should it translate the text (see utils.py)
        :param decode: boolean, should it decode to UTF-8 (see utils.py)
        :return: dictionary containing up-to-date meta-data and full text
        """
        self.open_text()
        self.parse_text(translate=translate,
                        decode=decode)

        meta_out = {}
        meta_out['fulltext'] = self.parsed_text
        return meta_out


class StandardExtractorHTML(object):
    """
    Class for extracting text from an HTML file.
    Output is encoded in UTF-8.
    """

    def __init__(self, dict_item):
        """
        Initialisation funuction (constructor) of the class

        :param dict_item: dictionary containing meta-data of the article
        :return: no return
        """
        self.dict_item = dict_item
        self.file_input = self.dict_item['ft_source'].split(',')[0]
        self.raw_html = None
        self.parsed_html = None
        self.dictionary_of_tables = None
        self.meta_name = 'html'

    def open_html(self, in_html=False):
        """
        Opens the HTML file and encodes it in UTF-8. Converts any HTML entries
        to the correct UTF-8 hexadecimal numbers.

        :param in_html: HTML file to override the one given by the super class
        :return:
        """
        import codecs

        if not in_html:
            html_file = self.file_input
        else:
            html_file = in_html

        with codecs.open(html_file, 'r', 'utf-8') as f:
            raw_html = f.read()

        raw_html = edef.convertentities(raw_html)

        if not in_html:
            self.raw_html = raw_html

        return raw_html

    def parse_html(self, in_html=False):
        """
        Parses the HTML document imported. Currently, BeautifulSoup is used.

        :param in_html: HTML file to override the one given by the super class
        :return: the parsed content

        # Alternative used etree HTMLParser, but this requires an extra
        # two calls, one making it a StringIO, and then acquiring the root
        # element tree, but I don't see a difference?
        # parser = etree.HTMLParser()
        # tree = etree.parse(StringIO(html), parser)
        #
        # return tree.getroot()
        """

        if not in_html:
            parsed_html = lxml.html.document_fromstring(self.raw_html)
            self.parsed_html = parsed_html
        else:
            parsed_html = lxml.html.document_fromstring(in_html)

        logger.debug('Parsed HTML. {0}'.format(parsed_html))

        return parsed_html

    def collate_tables(self):
        """
        Used to match the tables listed within the HTML, by links, to full text
        extracted. The tables are defined in the table that contains the article
        link data.  This setup appears for A&A papers 2003-2011.

        :return: dictionary conotaining all of the related tables
        """
        table_source_files = re.split('\s*,\s*',
                                      self.dict_item['ft_source'])
        table_source_files.reverse()
        file_source = table_source_files.pop()

        dictionary_of_tables = {}
        for table_file_path in filter(lambda x: re.search('table', x),
                                      table_source_files):
            table_name = os.path.basename(table_file_path)

            table_raw_html = self.open_html(table_file_path)
            dictionary_of_tables[table_name] = self.parse_html(table_raw_html)

        self.dictionary_of_tables = dictionary_of_tables

        logger.debug('Collated {0} tables'.format(
            len(self.dictionary_of_tables)))

        return self.dictionary_of_tables

    def extract_multi_content(self, translate=False, decode=False):
        """
        Extracts the HTML content, and the content of all the tables mentioned
        in the HTML content, for the article given.

        :param translate: boolean, should it translate the text (see utils.py)
        :param decode: boolean, should it decode to UTF-8 (see utils.py)
        :return: dictionary of meta-data that includes the full text
        """

        self.open_html()
        self.parse_html()

        removed_content = None

        # Remove anything before introduction
        for xpath in META_CONTENT[self.meta_name]['introduction']:
            try:
                tmp = self.parsed_html.xpath(xpath)
                if tmp and len(tmp) > 0:
                    removed_content = tmp[0] # TODO(rca): only first elem?
                    break

            except Exception:
                print Exception(traceback.format_exc())

        if removed_content is None:
            logger.debug('Could not find intro for {0} (last xpath: {1})'
                         .format(self.dict_item['bibcode'], xpath))
        else:
            first_position_index = removed_content.getparent().index(
                removed_content)

            for element_tree_node in \
                    removed_content.getchildren()[:first_position_index]:

                element_tree_node.getparent().remove(element_tree_node)

        # Remove the references
        for xpath in META_CONTENT[self.meta_name]['references']:
            removed_content = None
            try:
                removed_content = self.parsed_html.xpath(xpath)[0]
                html_ul_element = removed_content.getnext()
                html_ul_element.getparent().remove(html_ul_element)
                removed_content.getparent().remove(removed_content)
                break

            except Exception:
                logger.debug('Could not find references for {0} (last xpath: '
                             '{1})'.format(self.dict_item['bibcode'],
                                           xpath))

        # Insert tables from external files
        first_parsed_html = self.parsed_html
        self.collate_tables()
        for table_name, table_root_node in self.dictionary_of_tables.items():

            table_node_to_insert = None
            logger.debug(
                'Attempting to find table contents: {0}'.format(table_name))

            for xpath in META_CONTENT[self.meta_name]['table']:

                try:
                    table_node_to_insert = \
                        table_root_node.xpath(xpath)[0].getparent()
                    break

                except AttributeError:
                    raise AttributeError('You used an incorrect method')

                except Exception:
                    raise Exception('Could not find table content for %s (last '
                                    'xpath: %s)'.format((table_name, xpath)))

            logger.debug(
                'Attempting to find table links: {0}'.format(table_name))

            for xpath in META_CONTENT[self.meta_name]['table_links']:
                try:
                    logger.debug(self.parsed_html)
                    table_nodes_in_file_source = self.parsed_html.xpath(
                        xpath.replace('TABLE_NAME', table_name))
                    break

                except AttributeError:
                    raise AttributeError('You used an incorrect method',
                                         traceback.format_exc(),
                                         table_name, self.parsed_html)

                except Exception:
                    raise Exception(
                        'Could not find table links for'
                        ' {0} (last xpath: {1})'.format(
                            table_name,
                            xpath.replace('TABLE_NAME', table_name)
                        ))

            logger.debug('Attempting to replace table at table links: {0}'
                         .format(table_name))

            if table_nodes_in_file_source:
                parent_node_of_table_link = \
                    table_nodes_in_file_source[0].getparent()

                parent_node_of_table_link.replace(table_nodes_in_file_source[0],
                                                  table_node_to_insert)
                [remaining_node.getparent().remove(remaining_node) for
                 remaining_node in table_nodes_in_file_source[1:]]
        try:
            for xpath in META_CONTENT[self.meta_name]['head']:
                try:
                    self.parsed_html.xpath(xpath)
                    break

                except Exception:
                    continue

        except Exception:
            pass

        string_of_all_html = u" ".join(map(unicode.strip, map(unicode,
            [individual_element_tree_node for individual_element_tree_node
             in self.parsed_html.itertext()
             if individual_element_tree_node
             and not individual_element_tree_node.isspace()])))

        string_of_all_html = TextCleaner(text=string_of_all_html).run(
            translate=translate,
            decode=decode,
            normalise=True,
            trim=True)

        meta_out = {'fulltext': string_of_all_html}

        return meta_out


class StandardExtractorXML(object):
    """
    Class for extracting text from an XML file.
    Output is encoded in UTF-8.
    """

    def __init__(self, dict_item):
        """
        Initialisation funuction (constructor) of the class

        :param dict_item: dictionary containing meta-data of the article
        :return: no return
        """
        self.dict_item = dict_item
        self.file_input = dict_item['ft_source']
        self.raw_xml = None
        self.parsed_xml = None
        self.meta_name = "xml"
        self.data_factory = {
            'string': self.extract_string,
            'list': self.extract_list,
        }
        self.preferred_parser_names = load_config().get('PREFERRED_XML_PARSER_NAMES')

    def open_xml(self):
        """
        Opens the XML file and reads raw string, uses UnicodeDammit to encode.

        Removes some text that has no relevance for XML files, such as HTML tags, LaTeX entities

        :return: XML string with converted HTML entities
        """
        raw_xml = None

        try:
            logger.debug('Opening the file: {0}'.format(self.file_input))

            with open(self.file_input, 'rb') as fp:
                raw_xml = fp.read()

            # detect the encoding of the xml file (Latin-1, UTF-8, etc.)
            encoding = UnicodeDammit(raw_xml).original_encoding

            # this encoding is then used to decode bytecode into unicode
            raw_xml = raw_xml.decode(encoding, "ignore")

            # converting the html entities needs be given a string in unicode,
            # otherwise you'll be mixing bytecode with unicode
            raw_xml = edef.convertentities(raw_xml)

            logger.debug('reading')
            logger.debug('Opened file, trying to massage the input.')

            logger.debug('XML file opened successfully')
            self.raw_xml = raw_xml

        except Exception as err:
            logger.error('Error: {0}'.format(err))
            raise Exception(err)

        return raw_xml

    def _remove_keeping_tail(self, element):
        """
        Safe the tail text and then delete the element. For instance, the element
        corresponding to the tag inline-formula for this case:
        <p>Head <inline-formula>formula</inline-formula> tail <italic>end</italic>.</p>
        will contain not only the tags but also the tail text until the next tag:
        '<inline-formula>formula</inline-formula> tail'
        To avoid losing the tail when removing the element, that text has to be
        copied to the previous or parent node.
        """
        self._preserve_tail_before_delete(element)
        element.getparent().remove(element)

    def _preserve_tail_before_delete(self, node):
        if node.tail: # preserve the tail
            previous = node.getprevious()
            if previous is not None: # if there is a previous sibling it will get the tail
                if previous.tail is None:
                    previous.tail = node.tail
                else:
                    previous.tail = previous.tail + node.tail
            else: # The parent get the tail as text
                parent = node.getparent()
                if parent.text is None:
                    parent.text = node.tail
                else:
                    parent.text = parent.text + node.tail

    def _append_tag_outside_parent(self, node):
        """
        move tag outside/after the parent tag so it is now a sibling
        """

        parent = node.getparent()

        if parent != None:
            parent.remove(node)
            parent.addnext(node)

    def _remove_special_elements(self, raw_xml, parser_name):
        """
        Remove character data (CDATA), comments and processing instructions
        using regex as needed for the target parser
        """
        if parser_name in ("lxml-xml", ):
            # These parsers will use the encoding specified in the content, we need to
            # replace encoding by UTF-8 since we already decoded the original file content
            raw_xml = re.sub('(<\?[^>]+encoding=")(?:[^"]*)("\?>)', '\g<1>UTF-8\g<2>', raw_xml)

        if parser_name in ("html5lib", "html.parser", "lxml-html", "direct-lxml-html", "lxml-xml", "direct-lxml-xml",):
            # replace <!-- body enbody --> with content inside
            # see issue https://github.com/adsabs/ADSfulltext/issues/104
            raw_xml = re.sub('<!--\s*body\s*([\s\S\n]*)\s*endbody\s*-->', r'\1', raw_xml)
        if parser_name in ("lxml-xml", "lxml-html", "html.parser", "html5lib"):
            # - A comment is coded like this: <!--  My comment goes here. and it can span multiple lines -->
            #   RegEx Source: https://stackoverflow.com/a/4616640/6940788
            raw_xml = re.sub('<!--[\s\S\n]*?-->', '', raw_xml) # Comments
        # - A CDATA is coded like this: <![CDATA[<b>Your Code Goes Here</b>]]>
        #   RegEx Source: https://superuser.com/a/1153242
        raw_xml = re.sub('<!\[CDATA\[.*?\]\]>', '', raw_xml) # CDATA
        # Notes:
        #   - no parser provides a reliable way to find CDATA and remove their content
        #     Source: https://stackoverflow.com/a/44561547
        if parser_name in ("lxml-html", "html.parser", "html5lib"):
            # - A processing instruction is coded like this: <?ignore .... what ever I want here, including <!-- comments --> ...  ?>
            #   RegEx Source: https://stackoverflow.com/a/29418829/6940788
            raw_xml = re.sub('<\?[^>]+\?>', '', raw_xml) # Processing instructions
        if parser_name in ("html5lib",):
            # - Convert self closing xml tags to closing tags
            #   Source: https://stackoverflow.com/a/14028108
            # - html5lib will close them itself (unless it is a recognised html
            #   tag) at a later point in the document, wrapping other content,
            #   and if it turns out to be a tag that we want to remove
            #   (i.e., graphics), we will wrongly remove the content that was
            #   wrapped
            raw_xml = re.sub('<\s*([^\s>]+)([^>]*)/\s*>', r'<\1\2></\1>', raw_xml) # Self closing tags (e.g., <graphics/>) to closing tabs (e.g., <graphics></graphics>)

        return raw_xml

    def _save_body_tag(self, raw_xml):
        # These parsers expect the document to be formatted:
        #   <html>
        #    <head></head>
        #    <body></body>
        #   </html>
        # If it is not the case, any body tag in a different position
        # is removed and they create the html and body tags surrounding
        # the whole content, thus we need to replace any body tag with
        # a random tag and we will recover it later on
        random_body_tag = None
        if "<body>" in raw_xml and "</body>" in raw_xml:
            counter = 10
            while counter > 0:
                random_body_tag = ''.join(random.choice(string.ascii_lowercase) for i in range(32))
                if random_body_tag not in raw_xml:
                    break
                counter -= 1
            if counter == 0:
                logger.error("Impossible to find a random body tag that does not exist in the file already after 10 attempts")
            else:
                raw_xml = raw_xml.replace("<body>", "<{}>".format(random_body_tag))
                raw_xml = raw_xml.replace("</body>", "</{}>".format(random_body_tag))
        return raw_xml, random_body_tag

    def _restore_body_tag(self, parsed_xml, random_body_tag):
        # Remove the html and body elements created by certain parsers
        # (due to the XML file not being a HTML one)
        html_body = parsed_xml.find("body")
        html_body.tag = "root"
        parsed_xml = html_body
        if random_body_tag:
            # Find the original body tag (if any) and rename it
            for e in parsed_xml.xpath("//{}".format(random_body_tag)):
                e.tag = "body"
        return parsed_xml

    def _remove_namespaces(self, parsed_xml):
        # Some parsers detect namespaces and expand the namespace prefixes
        # into their namespace:
        #
        #   nsmap = {   'mml':      'http://www.w3.org/1998/Math/MathML',
        #               'xlink':    'http://www.w3.org/1999/xlink',
        #               'xsi':      'http://www.w3.org/2001/XMLSchema-instance'}
        #
        # We want to remove namespaces from tags (e.g., "{http://www.tei-c.org/ns/1.0}TEI")
        # and attributes (e.g., "{http://www.w3.org/1999/xlink}href")
        #
        # Remove namespaces:
        for elem in parsed_xml.getiterator():
            # Attributes
            for key in elem.attrib.iterkeys():
                if not hasattr(key, 'find') or key[0] != '{':
                    continue
                i = key.find('}')
                if i > 0:
                    new_key = key[i+1:]
                    elem.attrib[new_key] = elem.attrib.pop(key)
            # Tag
            if not hasattr(elem.tag, 'find') or elem.tag[0] != '{':
                continue
            i = elem.tag.find('}')
            if i > 0:
                elem.tag = elem.tag[i+1:]
        # Get rid of 'py:pytype' and/or 'xsi:type' information and remove unused namespace declarations
        lxml.objectify.deannotate(parsed_xml, cleanup_namespaces=True)
        # Source: https://stackoverflow.com/a/18160164
        return parsed_xml

    def _remove_namespace_prefixes(self, parsed_xml):
        # Some parsers do not detect namespaces and the namespace prefixes
        # remain untouched in tags (e.g. <'ja:body'>) or attributes
        # (e.g., 'xlink:href')
        #
        # Remove prefixes:
        for elem in parsed_xml.getiterator():
            # Attributes
            for key in elem.attrib.iterkeys():
                if not hasattr(key, 'find'):
                    continue
                i = key.find(':')
                if i > 0:
                    new_key = key[i+1:]
                    elem.attrib[new_key] = elem.attrib.pop(key)
            # Tag
            if not hasattr(elem.tag, 'find'):
                continue
            i = elem.tag.find(':')
            if i > 0:
                elem.tag = elem.tag[i+1:]
        return parsed_xml

    def parse_xml(self, preferred_parser_names=None):
        """
        Parses the encoded string read from the opened XML file.
        Tries multiple parsers (sorted by order of preference), it stops trying
        the next parser the moment some fulltext is extracted.
        Removes tables, graphics, formulas, tex-math and CDATA.
        """

        if preferred_parser_names is None or \
            (isinstance(preferred_parser_names, (list, tuple)) and not isinstance(preferred_parser_names, basestring) and \
             (len(preferred_parser_names) == 0 or all(item is None for item in preferred_parser_names))):
            # If None or (None,), use the default from the config file
            preferred_parser_names = self.preferred_parser_names

        for parser_name in preferred_parser_names:
            parsed_xml = self._parse_xml(parser_name)
            logger.debug("Checking if the parser '{}' succeeded".format(parser_name))
            success = False
            for xpath in META_CONTENT[self.meta_name].get('fulltext', {}).get('xpath', []):
                fulltext = None
                fulltext_elements = parsed_xml.xpath(xpath)
                if len(fulltext_elements) > 0:
                    fulltext = u" ".join(map(unicode.strip, map(unicode, fulltext_elements[0].itertext())))
                    fulltext = TextCleaner(text=fulltext).run(decode=False, translate=True, normalise=True, trim=True)
                if not fulltext:
                    continue
                else:
                    logger.debug("The parser '{}' succeeded".format(parser_name))
                    success = True
                    break

            if not success:
                logger.debug("The parser '{}' failed".format(parser_name))
            else:
                break

        if not success:
            logger.warn('Parsing XML in non-standard way')
            parsed_xml = lxml.html.document_fromstring(self.raw_xml.encode('utf-8'))

        self.parsed_xml = parsed_xml
        return parsed_xml

    def _parse_xml(self, parser_name):
        """
        Parses the encoded string read from the opened XML file.
        Removes tables, graphics, formulas, tex-math and CDATA.

        Valid parser name options:

            parser_name = "direct-lxml-xml"
            parser_name = "direct-lxml-html"
            parser_name = "lxml-xml"
            parser_name = "lxml-html"
            parser_name = "html.parser"
            parser_name = "html5lib"

        :return: parsed XML file
        """
        raw_xml = self.raw_xml

        raw_xml = self._remove_special_elements(raw_xml, parser_name)
        if parser_name in ("direct-lxml-html", "lxml-html", "html5lib"):
            raw_xml, random_body_tag = self._save_body_tag(raw_xml)
        else:
            random_body_tag = None

        if parser_name in ("lxml-xml", "lxml-html", "html.parser", "html5lib"):
            # BeautifulSoup4 parsers:
            # - html.parser
            #    Advantages: Batteries included, Decent speed, Lenient (as of Python 2.7.3 and 3.2.)
            #    Disadvantages: Not very lenient (before Python 2.7.3 or 3.2.2)
            # - lxml-html / lxml-xml
            #    Advantages: Very fast, Lenient
            #    Disadvantages: External C dependency
            # - html5lib
            #    Advantages: Extremely lenient, Parses pages the same way a web browser does, Creates valid HTML5
            #    Disadvantages: Very slow, External Python dependency
            # Source: https://stackoverflow.com/a/45494776/6940788
            #
            # Note: lxml package has a soupparser module that relies on BeautifulSoup,
            # which in turn can be instructed to use lxml-html/xml parser or others
            #
            parsed_xml = lxml.html.soupparser.fromstring(raw_xml, features=parser_name)
        else:
            # lxml parsers (BeautifulSoup4 not needed) with our custom options:
            # - XMLParser
            # - HTMLParser
            if parser_name == "direct-lxml-xml":
                parser = lxml.etree.XMLParser(ns_clean=True, recover=True, remove_blank_text=True, remove_comments=True, remove_pis=True, \
                                         strip_cdata=True, resolve_entities=True, encoding="UTF-8")
                parsed_xml = lxml.etree.XML(raw_xml.encode('utf-8'), parser=parser)
            elif parser_name == "direct-lxml-html":
                parser = lxml.etree.HTMLParser(recover=True, no_network=True, remove_blank_text=True, remove_comments=True, remove_pis=True, \
                                          strip_cdata=True, default_doctype=False, encoding="UTF-8")
                parsed_xml = lxml.etree.HTML(raw_xml.encode('utf-8'), parser=parser)
            else:
                raise Exception("Unknown parser: {}".format(parser_name))

        if parser_name in ("lxml-html", "html5lib", "direct-lxml-html"):
            # Remove the html and body elements created by these parsers
            # and restore the original body tag
            parsed_xml = self._restore_body_tag(parsed_xml, random_body_tag)

        if parser_name in ("lxml-xml", "direct-lxml-xml") and parsed_xml.nsmap:
            # These parsers detect namespaces and expand the namespace prefixes
            # into their namespace, we need to remove them to make xpath work
            # without having to specify the namespaces
            parsed_xml = self._remove_namespaces(parsed_xml)

        if parser_name in ("lxml-html", "html.parser", "html5lib"):
            # These parsers do not detect namespaces and the namespace prefixes
            # remain untouched in tags (e.g. <'ja:body'>) or attributes
            # (e.g., 'xlink:href'), we need to remove them to make xpath work
            # without having to specify the namespace prefixes
            parsed_xml = self._remove_namespace_prefixes(parsed_xml)

        # remove tables, formulas, figures and bibliography
        for e in parsed_xml.xpath("//table | //graphic | //disp-formula | ////inline-formula | //formula | //tex-math | //processing-instruction('CDATA') | //bibliography"):
            self._remove_keeping_tail(e)

        # move acknowledgments after body (most likely only a minority of documents have this problem)
        for e in parsed_xml.xpath(" | ".join(META_CONTENT['xml']['acknowledgements']['xpath'])):
            self._append_tag_outside_parent(e)

        return parsed_xml

    def extract_string(self, static_xpath, **kwargs):
        """
        Extracts the first matching string requested from the given xpath
        :param static_xpath: XPATH to be searched
        :param kwargs: decode and translate
        :return:
        """

        text_content = ''

        if 'decode' in kwargs:
            decode = kwargs['decode']
        else:
            decode = False

        if 'translate' in kwargs:
            translate = kwargs['translate']
        else:
            translate = False

        s = self.parsed_xml.xpath(static_xpath)

        if s:
            text_content = u" ".join(map(unicode.strip, map(unicode, s[0].itertext())))
        old = text_content
        text_content = TextCleaner(text=text_content).run(
            decode=decode,
            translate=translate,
            normalise=True,
            trim=True)

        return text_content

    def extract_list(self, static_xpath, **kwargs):
        """
        Extracts the first matching string requested from the given xpath, but
        then returns the list of content. This function also extracts the href
        within the span rather than the list of strings. When a list of strings
        is required, then that function can be added to the data factory.

        :param static_xpath: XPATH to be searched
        :param kwargs: "info" name of the content wanted from the span,
        "decode", and "translate.
        :return:
        """

        if 'decode' in kwargs:
            decode = kwargs['decode']
        else:
            decode = False

        if 'translate' in kwargs:
            translate = kwargs['translate']
        else:
            translate = False

        data_inner = []
        try:
            span_content = kwargs['info']
        except KeyError:
            logger.error('You did not supply the info kwarg,'
                         ' returning an empty list')
            return data_inner

        text_content = self.parsed_xml.xpath(static_xpath)

        for span in text_content:
            try:
                text_content = span.attrib.get(span_content)
                if text_content is None and ":" in span_content:
                    # Certain parsers will expand the namespace_prefix:name of
                    # tags/attributes to namespace:name (e.g., {http://www.w3.org/1999/xlink}href)
                    # while others will keep the prefix (e.g., xlink:href)
                    # Our processing removes the namespace expansion and the
                    # prefix (e.g., href), thus, if the attribute name in the ruls
                    # contains a namespace prefix, we need to remove it:
                    vspan_content = span_content.split(":")
                    if len(vspan_content) >= 2:
                        ns = vspan_content[0]
                        name = ":".join(vspan_content[1:])
                        text_content = span.attrib.get(name)
                text_content = TextCleaner(text=text_content).run(
                    decode=decode,
                    translate=translate,
                    normalise=True,
                    trim=True)

                data_inner.append(text_content)
            except KeyError:
                logger.debug('Content of type {0} not found in this span'
                             .format(span_content))
                pass
            except Exception:
                logger.error('Unexpected error, skipping')

        return data_inner

    def extract_multi_content(self, translate=False, decode=False, preferred_parser_names=None):
        """
        Extracts full text content from the XML article specified. It also
        extracts any content specified in settings.py. It expects that the user
        gives the XPATH and the meta-data name to use for the component wished
        to be extracted.

        :param translate: boolean, should it translate the text (see utils.py)
        :param decode: boolean, should it decode to UTF-8 (see utils.py)
        :return: updated meta-data containing the full text and other user
        specified content
        """

        if preferred_parser_names is None or \
            (isinstance(preferred_parser_names, (list, tuple)) and not isinstance(preferred_parser_names, basestring) and \
             (len(preferred_parser_names) == 0 or all(item is None for item in preferred_parser_names))):
            # If None or (None,), use the default from the config file
            preferred_parser_names = self.preferred_parser_names

        meta_out = {}
        self.open_xml()
        self.parse_xml(preferred_parser_names=preferred_parser_names)
        logger.debug('{0}: Extracting: {0}'.format(self.meta_name,
                                                   self.file_input))

        for content_name in META_CONTENT[self.meta_name]:
            logger.debug('Trying meta content: {0}'.format(content_name))

            all_text_content = []
            unique = True

            for static_xpath \
                    in META_CONTENT[self.meta_name][content_name]['xpath']:

                logger.debug(META_CONTENT[self.meta_name][content_name])
                logger.debug('Trying xpath: {0}'.format(static_xpath))
                try:
                    # logger.debug(self.parsed_xml.text_content())
                    # This returns a unicode-like type

                    extractor_required = \
                        META_CONTENT[self.meta_name][content_name]['type']

                    extractor_info = \
                        META_CONTENT[self.meta_name][content_name]['info']

                    logger.debug('Loaded type: {0}, and info:'
                                 .format(extractor_required, extractor_info))

                    extractor_type = self.data_factory[extractor_required]

                    text_content = extractor_type(
                        static_xpath,
                        info=extractor_info,
                        decode=decode,
                        translate=translate,
                    )

                    if text_content:
                        # this is to deal with situations where the appendix is found inside of the body tags
                        # or when multiple xpaths return the same result which happens in some cases for the acknowledgments
                        for s in all_text_content:
                            if text_content in s:
                                unique = False

                        if unique:
                            all_text_content.append(text_content)
                        else:
                            continue
                    else:
                        continue

                    logger.debug('Successful.')

                except IndexError:
                    logger.debug('Index error for: {0}'.format(self.dict_item[
                        'bibcode']))
                    pass

                except KeyError:
                    logger.error('Dictionary key error for: {0} [{1}]'.format(
                        self.dict_item['bibcode'],
                        META_CONTENT[self.meta_name][content_name]
                    ))
                    raise KeyError(
                        'You gave a malformed xpath to HTMLElementTree: {0}'
                        .format(static_xpath))

                except Exception:
                    logger.error('Unknown error for: {0} [{1}]'
                                 .format(self.dict_item['bibcode'],
                                         traceback.format_exc()
                                         )
                                 )
                    raise Exception(traceback.format_exc())

            if META_CONTENT[self.meta_name][content_name]['type'] == 'string':
                meta_out[content_name] = "\n".join(all_text_content)
            elif len(all_text_content) > 0:
                meta_out[content_name] = all_text_content[0]

        return meta_out


class StandardExtractorTEIXML(StandardExtractorXML):
    """
    Class for parsing TEI XML as output from Grobid.
    Right now it's just a stub.
    See: http://grobid.readthedocs.org/en/latest/
    """

    def __init__(self, dict_item):
        StandardExtractorXML.__init__(self, dict_item)
        self.meta_name = 'teixml'



class StandardElsevierExtractorXML(StandardExtractorXML):
    """
    Class for extracting text from an Elsevier XML file. This is used instead of
    the standard class, as Elsevier can use name spaces within their XML files,
    which can break the standard extraction using BeautifulSoup. It also means
    XPATHs have to be formatted differently to handle extraction.
    Output is encoded in UTF-8.
    """

    def __init__(self, dict_item):
        """
        Initialisation funuction (constructor) of the class. Uses the
        superclass.

        :param dict_item: dictionary containing meta-data of the article
        :return: no return
        """
        StandardExtractorXML.__init__(self, dict_item)
        self.meta_name = 'xmlelsevier'



class StandardExtractorHTTP(StandardExtractorBasicText):
    """
    Class for extracting text from a document that is on a web server. There is
    currently no use case, but the code is implemented and tested. It inherits
    from the StandardExtractorBasicText for the parsing and cleaning of the
    content.
    Output is encoded in UTF-8.
    """

    def __init__(self, dict_item):
        """
        Initialisation funuction (constructor) of the class. Uses the
        superclass.

        :param dict_item: dictionary containing meta-data of the article
        :return: no return
        """
        StandardExtractorBasicText.__init__(self, dict_item)
        self.dict_item = dict_item
        self.meta_name = 'http'
        self.raw_text = None
        self.parsed_text = None
        self.request_headers = {'User-Agent': 'ADSClient',
                                'Accept': 'text/plain', }

        try:
            prev_time_stamp = self.dict_item['PREVIOUS_TIME_STAMP'] #TODO(rca): this mysterious constant cannot be found (on live or codebase); it seems like it was silently failing forever..
            last_modified = prev_time_stamp.strftime('%a, %d %b %Y %H:%M:%S %Z')
            self.request_headers['If-Modified-Since'] = last_modified

        except KeyError:
            pass

    def open_http(self):
        """
        Communicates with the web server to request the content. Returns the
        content if there is a 200 response, otherwise it does not.

        :return: the raw content received from the web server
        """

        import requests

        response = requests.get(self.dict_item['ft_source'],
                                headers=self.request_headers)

        if response.status_code != 200:
            raise HTTPError(
                'Status code not 200: {0}'.format(response.status_code)
            )

        self.raw_text = response.text

        return self.raw_text

    def parse_http(self, translate=True, decode=True):
        """
        Parses the web server content using the one inherited from the
        StandardExtractorBasicText class

        :param translate: boolean, should it translate the text (see utils.py)
        :param decode: boolean, should it decode to UTF-8 (see utils.py)
        :return: parsed and cleaned content
        """

        self.parsed_http = self.parse_text(translate=translate, decode=decode)
        return self.parsed_http

    @overrides(StandardExtractorBasicText)
    def extract_multi_content(self, translate=True, decode=True):
        """
        Opens and extracts the content from the web server. Pares and returns
        the meta-data content including the full text

        This is currently turned off given there is no use case. It would also
        be useful to include an integration test that implements HTTPretty.

        :param translate: boolean, should it translate the text (see utils.py)
        :param decode: boolean, should it decode to UTF-8 (see utils.py)
        :return: no return
        """
        pass

    def extract_multi_content(self, translate=True, decode=True):
        """
        Opens and extracts the content from the web server. Pares and returns
        the meta-data content including the full text

        :param translate: boolean, should it translate the text (see utils.py)
        :param decode: boolean, should it decode to UTF-8 (see utils.py)
        :return: no return
        """
        self.open_http()
        self.parse_http(translate=translate, decode=decode)
        self.parsed_http = TextCleaner(text=self.parsed_http).run(
            translate=translate,
            decode=decode,
            normalise=True,
            trim=True)
        meta_out = {}
        meta_out['fulltext'] = self.parsed_http
        return meta_out


class PDFExtractor(object):
    def __init__(self, kwargs):
        self.ft_source = kwargs.get('ft_source', None)
        self.bibcode = kwargs.get('bibcode', None)
        self.provider = kwargs.get('provider', None)
        self.extract_pdf_script = proj_home + kwargs.get('extract_pdf_script', '/scripts/extract_pdf_with_pdftotext.sh')

        if not self.ft_source:
            raise Exception('Missing or non-existent source: %s', self.ft_source)

    def extract_multi_content(self, translate=False, decode=True):
        p = Popen([self.extract_pdf_script, self.ft_source], stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise Exception(stderr)
        fulltext = TextCleaner(text=stdout).run(translate=translate,
                                          decode=decode,
                                          normalise=True,
                                          trim=True)
        return  {
                    'fulltext': fulltext,
                }

class GrobidPDFExtractor(object):
    def __init__(self, kwargs):
        self.ft_source = kwargs.get('ft_source', None)
        self.bibcode = kwargs.get('bibcode', None)
        self.provider = kwargs.get('provider', None)
        self.timeout = 120 # seconds
        self.grobid_service = kwargs.get('grobid_service', None)

        if not self.ft_source:
            raise Exception('Missing or non-existent source: %s', self.ft_source)

    def extract_multi_content(self, translate=False, decode=True):
        grobid_xml = ""
        if self.grobid_service is not None:
            try:
                with open(self.ft_source, 'r') as f:
                    logger.debug("Contacting grobid service: %s", self.grobid_service)
                    response = requests.post(url=self.grobid_service, files={'input': f}, timeout=self.timeout)
            except IOError, error:
                logger.exception("Error opening file %s: %s", self.ft_source, error)
            except requests.exceptions.Timeout:
                logger.exception("Grobid service timeout after %d seconds", self.timeout)
            except:
                logger.exception("Grobid request exception")
            else:
                if response.status_code == 200:
                    logger.debug("Successful response from grobid server (%d bytes)", len(response.content))
                    logger.debug("Successful response from grobid server: %s", response.content)
                    grobid_xml = response.text
                else:
                    logger.error("Grobid service response error (code %s): %s", response.status_code, response.text)
        else:
            logger.debug("Grobid service not defined")
        grobid_xml = TextCleaner(text=grobid_xml).run(translate=translate,
                                          decode=decode,
                                          normalise=True,
                                          trim=True)

        return  {
                    'fulltext': grobid_xml,
                }

# Dictionary containing the relevant extensions for the relevant class

EXTRACTOR_FACTORY = {
    "xml": StandardExtractorXML,
    "html": StandardExtractorHTML,
    "txt": StandardExtractorBasicText,
    "ocr": StandardExtractorBasicText,
    "elsevier": StandardElsevierExtractorXML,
    "teixml": StandardExtractorTEIXML,
    "http": StandardExtractorHTTP,
    "pdf": PDFExtractor,
    "pdf-grobid": GrobidPDFExtractor
}


def extract_content(input_list, **kwargs):
    """
    accept a list of dictionaries that contain the relevant meta-data for an
    article. It matches the type of file to the correct extractor type, and then
    extracts the full text content and anything else relevant, e.g.,
    acknowledgements, and dataset IDs (that are defined by the user in
    settings.py).

    :param input_list: dictionaries that contain meta-data of articles
    :param kwargs: used to store grobid service URL
    :return: json formatted list of dictionaries now containing full text
    """

    import json

    output_list = []

    ACCEPTED_FORMATS = ['xml', 'teixml', 'html', 'txt', 'ocr', 'http', 'pdf', 'pdf-grobid']

    for dict_item in input_list:

        recovered_content = None
        if 'UPDATE' in dict_item and dict_item['UPDATE'] == 'FORCE_TO_SEND':
            # Read previously extracted data
            recovered_content = reader.read_content(dict_item)

        if recovered_content is not None and recovered_content['fulltext'] != "":
            for key, value in recovered_content.iteritems():
                if key != 'UPDATE':
                    dict_item[key] = value
            output_list.append(dict_item)
        else:
            try:
                extension = dict_item['file_format']
                if extension not in ACCEPTED_FORMATS:
                    raise KeyError('You gave an unsupported file extension.')

                if extension == 'xml' \
                        and dict_item['provider'] == 'Elsevier':

                    extension = "elsevier"
                ExtractorClass = EXTRACTOR_FACTORY[extension]

            except KeyError:
                msg = "Article '{}' has a format not currently supported for extraction: {}".format(dict_item['bibcode'], dict_item['file_format'])
                logger.exception(msg)
                raise KeyError(msg, traceback.format_exc())

            try:
                dict_item['grobid_service'] = kwargs.get('grobid_service', None)
                dict_item['extract_pdf_script'] = kwargs.get('extract_pdf_script', None)
                # get one or more files from ft_source and process
                files = get_filenames(dict_item['ft_source'])
                for f in files:
                    dict_item['ft_source'] = f
                    extractor = ExtractorClass(dict_item)
                    parsed_content = extractor.extract_multi_content()

                    for item in parsed_content:
                        if item in dict_item:
                            # values can be strings or, for dataset, a list
                            if isinstance(dict_item[item], str):
                                dict_item[item] += ' ' + parsed_content[item]
                            else:
                                dict_item[item] += parsed_content[item]
                        else:
                            dict_item[item] = parsed_content[item]

                del dict_item['grobid_service']
                del dict_item['extract_pdf_script']

                output_list.append(dict_item)

            except Exception:
                logger.exception("Fulltext extraction failed for bibcode '{}': '{}'".format(dict_item['bibcode'], dict_item['ft_source']))
                raise Exception(traceback.format_exc())

            del extractor, parsed_content

    return output_list
