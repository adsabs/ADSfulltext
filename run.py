#!/usr/bin/env python
import os
import sys
import tempfile
import argparse
import json
from adsft import tasks, utils
from adsputils import setup_logging

logger = setup_logging('run.py')


def read_links_from_file(file_input, force_extract=False, force_send=False):
    """
    Opens the link file given and parses the content into a set of lists.

    :param file_input: path to the link file
    :param force_extract: did the user bypass the internal checks
    :param force_send: always send results to master, even for already extracted files
    :return: file stream type (see utils.py)
    """

    FileInputStream = utils.FileInputStream(file_input)
    FileInputStream.extract(force_extract=force_extract, force_send=force_send)

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

    if 'force_send' in kwargs:
        force_send = kwargs['force_send']
    else:
        force_send = False

    if 'diagnose' in kwargs:
        diagnose = kwargs['diagnose']
    else:
        diagnose = False


    if diagnose:
        print("Calling 'read_links_from_file' with filename '{}', force_extract set to '{}' and force_send set to '{}'".format(full_text_links, str(force_extract), str(force_send)))
    logger.debug("Calling 'read_links_from_file' with filename '%s', force_extract set to '%s and force_send set to '%s''", full_text_links, str(force_extract), str(force_send))
    records = read_links_from_file(
        full_text_links,
        force_extract=force_extract,
        force_send=force_send
    )


    logger.info('Setting variables')
    if 'max_queue_size' in kwargs:
        max_queue_size = kwargs['max_queue_size']
        logger.info('Max queue size overridden: %d' % kwargs['max_queue_size'])
    else:
        max_queue_size = 0

    logger.info('Publishing records to: CheckIfExtract')

    i = 0
    total = len(records.payload)
    for record in records.payload:
        logger.info(
            'Publishing [{0:d}/{1:d}]: [{2}]'.format(
                i+1, total, record['bibcode'])
        )

        if max_queue_size and i >= max_queue_size:
            logger.info('Max_queue_size reached, stopping...')
            break

        if diagnose:
            print("[{}/{}] Calling 'task_check_if_extract' with '{}'".format(i+1, total, str(record)))
        logger.info("[%i/%i] Calling 'task_check_if_extract' with '%s'", i+1, total, str(record))
        tasks.task_check_if_extract.delay(record)
        #tasks.task_check_if_extract(record) # Treat synchronously to avoid saturating NFS mount access
        i += 1

def build_diagnostics(bibcodes=None, raw_files=None, providers=None):
    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    print("Preparing diagnostics temporary file '{}'...".format(tmp_file.name))
    for bibcode, raw_file, provider in zip(bibcodes, raw_files, providers):
        tmp_str = '{}\t{}\t{}'.format(bibcode, raw_file, provider)
        print("\t{}".format(tmp_str))
        tmp_file.write(tmp_str+"\n")
    tmp_file.close()
    return tmp_file.name

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

    parser.add_argument('-s',
                        '--send_force',
                        dest='force_send',
                        action='store_true',
                        help='Force sending all extracted fulltext to master (it does not extract again if it was already extracted)')

    parser.add_argument('-d',
                        '--diagnose',
                        dest='diagnose',
                        action='store_true',
                        default=False,
                        help='Show me what you would do with input files')

    parser.add_argument('-b',
                        '--bibcodes',
                        dest='bibcodes',
                        action='store',
                        default=None,
                        help='Comma delimited list of bibcodes (for diagnostics)')

    parser.add_argument('-r',
                        '--raw-files',
                        dest='raw_files',
                        action='store',
                        default=None,
                        help='Comma delimited list of raw input files (for diagnostics)')

    parser.add_argument('-p',
                        '--providers',
                        dest='providers',
                        action='store',
                        default=None,
                        help='Comma delimited list of providers (for diagnostics)')

    parser.set_defaults(full_text_links=False)
    parser.set_defaults(packet_size=100)
    parser.set_defaults(purge_queues=False)
    parser.set_defaults(max_queue_size=0)
    parser.set_defaults(force_extract=False)
    parser.set_defaults(force_send=False)
    parser.set_defaults(diagnose=False)

    args = parser.parse_args()

    if args.diagnose:
        if args.bibcodes:
            args.bibcodes = [x.strip() for x in args.bibcodes.split(',')]
        else:
            # Defaults
            args.bibcodes = ["1908MNRAS..68..224.", "1950AFChr..20..320."]

        if args.raw_files:
            args.raw_files = [x.strip() for x in args.raw_files.split(',')]
        else:
            # Defaults
            args.raw_files = ["/proj/ads/articles/bitmaps/seri/MNRAS/0068/PDF/1908MNRAS..68..224..pdf", "/proj/ads/fulltext/sources/downloads/cache/ADS/articles.adsabs.harvard.edu/full/AFChr/0020/1950AFChr..20..320..ocr"]

        if args.providers:
            args.providers = [x.strip() for x in args.providers.split(',')]
        else:
            # Defaults
            args.providers = ["ADS", "ADS"]

        args.full_text_links = build_diagnostics(raw_files=args.raw_files, bibcodes=args.bibcodes, providers=args.providers)

    if not args.full_text_links:
        print 'You need to give the input list'
        parser.print_help()
        sys.exit(0)

    # Send the files to be put on the queue
    run(args.full_text_links,
        packet_size=args.packet_size,
        max_queue_size=args.max_queue_size,
        force_extract=args.force_extract,
        force_send=args.force_send,
        diagnose=args.diagnose)

    if args.diagnose:
        print("Removing diagnostics temporary file '{}'".format(args.full_text_links))
        os.unlink(args.full_text_links)
