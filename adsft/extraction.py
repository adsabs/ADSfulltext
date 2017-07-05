"""
StandardFileExtractor Worker Functions

Functions for the StandardFileExtractor worker. The sub classes implement
different extractors for different file types. Primarily; text, ocr, XML,
HTML, and HTTP. For information on the PDF extraction, look at the relevant
Java pipeline.

Credits: repository adsabs/adsdata by Jay Luke
"""

__author__ = 'J. Elliott'
__maintainer__ = 'J. Elliott'
__copyright__ = 'Copyright 2015'
__version__ = '1.0'
__email__ = 'ads@cfa.harvard.edu'
__status__ = 'Production'
__credit__ = ['V. Sudilovsky', 'A. Accomazzi', 'J. Luker']
__license__ = 'GPLv3'

import sys
import os

from adsputils import setup_logging, overrides, load_config
from adsft.utils import TextCleaner
import re
import traceback
import unicodedata
from lxml.html import soupparser, document_fromstring, fromstring
from adsft import entitydefs as edef
from adsft.rules import META_CONTENT
from requests.exceptions import HTTPError
from subprocess import Popen, PIPE, STDOUT

proj_home = load_config()['PROJ_HOME']
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

    def parse_text(self, translate=False, decode=False, normalise=True):
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
                                                  normalise=True)

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
            parsed_html = document_fromstring(self.raw_html)
            self.parsed_html = parsed_html
        else:
            parsed_html = document_fromstring(in_html)

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

        string_of_all_html = " ".join(
            [individual_element_tree_node for individual_element_tree_node
             in self.parsed_html.itertext()
             if individual_element_tree_node
             and not individual_element_tree_node.isspace()])

        string_of_all_html = TextCleaner(text=string_of_all_html).run(
            translate=translate,
            decode=decode,
            normalise=True)

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

    def open_xml(self):
        """
        Opens the XML file and encodes it into UTF-8. Removes some text that
        has no relevance for XML files, such as HTML tags.

        :return: semi-parsed XML content
        """
        raw_xml = None

        try:
            logger.debug('Opening the file: {0}'.format(self.file_input))

            import codecs

            with codecs.open(self.file_input, 'r', encoding='utf-8') as f:
                raw_xml = f.read()

            logger.debug('reading')
            logger.debug('Opened file, trying to massage the input.')
            raw_xml = re.sub('(<!-- body|endbody -->)', '', raw_xml)
            raw_xml = edef.convertentities(raw_xml)
            raw_xml = re.sub('<\?CDATA.+?\?>', '', raw_xml)
            logger.debug('XML file opened successfully')
            self.raw_xml = raw_xml

        except Exception as err:
            logger.error('Error: {0}'.format(err))
            raise Exception(err)

        return raw_xml

    def parse_xml(self):
        """
        Parses the opened XML file. Removes inline formula from each XML node.

        :return: parsed XML file
        """

        parsed_content = soupparser.fromstring(self.raw_xml)

        # strip out the latex stuff (for now)
        for e in parsed_content.xpath('//inline-formula'):
            e.getparent().remove(e)

        self.parsed_xml = parsed_content
        return parsed_content

    def extract_string(self, static_xpath, **kwargs):
        """
        Extracts the first matching string requested from the given xpath
        :param static_xpath: XPATH to be searched
        :param kwargs: decode and translate
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

        text_content = self.parsed_xml.xpath(static_xpath)[0].text_content()
        text_content = TextCleaner(text=text_content).run(
            decode=decode,
            translate=translate,
            normalise=True)

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
                text_content = TextCleaner(text=text_content).run(
                    decode=decode,
                    translate=translate,
                    normalise=True)

                data_inner.append(text_content)
            except KeyError:
                logger.debug('Content of type {0} not found in this span'
                             .format(span_content))
                pass
            except Exception:
                logger.error('Unexpected error, skipping')

        return data_inner

    def extract_multi_content(self, translate=False, decode=False):
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

        meta_out = {}
        self.open_xml()
        self.parse_xml()
        logger.debug('{0}: Extracting: {0}'.format(self.meta_name,
                                                   self.file_input))

        for content_name in META_CONTENT[self.meta_name]:
            logger.debug('Trying meta content: {0}'.format(content_name))

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
                        meta_out[content_name] = text_content
                    else:
                        continue

                    logger.debug('Successful.')
                    break

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

    def parse_xml(self):
        """
        Parses the XML file using BeautifulSoup, using the super class. A quick
        check if normal XPATH extraction works is carried out. If this fails, it
        uses an alternative method to extract the content.

        :return: opened and parsed XML content
        """
        try:
            logger.debug('Parsing EXML with soupparser')
            self.parsed_xml = super(StandardElsevierExtractorXML,
                                    self).parse_xml()
            logger.debug('Checking soupparser handled itself correctly')
            check = self.parsed_xml.xpath('//body')[0].text_content()
            # this may be better? //named-content[@content-type="dataset"]

        except:
            logger.debug('Parsing EXML in non-standard way')
            self.parsed_xml = document_fromstring(self.raw_xml)

        return self.parsed_xml

    @overrides(StandardExtractorXML)
    def extract_multi_content(self, translate=False, decode=False):
        """
        Opens and extracts the content of the Elseiver article given. Currently,
        there is no altnerative way to carry out the multi-content extraction,
        but the override is in place in case something different is needed.

        :param translate: boolean, should it translate the text (see utils.py)
        :param decode: boolean, should it decode to UTF-8 (see utils.py)
        :return: updated meta-data containing the full text and other user
        specified content
        """

        content = super(StandardElsevierExtractorXML,
                        self).extract_multi_content(translate=translate,
                                                    decode=decode)
        return content


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
            normalise=True)
        meta_out = {}
        meta_out['fulltext'] = self.parsed_http
        return meta_out


class PDFBoxExtractor(object):
    def __init__(self, kwargs):
        self.ft_source = kwargs.get('ft_source', None)
        self.bibcode = kwargs.get('bibcode', None)
        self.provider = kwargs.get('provider', None)
        self.cmd = kwargs.get('executable', proj_home + '/scripts/extract_pdf.sh') #TODO(rca) make it configurable
        
        if not self.ft_source:
            raise Exception('Missing or non-existent source: %s', self.ft_source)
        
    def extract_multi_content(self):
        p = Popen([self.cmd, self.ft_source], stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise Exception(stderr)
        return {'fulltext': stdout}
    
# Dictionary containing the relevant extensions for the relevant class

EXTRACTOR_FACTORY = {
    "xml": StandardExtractorXML,
    "html": StandardExtractorHTML,
    "txt": StandardExtractorBasicText,
    "ocr": StandardExtractorBasicText,
    "elsevier": StandardElsevierExtractorXML,
    "teixml": StandardExtractorTEIXML,
    "http": StandardExtractorHTTP,
    "pdf": PDFBoxExtractor
}


def extract_content(input_list, **kwargs):
    """
    accept a list of dictionaries that contain the relevant meta-data for an
    article. It matches the type of file to the correct extractor type, and then
    extracts the full text content and anything else relevant, e.g.,
    acknowledgements, and dataset IDs (that are defined by the user in
    settings.py).

    :param input_list: dictionaries that contain meta-data of articles
    :param kwargs: currently not used
    :return: json formatted list of dictionaries now containing full text
    """

    import json

    output_list = []

    ACCEPTED_FORMATS = ['xml', 'teixml', 'html', 'txt', 'ocr', 'http', 'pdf']

    for dict_item in input_list:

        try:
            extension = dict_item['file_format']
            if extension not in ACCEPTED_FORMATS:
                raise KeyError('You gave an unsupported file extension.')

            if extension == 'xml' \
                    and dict_item['provider'] == 'Elsevier':

                extension = "elsevier"

            ExtractorClass = EXTRACTOR_FACTORY[extension]

        except KeyError:
            raise KeyError(
                'You gave a format not currently supported for extraction: {0}'
                .format(dict_item['file_format'], traceback.format_exc()))

        try:
            extractor = ExtractorClass(dict_item)
            parsed_content = extractor.extract_multi_content()

            for item in parsed_content:
                dict_item[item] = parsed_content[item]

            output_list.append(dict_item)

        except Exception:
            raise Exception(traceback.format_exc())

        del extractor, parsed_content

    return output_list
