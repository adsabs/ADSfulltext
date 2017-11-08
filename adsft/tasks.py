from __future__ import absolute_import, unicode_literals
from adsputils import get_date, exceptions
import adsft.app as app_module
from kombu import Queue
from adsft import extraction, checker, writer
from adsmsg import FulltextUpdate
import os

# ============================= INITIALIZATION ==================================== #

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), '../'))
app = app_module.ADSFulltextCelery('ads-fulltext', proj_home=proj_home)
logger = app.logger


app.conf.CELERY_QUEUES = (
    Queue('check-if-extract', app.exchange, routing_key='check-if-extract'),
    Queue('extract', app.exchange, routing_key='extract'),
    Queue('extract-grobid', app.exchange, routing_key='extract-grobid'),
    Queue('output-results', app.exchange, routing_key='output-results'),
)


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
        for x in ('acknowledgements', 'dataset'):
            if x in r and r[x]:
                msg[x] = r[x]

        logger.debug("Calling 'task_output_results' with '%s'", msg)
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
            #msg = {
                    #'bibcode': r['bibcode'],
                    #'body': r['grobid_fulltext'],
                    #}
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
    logger.debug('Will forward this record: %s', msg)
    rec = FulltextUpdate(**msg)
    logger.debug("Calling 'app.forward_message' with '%s'", str(rec))
    app.forward_message(rec)

if __name__ == '__main__':
    app.start()
