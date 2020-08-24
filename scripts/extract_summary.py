"""
Extracts a list of summaries from AAS XML publications.
Used to provide data to Chandra (Sherry Winkelman) and 
NASA OCIO (Brian Thomas).
Requires a table of bibcode, file, provider in stdin.

Run as: 
   look -f 2016ApJ...828...53H /proj/ads/abstracts/config/links/fulltext/all.links | /proj/adsx/python/bin/python ./extract_summary.py

AA 10/4/2016
"""
from __future__ import print_function

import sys
from builtins import str
import json
import fileinput
import traceback
import codecs
from adsft import extraction
from adsft.utils import TextCleaner

# appears to be the last <sec> element in the <body> section
sections_xpath = '//body/sec'
paragraphs_xpath = '//body/p'

def process_one_file(bibcode, fname, provider):
    ext = fname.split('.')[-1]
    d = { 'bibcode': bibcode,
          'provider': provider,
          'file_format': ext,
          'ft_source': fname }
    extractor = extraction.StandardExtractorXML(d)
    extractor.open_xml()
    xml = extractor.parse_xml()
    sections = xml.xpath(sections_xpath) or xml.xpath(paragraphs_xpath)
    summary = sections[-1].text_content()
    sys.stderr.write("summary is of type {}\n".format(type(summary)))
    text = TextCleaner(text=summary)
    if sections:
        if sys.version_info > (3,):
            test_type = str
        else:
            test_type = unicode
        summary = test_type(sections[-1].text_content())
    if summary:
        text = TextCleaner(text=summary).run()
    return text

if __name__ == '__main__':

    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr)
    for line in fileinput.input():
        bibcode, fname, provider = line.strip().split()
        summary = None
        try: 
            summary = process_one_file(bibcode, fname, provider)
        except KeyboardInterrupt:
            pass
        except Exception as desc:
            traceback.print_exc()
            sys.stderr.write("error extracting summary for {}\n".format(bibcode))
        if summary:
            print(u"%R {}\n{}\n".format(bibcode, summary.strip()))
