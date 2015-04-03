# Overview of the ADSfulltext Pipeline
<!-- TOC depth:4 withLinks:1 updateOnSave:1 -->
- [Overview of the ADSfulltext Pipeline](#overview-of-the-adsfulltext-pipeline)
	- [DevOps](#devops)
		- [Development](#development)
		- [Tests](#tests)
		- [Deployment](#deployment)
	- [Pipeline Design](#pipeline-design)
- [Pipeline Settings](#pipeline-settings)
	- [Workers](#workers)
- [Extraction Settings](#extraction-settings)
<!-- /TOC -->
## DevOps

### Development

   Development can be carried out on a *Vagrant* virtual machine. There exists a *Puppet* manifest file on the repository and can be installed by:

`user@computer> vagrant up`

The following services and tools are setup:
  1. RabbitMQ (controlled by docker and auto-started by upstart on boot)
  2. Supervisor (auto-started by upstart on boot)  
  3. Python2.7/pip
  4. Java 1.7 (1.8 also works)
  5. Maven

### Tests

The pipeline contains three types of testing suites:

  1. **Unit tests**, one each for the Python and Java code. They test the bare bones of each part of the relevant modules (e.g., extracting an XML document).
    * Python: tests/test_unit/
    *        **run by**: nosetests -w tests/test_unit/ test.py
    * Java: src/test/java/org/adslabs/adsfulltext
    *        **run by**: mvn test (N.B. there is currently no way to distinguish between the unit and integration tests within the Java module)

  2. **Integration tests**. The python code is self contained, and is used to test the interaction between the pipeline and a RabbitMQ instance. The Java integration code is not independent from the unit tests.
    * Python: tests/test_integration/
    * **run by** ./tests/integration_test.sh

  3. **Functional tests** runs the entire pipeline and checks that it works as expected, i.e., Python, Java, RabbitMQ, supervisor, all in tandem.
     * **run by** nosetests -w tests/test_functional/ test_extraction.py

All of these tests (bar functional tests) are carried out on TravisCI. Therefore, if you make a pull request, please ensure that they pass, otherwise they will not be merged.

### Deployment

To deploy on a system without using puppet manifest files, the following should be carried out:

  1. Download from github
  2. Modify the pipeline/psettings.py and src/main/resources/settings.yml files so that they point to the correct RabbitMQ URI
  3. Add the supervisord config details to /etc/supervisord.conf
  4. Compile and build the PDF Extractor, mvn package -DskipTests
  5. Run the unit tests, nosetests -w tests/test_unit/ test.py
  6. Run the integration tests, ./tests/integration_test.sh
  7. Run the functional tests, nosetests -w tests/test_functional/ test_extraction.py

At this stage everything should work. Now you need to setup the cronjob that is to be run:
  1. Change the 'FULLTEXT_EXTRACT_PATH' in settings

To start the pipeline:

```
supervisorctrl start FulltextExtraction:
```

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

To modify the number of PDFFileExtractor**Workers** you need to modify the supervisord config file located at /etc/supervisord.conf. The relevant location is :
```
[program:ADSfulltextPDFLIVE]
command=/usr/bin/java -jar target/ADSfulltext-1.0-SNAPSHOT-jar-with-dependencies.jar --consume-queue
process_name=%(program_name)s_%(process_num)02d
numprocs=5
```

For this example there are 5 processes, update this number and restart supervisor via `supervisorctl update` to apply the changes. Also, restart the pipeline via `supervisorctrl restart FulltextExtraction:`.

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
   * **HTTP** using the requests package

 It publishes the extracted content to the WriteMetaFile**Queue**.

 3. PDFFileExtractor**Worker**

 This worker communicates with the PDFFileExtract**Queue**. It is separate to the standard file queue, as the worker is written in Java and not Python. This is only feasible due to RabbitMQ. The worker uses PDFBox to extract the content of the PDF files. This has its own settings file, which is located in the YAML file: settings.yml. For testing and the live instance, they can be found:
   * src/main/resources/settings.yml
   * src/test/resources/settings.yml

   The logging for this worker is controlled by Simple Logging Facade for Java (SLF4J), with a Log4j backend. The settings are located in:
   * src/main/resources/log4j.properties
   * src/test/resources/log4j.properties

 4. WriteMetaFile**Worker**

 This worker communicates with the WriteMetaFile**Queue**. It's sole purpose is to write the full text content and meta data to file. The output location is determined by two things:
   * i) The absolute location is given in the settings.py file, in the **config** dictionary, with the key **FULLTEXT_EXTRACT_PATH**. For testing, the alternative path **FULLTEXT_EXRACT_PATH_UNITTEST** is used.

   * ii) The relative path of the article is determind from the bibliographic code, BibCode. The BibCode is converted into a **pair-tree path**, e.g., MNRAS2014 becomes MN/RA/S2/01/4/. This is to both not run into the unix file limit per directory, and make indexable searching faster.

 5. ErrorHandler**Worker**

 This worker communicates with the ErrorHandler**Queue**. Any worker that runs into an exception error and exits, will be placed into the ErrorHandler**Queue**. The worker determines who the sender was, and re-runs all of the problem files. If they fail a second time, they are discarded from the queue system. For the PDFFileExtractor**Worker**, it will resubmit all of the individual jobs back to the PDFFileExtractor**Queue**, and carry out the same logic as above.

 6. ProxyPublish**Worker**

 This worker is purely to forward information to the ADSimportpipeline to trigger the ingest of the newly extracted full text content. A bibcode is only sent to this external queue if the full text is written to disk and succesfully works as expected. Therefore, it is given content from the WriteMetaFile**Worker**. The user only need change the queue name or the *vhost* settings which are all located within the *psettings.py* configuration file.

# Extraction Settings

XML files are the only extracted content that can access more relevant content in a systematic way. With the current extractor class, it is possible to extract more content without modifying the code extensively. Within the settings file **settings.py**, the following can be found:
```
META_CONTENT = {
    "XML": {
        "fulltext": ['//body','//section[@type="body"]', '//journalarticle-body'],
        "acknowledgements": ['//ack', '//section[@type="acknowledgments"]',
                             '//subsection[@type="acknowledgement" or @type="acknowledgment"]'
                             ],
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
