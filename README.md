[![Build Status](https://travis-ci.org/adsabs/ADSfulltext.svg)](https://travis-ci.org/adsabs/ADSfulltext)
[![Coverage Status](https://coveralls.io/repos/adsabs/ADSfulltext/badge.svg)](https://coveralls.io/r/adsabs/ADSfulltext)

# ADSfulltext

Article full text extraction pipeline. Set of workers that check the filesystem and convert
binary files into text.

## Purpose

To extract text from the source files of our articles, which may be in any of the listed formats:
- PDF
- XML (often malformed)
- OCR
- HTML
- TXT

The extracted text then gets sent to SOLR to be indexed.  

## Text Extraction
The main file for this pipeline is `extraction.py`. This file takes a message (in the form of a dictionary) containing the bibcode, directory of the source file to be extracted, file format, and provider/publisher. This information determines which parser will be used to extract the contents, for example this message:

    m = {
      'bibcode': '2019arXiv190105463B',
      'ft_source': /some/directory/file.xml,
      'file_format': 'xml',
      'provider': 'Elsevier'
    }

would use the Elsevier XML parser because XML files from that publisher need to be extracted using different methods than regular XML files. In this case Elsevier requires the use of `lxml.html.document_fromstring()` instead of `lxml.html.soupparser.fromstring()`.

#### XML Files

We utilize the lxml.html library to extract content from our XML files.

#### PDF Files

Our PDF extractor is mainly composed of of the pdfminer tool pdf2txt. We are exploring other options such a GROBID to find if we can improve the performance of this extractor, but as of right now pdf2txt is our best option. The main downfall of pdf2txt is that it does not allow for easy extraction of things like figures, formulas and tables which are known to produce useless strings and garbage. Some documentation on the journey to improve other parsers to outperform pdf2txt can be found [here](https://docs.google.com/document/d/1gt8bwO86ZQ9NV_h54IPm7lHeuh78CyeQK1orLPS43GM/edit?usp=sharing).

## Time-Capsule

If you stop here, oh tired traveller, please don't judge us too harshly, mere mortals. We tried to simplify the chaos we didn't create. Blame the universe for its affinity for chaos.
