#!/usr/bin/env python

"""
Pipeline to extract full text documents. It carries out the following:


  - Initialises the queues to be used in RabbitMQ
  - Starts the workers and connects them to the queue
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
import os

PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(PROJECT_HOME)

import psettings
import workers
import multiprocessing
import time
import signal
import sys
from workers import RabbitMQWorker
from utils import setup_logging

logger = setup_logging(__file__, __name__)


class Singleton(object):
    """
    Singleton type class. Collates a list of the class instances.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = \
                super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class TaskMaster(Singleton):
    """
    Class that starts, stops, and controls the workers that connect to the
    RabbitMQ instance running
    """

    def __init__(self, rabbitmq_url, rabbitmq_routes, workers):
        """
        Initialisation function (constructor) of the class

        :param rabbitmq_url: URI of the RabbitMQ instance
        :param rabbitmq_routes: list of routes that should exist
        :param workers: list of workers that should be started
        :return: no return
        """
        self.rabbitmq_url = rabbitmq_url
        self.rabbitmq_routes = rabbitmq_routes
        self.workers = workers
        self.running = False

    def quit(self, os_signal, frame):
        """
        Stops all RabbitMQ workers when it receives a SIGTERM or other type of
        SIGKILL from the OS

        :param os_signal: signal received from the OS, e.g., SIGTERM
        :param frame: packet information
        :return:
        """

        try:
            logger.info(
                'Got SIGTERM to stop workers, attempt graceful shutdown.')

            self.stop_workers()

        except Exception as err:
            logger.warning('Workers not stopped gracefully: {0}'.format(err))

        finally:
            self.running = False
            sys.exit(0)

    def initialize_rabbitmq(self):
        """
        Sets up the correct routes, exchanges, and bindings on the RabbitMQ
        instance for full text extraction

        :return: no return
        """

        w = RabbitMQWorker()
        w.connect(self.rabbitmq_url)
        w.declare_all(*[self.rabbitmq_routes[i]
                        for i in ['EXCHANGES', 'QUEUES', 'BINDINGS']])
        w.connection.close()

    def poll_loop(self, poll_interval=psettings.POLL_INTERVAL, ttl=7200,
                  extra_params=False):
        """
        Starts all of the workers connecting and consuming to the queue. It then
        continually polls the workers to ensure that the correct number exists,
        in case one has died.

        :param poll_interval: how often to poll
        :param ttl: time to live, how long before it tries to restart workers
        :param extra_params: other parameters
        :return: no return
        """

        while self.running:

            time.sleep(poll_interval)
            for worker, params in self.workers.iteritems():
                for active in params['active']:
                    if not active['proc'].is_alive():

                        logger.debug('{0} is not alive, restarting: {1}'.format(
                            active['proc'], worker))

                        active['proc'].terminate()
                        active['proc'].join()
                        active['proc'].is_alive()
                        params['active'].remove(active)
                        continue
                    if ttl:
                        if time.time()-active['start']>ttl:
                            logger.debug('time to live reached')
                            active['proc'].terminate()
                            active['proc'].join()
                            active['proc'].is_alive()
                            params['active'].remove(active)

            self.start_workers(verbose=False, extra_params=extra_params)

    def start_workers(self, verbose=True, extra_params=False):
        """
        Starts the workers and the relevant number of them wanted by the user,
        which is defined with the pipeline settings module, psettings.py.

        :param verbose: if the messages should be verbose
        :param extra_params: other parameters
        :return: no return
        """

        for worker, params in self.workers.iteritems():
            logger.debug('Starting worker: {0}'.format(worker))
            params['active'] = params.get('active', [])
            params['RABBITMQ_URL'] = psettings.RABBITMQ_URL
            params['ERROR_HANDLER'] = psettings.ERROR_HANDLER
            params['PDF_EXTRACTOR'] = psettings.PDF_EXTRACTOR

            for par in extra_params:

                logger.debug('Adding extra content: [{0}]: {1}'.format(
                    par, extra_params[par]))

                params[par] = extra_params[par]

            while len(params['active']) < params['concurrency']:

                w = eval('workers.{0}'.format(worker))(params)
                process = multiprocessing.Process(target=w.run)
                process.daemon = True
                process.start()

                if verbose:
                    logger.debug('Started {0}-{1}'.format(worker, process.name))
                params['active'].append({
                    'proc': process,
                    'start': time.time(),
                })

            logger.debug('Successfully started: {0}'.format(
                len(params['active'])))

        self.running = True

    def stop_workers(self):
        """
        Stops the workers. Currently it does nothing as closing the main process
        should gracefully clean up each daemon process.

        :return: no return
        """
        pass


def start_pipeline(params_dictionary=False):
    """
    Starts the TaskMaster that starts the queues needed for full text
    extraction. Defines how the system can be stopped, and begins the polling
    of the workers. This is the main application of ADSfulltext.

    :param params_dictionary: parameters needed for the workers and polling
    :return: no return
    """

    TM = TaskMaster(psettings.RABBITMQ_URL,
                    psettings.RABBITMQ_ROUTES,
                    psettings.WORKERS)

    TM.initialize_rabbitmq()
    TM.start_workers(extra_params=params_dictionary)

    # Define the SIGTERM handler
    signal.signal(signal.SIGTERM, TM.quit)

    # Start the main process in a loop
    TM.poll_loop(extra_params=params_dictionary)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Process user input.')

    parser.add_argument('--no-consume-queue',
                        dest='test_run',
                        action='store_true',
                        help='Worker will exit the queue after consuming a '
                             'single message.')

    parser.add_argument('--consume-queue',
                        dest='test_run',
                        action='store_false',
                        help='Worker will sit on the queue, continuously '
                             'consuming.')

    parser.add_argument('--testing',
                        dest='extract_key',
                        action='store_const',
                        const='FULLTEXT_EXTRACT_PATH_UNITTEST',
                        help='Uses the tests/ as an output directory, relevant '
                             'for unit tests')

    parser.add_argument('--live',
                        dest='extract_key',
                        action='store_const',
                        const='FULLTEXT_EXTRACT_PATH',
                        help='Uses the user given output directory, relevant '
                             'for live running')

    parser.set_defaults(test_run=False)
    parser.set_defaults(extract_key='FULLTEXT_EXTRACT_PATH')

    args = parser.parse_args()

    params_dictionary = {'TEST_RUN': args.test_run,
                         'extract_key': args.extract_key}

    start_pipeline(params_dictionary)


if __name__ == "__main__":
    main()