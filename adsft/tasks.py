
from __future__ import absolute_import, unicode_literals
import adsft.app as app_module
from adsputils import get_date, exceptions
from kombu import Queue
from adsft import extraction, checker, writer
import os
from adsmsg import FulltextUpdate

# ============================= INITIALIZATION ==================================== #

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), '../'))
app = app_module.ADSFulltextCelery('ads-fulltext', proj_home=proj_home)
logger = app.logger


app.conf.CELERY_QUEUES = (
    Queue('check-if-extract', app.exchange, routing_key='check-if-extract'),
    Queue('extract', app.exchange, routing_key='extract')
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
    results = checker.check_if_extract(message, app.conf['FULLTEXT_EXTRACT_PATH'])
    logger.debug('Results: %s', results)
    if results:
        for key in results:
            if key == 'PDF' or key == 'Standard':
                for msg in results[key]:
                    task_extract.delay(msg)
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
    results = extraction.extract_content(message)
    logger.debug('Results: %s', results)
    for r in results:
        # Write locally to filesystem
        writer.write_content(r)

        # Send results to master
        msg = {
                'bibcode': r['bibcode'],
                'body': r['fulltext'],
                }
        task_output_results.delay(msg)


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
    app.forward_message(rec)

if __name__ == '__main__':
    app.start()
