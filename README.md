[![Build Status](https://travis-ci.org/adsabs/ADSfulltext.svg)](https://travis-ci.org/adsabs/ADSfulltext)
[![Coverage Status](https://coveralls.io/repos/adsabs/ADSfulltext/badge.svg)](https://coveralls.io/r/adsabs/ADSfulltext)

# ADSfulltext

Article full text extraction pipeline. Set of workers that check the filesystem and convert
binary files into text.

##### What does the pipeline extract?
- body
    - includes table and figure captions, appendixes and supplements
- acknowledgements
- any dataset(s)
- any facilities

We do not include the list of references because those are processed separately by the reference resolver to generate citations.

##### Where does this data go?
All of these fields are sent to ADSMasterPipeline, and all fields except the dataset are sent to Solr. Each bibcode has a fulltext.txt and meta.json file in the live folder in a directory constructed from the actual bibcode.

Facilties and datasets are not in use by any other pipeline. 

##### A note on PDFs:
When the fulltext is extracted from PDFs, we don’t necessarily have the different portions of the article properly fielded, and we end up throwing everything that comes out in the body field.  This will include things such as title, author list, abstract, keyword, bibliography, etc.  This is a bug and not a feature, of course, if we could use grobid to properly segment the source document we would only pick the relevant pieces

## Dependencies

In GNU/Linux (Debian based) we need the following packages in order to be able to compile the lxml package specified in the requirements:

```
apt install libxml2-dev libxslt1-dev
```

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

We utilize the lxml.html.soupparser library to extract content from our XML files, which is an lxml interface to the BeautifulSoup HTML parser. By default when using BeautifulSoup3 (which is the version we currently use) this library uses the lxml.html parser. This parser is fast but more importantly lenient enough for our data as a lot of our XML files are not valid XML. You can find a breakdown of the different types of parsers [here](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser).

Functions:
- `open_xml()`
  - This function is used to open/read an XML file and store its content as a string. To not lose data we decode this string using the encoding detected by UnicodeDammit. This is important to do before the next step as our string before decoding is in bytecode and the next step inserts unicode - mixing these two will cause nothing but problems. The next step converts HTML entities into unicode, for example `&angst;` -> &angst;. We do this even though soupparser has HTML entity conversion capabilties because our list is much more exhaustive and as of right now there is no functionality built in to pass a customized HTML entity map/dictionary as a parameter to this parser. Our dictionary of HTML entities can be found in `entitydefs.py`.
- `parse_xml()`
 - Here we pass the string returned by `open_xml()` to soupparser's `fromstring()` function. We then remove some tags to get rid of potential garbage/nonsense strings using the xpath function which lxml has made available to us.   
- `extract_string()`
 - Here we use the xpath function to get all matches for a specific tag, and return text for the first one found.
- `extract_list()`
 - This function is similar to `extract_string()` but it returns a list and is only used for datasets.
- `extract_multi_content()`
 - This is basically the main function for this class. It loops through the xpaths found in `rules.py` and collects the content for each one using `extract_string()` and `extract_list()`. It returns a dictionary containing fulltext, acknowledgments, and optionally dataset(s).


In the past we have used regular expressions, `string.replace()` and `re.sub()` to fix issues that should really be fixed inside the parser. For example, parsers may try to wrap our XML files with html and body tags to attempt to reconcile the invalid/broken HTML. This is actually normal behavior of a lenient parser, but in our case it results in content for the entire file being returned for the fulltext instead of just the content inside the body. We could replace the body tag before parsing with a different name and just extract the string from that tag instead, but this is more of a workaround than a solution. Sometimes this is the only way as it's also not a good idea to edit the lxml/BeautifulSoup code as this can cause a lot of complications down the line, but if it can be avoided I highly recommend not using regular expressions and string replacements to fix these types of issues. I defer to this humorous [stackoverflow answer](https://stackoverflow.com/questions/1732348/regex-match-open-tags-except-xhtml-self-contained-tags/1732454#1732454) to deter you.

Eventually we will need to upgrade to BeautifulSoup4 as python3 is not compatible with BeautifulSoup3.  

#### PDF Files

Our PDF extractor is mainly composed of of the pdfminer tool pdf2txt. We are exploring other options such a GROBID to find if we can improve the performance of this extractor, but as of right now pdf2txt is our best option. The main downfall of pdf2txt is that it does not allow for easy extraction of things like figures, formulas and tables which are known to produce useless strings and garbage. Some documentation on the journey to improve other parsers to outperform pdf2txt can be found [here](https://docs.google.com/document/d/1gt8bwO86ZQ9NV_h54IPm7lHeuh78CyeQK1orLPS43GM/edit?usp=sharing).

#### Development

For development/debugging purposes, it can be useful to run the whole pipeline in synchronous mode on our local machine. This can be achieved by copying `config.py` to  `local_config.py` enabling the following lines:

```
### Testing:
# When 'True', it converts all the asynchronous calls into synchronous,
# thus no need for rabbitmq, it does not forward to master
# and it allows debuggers to run if needed:
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
```

When these two variables are set to `True`, we can run the pipeline (via `run.py`) and we do not need to run workers (no need for RabbitMQ either) or master pipeline (no message will be forwarded outside this pipeline). This allows us to debug more easily (e.g., import pudb; pudb.set_trace()), we can explore the output in the `live/` directory or the logs in the `logs/` directory.

## Time-Capsule

If you stop here, oh tired traveller, please don't judge us too harshly, mere mortals. We tried to simplify the chaos we didn't create. Blame the universe for its affinity for chaos.

