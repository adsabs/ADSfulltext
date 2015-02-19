#!/usr/bin/env python

'''
Pipeline to extract full text documents. It carries out the following:


  - Initialises the queues to be used in RabbitMQ
'''

import psettings
import workers
import multiprocessing
import time
from workers import RabbitMQWorker
from utils import setup_logging

logger = setup_logging(__file__, __name__)


class Singleton:

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class TaskMaster(Singleton):
    def __init__(self, rabbitmq_url, rabbitmq_routes, workers):
        self.rabbitmq_url = rabbitmq_url
        self.rabbitmq_routes = rabbitmq_routes
        self.workers = workers
        self.running = False

    def initialize_rabbitmq(self):
        # Make sure the plumbing in rabbitMQ is correct; this procedure is idempotent
        w = RabbitMQWorker()
        w.connect(self.rabbitmq_url)
        w.declare_all(*[self.rabbitmq_routes[i] for i in ['EXCHANGES', 'QUEUES', 'BINDINGS']])
        w.connection.close()

    def poll_loop(self, poll_interval=psettings.POLL_INTERVAL, ttl=7200, extra_params=False):
        while self.running:
            time.sleep(poll_interval)
            for worker, params in self.workers.iteritems():
                for active in params['active']:
                    if not active['proc'].is_alive():
                        # <Process(Process-484, stopped[SIGBUS] daemon)> is not alive, restarting: ReadRecordsWorker
                        logger.info('%s is not alive, restarting: %s' % (active['proc'], worker))
                        active['proc'].terminate()
                        active['proc'].join()
                        active['proc'].is_alive()
                        params['active'].remove(active)
                        continue
                    if ttl:
                        if time.time()-active['start']>ttl:
                            active['proc'].terminate()
                            active['proc'].join()
                            active['proc'].is_alive()
                            params['active'].remove(active)
        self.start_workers(verbose=False, extra_params=extra_params)

    def start_workers(self, verbose=True, extra_params=False):

        for worker, params in self.workers.iteritems():
            logger.info('Starting worker: %s' % worker)
            params['active'] = params.get('active', [])
            params['RABBITMQ_URL'] = psettings.RABBITMQ_URL
            params['ERROR_HANDLER'] = psettings.ERROR_HANDLER

            for par in extra_params:
                logger.info('Adding extra content: [%s]: %s' % (par, extra_params[par]))
                params[par] = extra_params[par]

            while len(params['active']) < params['concurrency']:

                w = eval('workers.%s' % worker)(params)
                process = multiprocessing.Process(target=w.run)
                process.daemon = True
                process.start()

                if verbose:
                    logger.info("Started %s-%s" % (worker, process.name))
                params['active'].append({
                    'proc': process,
                    'start': time.time(),
                })
            logger.info('Successfully started: %d' % len(params['active']))
        self.running = True


def start_pipeline(params_dictionary=False):
    TM = TaskMaster(psettings.RABBITMQ_URL, psettings.RABBITMQ_ROUTES, psettings.WORKERS)
    TM.initialize_rabbitmq()
    TM.start_workers(extra_params=params_dictionary)
    TM.poll_loop(extra_params=params_dictionary)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('--no-consume-queue', dest='test_run', action='store_true',
                        help='Worker will exit the queue after consuming a single message.')
    parser.add_argument('--consume-queue', dest='test_run', action='store_false',
                        help='Worker will sit on the queue, continuously consuming.')
    parser.add_argument('--testing', dest='extract_key', action='store_const', const='FULLTEXT_EXTRACT_PATH_UNITTEST',
                        help='Uses the tests/ as an output directory, relevant for unit tests')
    parser.add_argument('--live', dest='extract_key', action='store_const', const='FULLTEXT_EXTRACT_PATH',
                        help='Uses the user given output directory, relevant for live running')

    parser.set_defaults(test_run=False)
    parser.set_defaults(extract_key='FULLTEXT_EXTRACT_PATH')

    args = parser.parse_args()

    params_dictionary = {'TEST_RUN': args.test_run,
                         'extract_key': args.extract_key}

    start_pipeline(params_dictionary)


if __name__ == "__main__":
    main()