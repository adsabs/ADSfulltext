#!/usr/bin/env python
"""
Routine obtains and publishes the desired file list to the RabbitMQ to be full
text extracted
"""

__author__ = 'J. Elliott'
__maintainer__ = 'J. Elliott'
__copyright__ = 'Copyright 2015'
__version__ = '1.0'
__email__ = 'ads@cfa.harvard.edu'
__status__ = 'Production'
__credit__ = ['V. Sudilovsky']
__license__ = "GPLv3"

import sys
import time
import utils
import argparse
import json
from settings import CONSTANTS
from pipeline import psettings, workers, ADSfulltext
from utils import setup_logging

logger = setup_logging(__file__, __name__)


def purge_queues(queues=psettings.RABBITMQ_ROUTES['QUEUES']):
    """
    Purges the ADSfulltext queue on the RabbitMQ instance of its content

    :param queues: queue name that needs to be purged
    :return: no return
    """

    publish_worker = workers.RabbitMQWorker()
    publish_worker.connect(psettings.RABBITMQ_URL)

    for queue in queues:
        _q = queue['queue']
        logger.info('Purging queue: %s' % _q)
        publish_worker.channel.queue_purge(queue=_q)


def publish(w, records, sleep=5, max_queue_size=10000,
            url=psettings.RABBITMQ_URL, exchange='FulltextExtractionExchange',
            routing_key='CheckIfExtractRoute'):
    """
    Used to publish packets to the RabbitMQ instance.

    :param w: worker used to communicate with the RabbitMQ instance
    :param records: the list of records to be published to the queue
    :param sleep: how long it should sleep if max_queue_size has been reached
    :param max_queue_size: the max number of items to be on the queue
    :param url: the URI of the RabbitMQ instance
    :param exchange: name of the exchange to publish to
    :param routing_key: the routing key of the queue to publish to
    :return: boolean to denote if the publishing was a success
    """

    logger.info('Injecting into the queue')
    n = len(records)
    ni = 1
    for record in records:

        response = w.channel.queue_declare(queue='CheckIfExtractQueue',
                                           passive=True)

        while response.method.message_count >= max_queue_size:
            logger.info('Max queue size reached [{0}], sleeping until can '
                        'inject to the queue safely' % max_queue_size)
            time.sleep(sleep)
            response = w.channel.queue_declare(queue='CheckIfExtractQueue',
                                               passive=True)

        temp = json.loads(record)
        first = temp[0][CONSTANTS['BIBCODE']]
        last = temp[-1][CONSTANTS['BIBCODE']]

        logger.info(
            'Publishing [{0:d}/{1:d}, {2:d}]: [{3}] ---> [{4}]'.format(
                ni, n, len(temp), first, last)
        )

        w.channel.basic_publish(exchange, routing_key, record)
        ni += 1

    return True


def read_links_from_file(file_input, force_extract):
    """
    Opens the link file given and parses the content into a set of lists.

    :param file_input: path to the link file
    :param force_extract: did the user bypass the internal checks
    :return: file stream type (see utils.py)
    """

    FileInputStream = utils.FileInputStream(file_input)
    FileInputStream.extract(force_extract=force_extract)

    return FileInputStream


def run(full_text_links, **kwargs):
    """
    Locates the file specified by the user, loads the list of bibcodes and
    parses the relevant content. It then publishes this to the CheckIfExtract
    queue on the RabbitMQ instance specified in psettings.py. This essentially
    the main() of this script and is meant to be the sole injector of packets
    to the ADSfulltext system. Extra keywords can be taken care of here, to be
    passed on to the relevant sub functions or classes.

    :param full_text_links: path to the file containing the full text articles
    :param kwargs: extra keyword arguments
    :return: no return
    """

    logger.info('Loading records from: {0}'.format(full_text_links))

    records = read_links_from_file(
        full_text_links,
        force_extract=kwargs['force_extract']
    )

    logger.info('Constructing temporary worker for publising records.')
    publish_worker = workers.RabbitMQWorker()
    publish_worker.connect(psettings.RABBITMQ_URL)

    logger.info('Setting variables')
    if 'packet_size' in kwargs:
        packet_size = kwargs['packet_size']
        logger.info(
            'Packet size overridden: {0:d}'.format(kwargs['packet_size']))
    else:
        packet_size = 10

    if 'max_queue_size' in kwargs:
        max_queue_size = kwargs['max_queue_size']
        logger.info('Max queue size overridden: %d' % kwargs['max_queue_size'])
    else:
        max_queue_size = 10000

    logger.info('Making payload')
    records.make_payload(packet_size=packet_size)

    logger.info('Publishing records to: CheckIfExtract')
    publish(publish_worker,
            records=records.payload,
            max_queue_size=max_queue_size,
            exchange='FulltextExtractionExchange',
            routing_key='CheckIfExtractRoute')


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Process user input.')

    parser.add_argument('-f',
                        '--full_text_links',
                        dest='full_text_links',
                        action='store',
                        type=str,
                        help='Path to the fulltext.links file'
                             ' that contains the article list.')

    parser.add_argument('-p',
                        '--packet_size',
                        dest='packet_size',
                        action='store',
                        type=int,
                        help='Size of the payloads to be sent to RabbitMQ.')

    parser.add_argument('-q',
                        '--purge_queues',
                        dest='purge_queues',
                        action='store_true',
                        help='Purge all the queues so there are no remaining'
                             ' packets')

    parser.add_argument('-m',
                        '--max_queue_size',
                        dest='max_queue_size',
                        action='store',
                        type=int,
                        help='The maximum number of packets in a queue')

    parser.add_argument('-e',
                        '--extract_force',
                        dest='force_extract',
                        action='store_true',
                        help='Force the extract of all input bibcodes')

    parser.set_defaults(fulltext_links=False)
    parser.set_defaults(packet_size=100)
    parser.set_defaults(purge_queues=False)
    parser.set_defaults(max_queue_size=10000)
    parser.set_defaults(force_extract=False)

    args = parser.parse_args()

    if args.purge_queues:
        purge_queues()
        sys.exit(0)

    if not args.full_text_links:
        print 'You need to give the input list'
        parser.print_help()
        sys.exit(0)

    # Send the files to be put on the queue
    run(args.full_text_links,
        packet_size=args.packet_size,
        max_queue_size=args.max_queue_size,
        force_extract=args.force_extract)