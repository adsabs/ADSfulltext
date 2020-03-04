from __future__ import absolute_import, unicode_literals
from adsputils import get_date, exceptions
import adsft.app as app_module
from kombu import Queue
from adsft import extraction, checker, writer, reader, ner
from adsmsg import FulltextUpdate
import os
from adsft.utils import TextCleaner
import spacy

# ============================= INITIALIZATION ==================================== #

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), '../'))
app = app_module.ADSFulltextCelery('ads-fulltext', proj_home=proj_home)
logger = app.logger


app.conf.CELERY_QUEUES = (
    Queue('check-if-extract', app.exchange, routing_key='check-if-extract'),
    Queue('extract', app.exchange, routing_key='extract'),
    Queue('extract-grobid', app.exchange, routing_key='extract-grobid'),
    Queue('output-results', app.exchange, routing_key='output-results'),
    Queue('facility-ner', app.exchange, routing_key='facility-ner'),
)


logger.debug("Loading spacy models for facilities...")
model1 = ner.load_model(app.conf['NER_FACILITY_MODEL_ACK'])
model2 = ner.load_model(app.conf['NER_FACILITY_MODEL_FT'])


# ============================= TASKS ============================================= #


@app.task(queue='check-if-extract')
def task_check_if_extract(message):
    """
    Checks if the file needs to be extracted and pushes to the correct
    extraction queue.
    """
    logger.debug('Checking content: %s', message)
    if not isinstance(message, list):
        message = [message]

    logger.debug("Calling 'check_if_extract' with message '%s' and path '%s'", message, app.conf['FULLTEXT_EXTRACT_PATH'])

    results = checker.check_if_extract(message, app.conf['FULLTEXT_EXTRACT_PATH'])
    logger.debug('Results: %s', results)
    if results:
        for key in results:
            if key == 'PDF' or key == 'Standard':
                for msg in results[key]:
                    logger.debug("Calling 'task_extract' with message '%s'", msg)
                    logger.info("Calling task_extract...")
                    task_extract.delay(msg)
                    if app.conf['GROBID_SERVICE'] is not None and key == 'PDF':
                        logger.debug("Calling 'task_extract_grobid' with message '%s'", msg)
                        task_extract_grobid.delay(msg)
            else:
                logger.error('Unknown type: %s and message: %s', (key, results[key]))


@app.task(queue='extract')
def task_extract(message):
    """
    Extracts the full text from the given location and pushes to the writing
    queue.
    """
    logger.debug('Extract content: %s', message)
    if not isinstance(message, list):
        message = [message]

    results = extraction.extract_content(message, extract_pdf_script=app.conf['EXTRACT_PDF_SCRIPT'])
    logger.debug('Results: %s', results)
    for r in results:

        logger.debug("Calling 'write_content' with '%s'", str(r))
        # Write locally to filesystem
        writer.write_content(r)

        # Send results to master
        msg = {
                'bibcode': r['bibcode'],
                'body': r['fulltext'],
                }
        for x in ('acknowledgements', 'dataset', 'facility'):
            if x in r and r[x]:
                msg[x] = r[x]

        # Call task without checking if fulltext is empty
        # to ensure other components (acks, etc) are output/sent to master
        logger.debug("Calling 'task_output_results' with '%s'", msg)
        logger.info("Calling task_output_results...")
        task_output_results.delay(msg)

if app.conf['GROBID_SERVICE'] is not None:
    @app.task(queue='extract-grobid')
    def task_extract_grobid(message):
        """
        Extracts the structured full text from the given location
        """
        logger.debug('Extract grobid content: %s', message)
        if not isinstance(message, list):
            message = [message]

        # Mofiy file format to force the use of GrobidPDFExtractor
        for msg in message:
            msg['file_format'] += "-grobid"

        results = extraction.extract_content(message, grobid_service=app.conf['GROBID_SERVICE'])
        logger.debug('Grobid results: %s', results)
        for r in results:
            logger.debug("Calling 'write_content' with '%s'", str(r))
            # Write locally to filesystem
            writer.write_content(r)

            ## Send results to master
            #if r['grobid_fulltext'] != "":
                #logger.debug("Calling 'task_output_results' with '%s'", msg)
                #task_output_results.delay(msg)


@app.task(queue='output-results')
def task_output_results(msg):
    """
    This worker will forward results to the outside
    exchange (typically an ADSMasterPipeline) to be
    incorporated into the storage

    :param msg: contains the bibliographic metadata

            {'bibcode': '....',
             'authors': [....],
             'title': '.....',
             .....
            }
    :return: no return
    """

    # Ensure we send unicode normalized trimmed text. Extractors already do this,
    # but we still have some file saved extraction that weren't cleaned.
    msg['body'] = TextCleaner(text=msg['body']).run(translate=False, decode=True, normalise=True, trim=True)

    logger.debug('Will forward this record: %s', msg)
    rec = FulltextUpdate(**msg)
    logger.debug("Calling 'app.forward_message' with '%s'", str(rec))
    logger.info("Calling app.forward_message...")
    if not app.conf['CELERY_ALWAYS_EAGER']:
        app.forward_message(rec)


@app.task(queue='facility-ner')
def task_identify_facilities(message):

    if not isinstance(message, list):
        message = [message]

    meta = []
    for m in message:
        meta.append(checker.load_meta_file(m, app.conf['FULLTEXT_EXTRACT_PATH']))


    for r in meta:

        if 'acknowledgements' in r:
            facs = ner.get_facilities(model1, r['acknowledgements'])
            if len(facs) > 0:
                r['facility-ack'] = []
                logger.debug("Adding %s as facilities found in ack using spacy ner model" % str(facs))
                for f in facs:
                    r['facility-ack'].append(f)

                r['facility-ack'] = list(set(r['facility-ack'])) # remove duplicates

            else:
                logger.info("No facilities found in acknowledgements for bibcode: %s." % r['bibcode'])

        else:
            logger.info("Acknowledgements field is empty for bibcode: %s" % r['bibcode'])


        if 'fulltext' in r:
            facs = ner.get_facilities(model2, r['fulltext'])
            if len(facs) > 0:
                r['facility-ft'] = []
                logger.debug("Adding %s as facilities found in fulltext using spacy ner model" % str(facs))
                for f in facs:
                    r['facility-ft'].append(f)

                r['facility-ft'] = list(set(r['facility-ft'])) # remove duplicates

            else:
                logger.info("No facilities found in fulltext for bibcode: %s." % r['bibcode'])

        else:
            logger.info("Fulltext field is empty for bibcode: %s" % r['bibcode'])


        writer.write_content(r)


if __name__ == '__main__':
    app.start()
