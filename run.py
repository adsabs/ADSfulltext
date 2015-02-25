#!/usr/bin/env python
'''
Routine obtains and publishes the desired file list to the RabbitMQ to be full text extracted
'''

import sys
import time
import utils
import argparse
import json
from settings import CONSTANTS
from pipeline import psettings, workers, ADSfulltext

from utils import setup_logging

logger = setup_logging(__file__, __name__, level='DEBUG')


def purge_queues(queues=psettings.RABBITMQ_ROUTES['QUEUES']):
    publish_worker = workers.RabbitMQWorker()
    publish_worker.connect(psettings.RABBITMQ_URL)

    for queue in queues:
        _q = queue['queue']
        logger.info('Purging queue: %s' % _q)
        publish_worker.channel.queue_purge(queue=_q)


def publish(w, records, sleep=5, max_queue_size=10000, url=psettings.RABBITMQ_URL,
            exchange='FulltextExtractionExchange', routing_key='CheckIfExtractRoute'):

    '''
    This is the unique publish method for the initial publish of input to the full text extraction queue
    '''

    #Treat CheckIfExtractQueue a bit differently, since it can consume messages at a much higher rate

    # logger.info('Connecting to the queue (passively)')
    # response = w.channel.queue_declare(queue='CheckIfExtractQueue', passive=True)

    logger.info('Injecting into the queue')
    n = len(records)
    ni = 1
    for record in records:

        response = w.channel.queue_declare(queue='CheckIfExtractQueue', passive=True)
        while response.method.message_count >= max_queue_size:
            logger.info('Max queue size reached [%d], sleeping until can inject to the queue safely' % max_queue_size)
            time.sleep(sleep)
            response = w.channel.queue_declare(queue='CheckIfExtractQueue', passive=True)

        temp = json.loads(record)
        first, last = temp[0][CONSTANTS['BIBCODE']], temp[-1][CONSTANTS['BIBCODE']]
        logger.info('Publishing [%d/%d, %d]: [%s] ---> [%s]' % (ni, n, len(temp), first, last))
        w.channel.basic_publish(exchange, routing_key, record)
        ni += 1

    return True


def read_links_from_file(file_input):

    FileInputStream = utils.FileInputStream(file_input)
    FileInputStream.extract()

    return FileInputStream


def run(full_text_links, **kwargs):

    logger.info('Loading records from: %s' % full_text_links)

    records = read_links_from_file(full_text_links)

    logger.info('Constructing temporary worker for publising records.')
    publish_worker = workers.RabbitMQWorker()
    publish_worker.connect(psettings.RABBITMQ_URL)

    logger.info('Publishing records to: CheckIfExtract')

    packet_size = 10
    if 'packet_size' in kwargs:
        packet_size = kwargs['packet_size']
        logger.info('Packet size overridden: %d' % kwargs['packet_size'])

    if 'max_queue_size' in kwargs:
        max_queue_size = kwargs['max_queue_size']
        logger.info('Max queue size overridden: %d' % kwargs['max_queue_size'])

    records.make_payload(packet_size=packet_size)
    publish(publish_worker, records=records.payload, max_queue_size=max_queue_size,
            exchange='FulltextExtractionExchange', routing_key='CheckIfExtractRoute')


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Process user input.')

    parser.add_argument('-f', '--full_text_links', dest='full_text_links', action='store', type=str,
                        help='Path to the fulltext.links file that contains the article list.')
    parser.add_argument('-p', '--packet_size', dest='packet_size', action='store', type=int,
                        help='Size of the payloads to be sent to RabbitMQ.')
    parser.add_argument('-q', '--purge_queues', dest='purge_queues', action='store_true',
                        help='Purge all the queues so there are no remaining packets')
    parser.add_argument('-m', '--max_queue_size', dest='max_queue_size', action='store', type=int)

    parser.set_defaults(fulltext_links=False)
    parser.set_defaults(packet_size=100)
    parser.set_defaults(purge_queues=False)
    parser.set_defaults(max_queue_size=10000)

    args = parser.parse_args()

    if args.purge_queues:
        purge_queues()
        sys.exit(0)

    if not args.full_text_links:
        print 'You need to give the input list'
        parser.print_help()
        sys.exit(0)

    # Send the files to be put on
    run(args.full_text_links, packet_size=args.packet_size, max_queue_size=args.max_queue_size)