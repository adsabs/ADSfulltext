# Overview of the ADSfulltext Pipeline

## DevOps

 1. **Development**
   
   Development can be carried out on a *Vagrant* virtual machine. There exists a *Puppet* manifest file on the repository and can be installed by:
   
   `user@computer> vagrant up`
   
   RabbitMQ is installed by *Docker*, and should require no intervention, other than possibly restarting it in scenarios it crashes.
   
 2. **Tests**
 
   The repository contains two sets of testing suites. The first is the *functional_tests*. These test that the pipeline works as expected, usually, from start to finish. There exist a set of stub data that are used to be extracted and can be seen in *tests/test_unit/stub_data/*. TravisCI is to be implemented once the first live pipeline is finished.
   
   The second set of tests are unit tests that check each of the individual functions of the wrkers obehave as they are expected to. The stub data for these tests are kept in the same place as noted above. They will also be included in TravisCI.
   
 3. **Deployment**
  
  TBD

## Pipeline Design

The purpose of the pipeline is to extract the full text content of articles and write them to disk, so that they can be accessed by other parts of the ADS infrastructure, e.g., the Solr search engine or ADSData. The following describes how a single article would undergo extraction:

  1. The article is determined if it should be extracted or not
  2. The full text is the extracted along with some relevant meta data.
  3. The full text content and meta content are written to file, one into the file fulltext.txt and the other into meta.json.

All these tasks can be asynchronous and so, an **A**synchronous **M**essage **Q**ueueing **P**rotocol (AMQP), via the RabbitMQ package, has been used. A simple Publish/Subscribe pattern has been implemented, with a direct exchange. This means for every queue, a worker can either publish content to a queue (Publisher), or receive conent from a queue (Consumer). The workers are described below. The RabbitMQ schema is shown in the following image (TBD). For more details read the docs on RabbitMQ's webpages. The python package **pika** has been used to communicate with RabbitMQ.

# Pipeline Settings

The pipeline settings are found in the file **psettings.py**. This is where all details of the pipeline can be modified without modifying the code directly.

The RabbitMQ exchanges and its properties are defined here:
```
  'EXCHANGES':[
    {
      'exchange': 'FulltextExtractionExchange',
      'exchange_type': 'direct',
      'passive': False,
      'durable': True,
    },
  ]
```
The content should be comparable to that outlined in RabbitMQ/pika for easy modification. The queue names and their routes here:
```
  'QUEUES':[
    {
      'queue': 'CheckIfExtractQueue',
      'durable': True,
    },
    ...]
   
```

And finally, the workers properties, here:
```
WORKERS = {

  'CheckIfExtractWorker': { 
    'concurrency': 1,
    'publish': {
      'PDF': [{'exchange': 'FulltextExtractionExchange', 'routing_key': 'PDFFileExtractorRoute',}],
      'Standard': [{'exchange': 'FulltextExtractionExchange', 'routing_key': 'StandardFileExtractorRoute',}],
      },
    'subscribe': [
      {'queue': 'CheckIfExtractQueue',},
    ],
  },
  ...}
```

**concurrency** refers to the total number of *asynchronous* workers. This can be changed to any integer, and this will alter the number of these workers at run time.

## Workers

There are currently one worker per each queue (see next section). Their roles are independent of each other, and are built to be asynchronous. The workers are split into the following types:

 1. CheckIfExtract**Worker**
 
 This worker communicates with the CheckIfExtract**Queue**. It determines if the given article is to be updated or not. This decision is made using the following criteria:
   * Does this article already have a *pair-tree-path*/meta.json file, i.e., has an extraction ever been carried out for this article?
   * Has the given extraction source changed since the last extraction. The last source file is obtained from the *pair-tree-path*/meta.json file.
   * Is the content stale? Currently, this is determined using the last modified time of the <pair-tree>/meta.json and checking if it is older than the article's source file. If it is older, it is stale, and needs to be updated.
   
 If the full text is to be extracted based on the previous criteria, it is published to the extraction queue. Depending on the file type, it is either sent to the StandardFileExtractor**Queue** or the PDFFileExtractor**Queue**.
   
 2. StandardFileExtractor**Worker**
 
 This worker communicates with the StandardFileExtract**Queue**. It determines the type of file that it has been given and extracts the full text content from it. Currently, the formats that it can extract from are:
   * **XML** using the python package lxml, and SoupParser
   * **HTML** using the python package lxml
   * **Text** and **OCR** using python's built-in tools
   * *HTTP* TBD
   
 It publishes the extracted content to the WriteMetaFile**Queue**.
   
 3. *PDFFileExtractor**Worker*** TBD
 
 This worker communicates with the PDFFileExtract**Queue**. It is separate to the standard file queue, as the worker is written in Java and not Python. This is only feasible due to RabbitMQ. The planned output will be published to the WriteMetaFile**Queue**
 
 4. WriteMetaFile**Worker**
 
 This worker communicates with the WriteMetaFile**Queue**. It's sole purpose is to write the full text content and meta data to file. The output location is determined by two things:
   * i) The absolute location is given in the settings.py file, in the **config** dictionary, with the key **FULLTEXT_EXTRACT_PATH**. For testing, the alternative path **FULLTEXT_EXRACT_PATH_UNITTEST** is used.
   
   * ii) The relative path of the article is determind from the bibliographic code, BibCode. The BibCode is converted into a **pair-tree path**, e.g., MNRAS2014 becomes MN/RA/S2/01/4/. This is to both not run into the unix file limit per directory, and make indexable searching faster.
 
 5. *ErrorHandler**Worker*** TBD
 
 This worker communicates with the ErrorHandler**Queue**. Any worker that runs into an exception error and exits, will be placed into the ErrorHandler**Queue**. The worker should then attempt to find the problem article, and attempt to fix the problem, otherwise discard it into the log files for manual intervention.
 
# Extraction Settings

XML files are the only extracted content that can access more relevant content in a systematic way. With the current extractor class, it is possible to extract more content without modifying the code extensively. Within the settings file **settings.py**, the following can be found:
```
META_CONTENT = {
    "XML": {
        "fulltext": ['//body','//section[@type="body"]', '//journalarticle-body'],
        "acknowledgements": ['//ack', '//section[@type="acknowledgments"]', '//subsection[@type="acknowledgement" or @type="acknowledgment"]'],
        "dataset": ['//named-content[@content-type="dataset"]'],
    },
```

The dictionary key is the content wanted, e.g., fulltext. The key's value is the **XPATH** search pattern. Given not all XML files are formatted the same way, each content has a range of XPATH patterns to try. The system will loop over each one until successful. To include another type of content to extract, the dictionary simply needs to be appended the new content key name and an XPATH. For more details on the XPATH extraction, read the lxml docs. A quick example:

```
<named-content content-type=simbad-id>M87</named-content>
```
The new addition to the dictionary, could be:
```
"simbad-id": ['//named-content[@content-type="simbad-id"]']
```
