from __future__ import absolute_import, unicode_literals
import sys
if sys.version_info > (3,):
    from builtins import zip
    from builtins import str
from adsputils import get_date, exceptions
import adsft.app as app_module
from kombu import Queue
from adsft import extraction, checker, writer, reader, ner
from adsmsg import FulltextUpdate
import os
from adsft.utils import TextCleaner

# ============================= INITIALIZATION ==================================== #

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), '../'))
app = app_module.ADSFulltextCelery('ads-fulltext', proj_home=proj_home, local_config=globals().get('local_config', {}))
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

    try:
        results = checker.check_if_extract(message, app.conf['FULLTEXT_EXTRACT_PATH'])
    except OSError as err:
        logger.error('Task failed at check_if_extract because of missing file. Error: %s', err)
        return
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
                logger.error('Unknown type: %s and message: %s', key, results[key])


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
        task_output_results.delay(msg)

    if app.conf['RUN_NER_FACILITIES_AFTER_EXTRACTION']:
        # perform named-entity recognition
        task_identify_facilities.delay(message)

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
    logger.info("Forwarding extracted fulltext to master for bibcode: %s", msg['bibcode'])
    if not app.conf['CELERY_ALWAYS_EAGER']:
        app.forward_message(rec)


@app.task(queue='facility-ner')
def task_identify_facilities(message):

    if not isinstance(message, list):
        message = [message]

    content = []
    for m in message:
        meta = checker.load_meta_file(m, app.conf['FULLTEXT_EXTRACT_PATH'])
        ft = reader.read_content(meta)
        if ft is not None:
            content.append(ft)

    keys = ['acknowledgements', 'fulltext']

    for r in content:

        bibcode_pair_tree_path = os.path.dirname(r['meta_path'])
        output_file_path = os.path.join(bibcode_pair_tree_path, 'facility_ner.json')

        out = {}

        for key, elem_str, model in zip(keys, ['facility-ack', 'facility-ft'], [model1, model2]):

            if key in r:
                facs = ner.get_facilities(model, r[key])
                if len(facs) > 0:
                    logger.debug("Adding %s as facilities found in %s using spacy ner model", str(facs), key)
                    out[elem_str] = list(set(facs)) # remove duplicates

                else:
                    logger.info("No facilities found in the %s for bibcode: %s.", key, r['bibcode'])

            else:
                logger.info("The %s field is empty for bibcode: %s", key, r['bibcode'])

        writer.write_file(output_file_path, out)


if __name__ == '__main__':
    app.start()
