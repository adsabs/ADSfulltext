#!/usr/bin/env python


import sys
import argparse
import json
from adsft import tasks, utils
from adsputils import setup_logging

logger = setup_logging('run.py')


def read_links_from_file(file_input, force_extract=False):
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

    if 'force_extract' in kwargs:
        force_extract = kwargs['force_extract']
    else:
        force_extract = False

    records = read_links_from_file(
        full_text_links,
        force_extract=force_extract
    )


    logger.info('Setting variables')
    if 'max_queue_size' in kwargs:
        max_queue_size = kwargs['max_queue_size']
        logger.info('Max queue size overridden: %d' % kwargs['max_queue_size'])
    else:
        max_queue_size = 0

    logger.info('Publishing records to: CheckIfExtract')
    
    i = 0
    for record in records.payload:
        temp = record
        first = temp[0]['bibcode']
        last = temp[-1]['bibcode']

        logger.info(
            'Publishing [{0:d}/{1:d}, {2:d}]: [{3}] ---> [{4}]'.format(
                i, i+len(temp), len(temp), first, last)
        )
        i += len(temp)
        
        if max_queue_size and i > max_queue_size:
            logger.info('Max_queue_size reached, stopping...')
            break
        
        tasks.task_check_if_extract(record)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Process user input.')

    parser.add_argument('-f',
                        '--full_text_links',
                        dest='full_text_links',
                        action='store',
                        type=str,
                        help='Path to the fulltext.links file'
                             ' that contains the article list.')

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

    parser.set_defaults(full_text_links=False)
    parser.set_defaults(packet_size=100)
    parser.set_defaults(purge_queues=False)
    parser.set_defaults(max_queue_size=100000)
    parser.set_defaults(force_extract=False)

    args = parser.parse_args()

    if not args.full_text_links:
        print 'You need to give the input list'
        parser.print_help()
        sys.exit(0)

    # Send the files to be put on the queue
    run(args.full_text_links,
        packet_size=args.packet_size,
        max_queue_size=args.max_queue_size,
        force_extract=args.force_extract)
