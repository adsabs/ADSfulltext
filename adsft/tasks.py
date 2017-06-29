
from __future__ import absolute_import, unicode_literals
import adsft.app as app_module
from adsputils import get_date, exceptions
from kombu import Queue
from adsft import extraction, checker, writer

# ============================= INITIALIZATION ==================================== #

app = app_module.ADSFulltextCelery('ads-fulltext')
logger = app.logger


app.conf.CELERY_QUEUES = (
    Queue('check-if-extract', app.exchange, routing_key='check-if-extract'),
    Queue('extract-standard', app.exchange, routing_key='extract-standard'),
    Queue('extract-pdf', app.exchange, routing_key='extract-pdf'),
    Queue('write-text', app.exchange, routing_key='write-text')
)


# ============================= TASKS ============================================= #


@app.task(queue='check-if-extract')
def task_check_if_extract(message):
    """
    Checks if the file needs to be extracted and pushes to the correct
    extraction queue.
    """
    logger.debug('Checking content: %s', message)
    results = extraction.check_if_extract(message)
    logger.debug('Results: %s', results)
    if results:
        for key in results:
            if key == 'PDF':
                for msg in results[key]:
                    
                    
                    task_extract_pdf.delay(msg)
            elif key == 'Standard':
                for msg in results[key]:
                    task_extract_standard.delay(msg)
            else:
                logger.error('Unknown type: %s and message: %s', (key, results[key]))
    
    
    
@app.task(queue='extract-standard')
def task_extract_standard(message):
    """
    Extracts the full text from the given location and pushes to the writing
    queue.
    """
    logger.debug('Extract content: %s', message)
    if not isinstance(message, list):
        message = [message]
    results = extraction.extract_content(message)
    logger.debug('Results: %s', results)
    task_write_text.delay(results)


@app.task(queue='extract-pdf')
def task_extract_pdf(message):
    """
    Extracts the full text from the given location and pushes to the writing
    queue.
    """
    logger.debug('Extract content: %s', message)
    results = extraction.extract_content(message) # TODO(rca) call PDF worker
    logger.debug('Results: %s', results)
    task_write_text.delay(results)
    

@app.task(queue='write-text')
def task_write_text(message, **kwargs):
    """
    Writes the full text to file
    """
    logger.debug('Extract content: %s', message)
    results = writer.extract_content(message)
    logger.debug('Results: %s', results)
    task_write_text.delay(results)    


if __name__ == '__main__':
    app.start()