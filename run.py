'''
Routine obtains and publishes the desired file list to the RabbitMQ to be full text extracted
'''

import time
import utils
from pipeline import psettings, workers, ADSfulltext

from utils import setup_logging

logger = setup_logging(__file__, __name__, level='DEBUG')


def publish(w, records, sleep=5, max_queue_size=100000, url=psettings.RABBITMQ_URL,
            exchange='FulltextExtractionExchange', routing_key='CheckIfExtractRoute'):

    '''
    This is the unique publish method for the initial publish of input to the full text extraction queue
    '''

    #Treat CheckIfExtractQueue a bit differently, since it can consume messages at a much higher rate

    logger.info('Connecting to the queue (passively)')
    response = w.channel.queue_declare(queue='CheckIfExtractQueue', passive=True)

    while response.method.message_count >= max_queue_size:
        logger.info('Max queue size reached, sleeping until can inject to the queue safely')
        time.sleep(sleep)
        response = w.channel.queue_declare(queue='CheckIfExtractQueue', passive=True)

    logger.info('Injecting into the queue')
    n = len(records)
    ni = 1
    for record in records:
        logger.info('Publishing [%d/%d]: %s' % (ni, n, record))
        w.channel.basic_publish(exchange, routing_key, record)
        ni += 1

    return True


def read_links_from_file(file_input):

    FileInputStream = utils.FileInputStream(file_input)
    FileInputStream.extract()

    return FileInputStream


def main(full_text_links, **kwargs):

    # TM = ADSfulltext.TaskMaster(psettings.RABBITMQ_URL, psettings.RABBITMQ_ROUTES, psettings.WORKERS)
    # TM.initialize_rabbitmq()

    logger.info('Loading records from: %s' % full_text_links)
    records = read_links_from_file(full_text_links)

    logger.info('Constructing temporary worker for publising records.')
    publish_worker = workers.RabbitMQWorker()
    publish_worker.connect(psettings.RABBITMQ_URL)

    logger.info('Publishing records to CheckIfExtract queue')

    packet_size = 10
    if 'packet_size' in kwargs:
        packet_size = kwargs['packet_size']

    records.make_payload(packet_size=packet_size)
    publish(publish_worker, records.payload, exchange='FulltextExtractionExchange',
            routing_key='CheckIfExtractRoute')