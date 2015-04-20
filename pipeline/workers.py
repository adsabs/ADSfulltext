"""
This contains the classes required for each worker, which are all inheriting
from the RabbitMQ class.

Each Workers functions are defined inside the lib/ folder.

Same schema is used as defined within adsabs/ADSimportpipeline
"""

__author__ = 'J. Elliott'
__maintainer__ = 'J. Elliott'
__copyright__ = 'Copyright 2015'
__version__ = '1.0'
__email__ = 'ads@cfa.harvard.edu'
__status__ = 'Production'
__credit__ = ['V. Sudilovsky']
__license__ = "GPLv3"

import sys, os
from settings import CONSTANTS

PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(PROJECT_HOME)

import pika
import json
import utils
import sys
import traceback


class RabbitMQWorker(object):
    """
    Base worker class. Defines the plumbing to communicate with rabbitMQ
    """

    def __init__(self, params=None):
        """
        Initialisation function (constructor) of the class

        :param params: dictionary of parameters
        :return: no return
        """

        self.params = params
        self.logger = self.setup_logging()
        self.connection = None
        # self.channel = None
        self.results = None

    def setup_logging(self, level='DEBUG'):
        """
        Sets up the generic logging of the worker

        :param level: level of the logging, INFO, DEBUG, WARN
        :return: no return
        """

        return utils.setup_logging(__file__, self.__class__.__name__)

    def connect(self, url, confirm_delivery=False):
        """
        Connect to RabbitMQ on <url>, and confirm the delivery

        :param url: URI of the RabbitMQ instance
        :param confirm_delivery: should the worker confirm delivery of packets
        :return: no return
        """

        return_value = False
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(url))
            self.channel = self.connection.channel()
            if confirm_delivery:
                self.channel.confirm_delivery()
            self.channel.basic_qos(prefetch_count=1)
            return_value = True

        except:
            self.logger.error(sys.exc_info())
            raise Exception(sys.exc_info())

        finally:
            return return_value

    def publish_to_error_queue(self, message, exchange=None, routing_key=None,
                               **kwargs):
        """
        Publishes messages to the error queue. Prefixes the message with the
        worker that passed on the message.

        :param message: message received from the queue
        :param exchange: name of the exchange that contains the error queue
        :param routing_key: routing key for the error queue
        :param kwargs: extra keywords that may be needed
        :return: no return
        """
        if not exchange:
            exchange = self.params['ERROR_HANDLER']['exchange']

        if not routing_key:
            routing_key = self.params['ERROR_HANDLER']['routing_key']

        self.logger.debug('exchange, routing key: {0}, {1}'.format(routing_key,
                                                                   exchange))

        self.channel.basic_publish(exchange, routing_key,
                                   message, properties=kwargs['header_frame'])

    def publish(self, message, topic=False, **kwargs):
        """
        Publishes messages to the queue. Uses the generic template for the
        relevant worker, which is defined in the pipeline settings module.

        :param message: message to be publishes
        :param topic: refers to PDF or StandardFile
        :param kwargs: extra keywords that may be needed
        :return: no return
        """

        if topic:
            self.logger.debug('Using topic in publish')
            for key in self.params['publish'].keys():
                self.logger.debug('Using key: {0}'.format(key))
                for e in self.params['publish'][key]:

                    if not json.loads(message[key]):

                        self.logger.debug(
                            '{0} list is empty, not publishing'.format(e))

                        continue

                    self.logger.debug('Using exchange: {0}'.format(e))

                    self.channel.basic_publish(e['exchange'],
                                               e['routing_key'],
                                               message[key])
        else:
            for e in self.params['publish']:

                self.logger.debug('Basic publish')

                self.channel.basic_publish(e['exchange'],
                                           e['routing_key'],
                                           message)

    def subscribe(self, callback, **kwargs):
        """
        Starts the worker consuming from the relevant queue defined in the
        pipeline settings module, for that worker.

        :param callback: the function called by the worker when it consumes
        :param kwargs: extra keyword arguments
        :return: no return
        """

        for e in self.params['subscribe']:
            self.logger.debug('Subscribing to: {0}'.format(e['queue']))
            self.channel.basic_consume(callback, queue=e['queue'], **kwargs)

            if not self.params.get('TEST_RUN', False):

                self.logger.debug('Worker consuming from queue: {0}'.format(
                    e['queue']))

                self.channel.start_consuming()

    def declare_all(self, exchanges, queues, bindings):
        """
        Generates all the queues that should exist. These queues are defined in
        the pipeline settings module.

        :param exchanges: name of the exchanges that should exist
        :param queues: name of the queues that should exist
        :param bindings: bindings between exchanges and queues should exist
        :return: no return
        """

        [self.channel.exchange_declare(**e) for e in exchanges]
        [self.channel.queue_declare(**q) for q in queues]
        [self.channel.queue_bind(**b) for b in bindings]


class CheckIfExtractWorker(RabbitMQWorker):
    """
    Checks if the file needs to be extracted and pushes to the correct
    extraction queue.
    """

    def __init__(self, params=None):
        """
        Initialisation function (constructor) of the class

        :param params: dictionary of parameters
        :return: no return
        """

        self.params = params
        from lib import CheckIfExtract
        self.f = CheckIfExtract.check_if_extract
        self.logger = self.setup_logging()
        self.logger.debug("Initialized")

    def on_message(self, channel, method_frame, header_frame, body):
        """
        Function that is executed on the packet that the worker receives. It
        loads the relevant function from the libraries module, lib. If it fails
        it will publish the message to the error queue.

        :param channel: the channel instance for the connected queue
        :param method_frame: contains delivery information of the packet
        :param header_frame: contains header information of the packet
        :param body: contains the message inside the packet
        :return: no return
        """

        message = json.loads(body)
        try:
            self.logger.debug('Running on message')
            self.results = self.f(message, self.params['extract_key'])
            self.publish(self.results, topic=True)

        except Exception, e:
            self.results = 'Offloading to ErrorWorker due to exception:' \
                           ' {0}'.format(e.message)

            self.logger.warning('Offloading to ErrorWorker due to exception: '
                                '{0} ({1})'.format(e.message,
                                                   traceback.format_exc()))

            self.publish_to_error_queue(json.dumps(
                {self.__class__.__name__: message}),
                header_frame=header_frame
            )

        # Send delivery acknowledgement
        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def run(self):
        """
        Wrapper function that both connects the worker to the RabbitMQ instance
        and starts it consuming messages.
        :return: no return
        """

        self.connect(self.params['RABBITMQ_URL'])
        self.subscribe(self.on_message)


class StandardFileExtractWorker(RabbitMQWorker):
    """
    Extracts the full text from the given location and pushes to the writing
    queue.
    """

    def __init__(self, params=None):
        """
        Initialisation function (constructor) of the class

        :param params: dictionary of parameters
        :return: no return
        """
        self.params = params
        from lib import StandardFileExtract
        self.f = StandardFileExtract.extract_content
        self.logger = self.setup_logging()
        self.logger.debug('Initialised')

    def on_message(self, channel, method_frame, header_frame, body):
        """
        Function that is executed on the packet that the worker receives. It
        loads the relevant function from the libraries module, lib. If it fails
        it will publish the message to the error queue.

        :param channel: the channel instance for the connected queue
        :param method_frame: contains delivery information of the packet
        :param header_frame: contains header information of the packet
        :param body: contains the message inside the packet
        :return: no return
        """

        message = json.loads(body)
        try:
            self.results = self.f(message)
            self.logger.debug('Publishing')
            self.publish(self.results)

        except Exception, e:
            self.results = 'Offloading to ErrorWorker due to exception: ' \
                           '{0}'.format(e.message)

            self.logger.warning('Offloading to ErrorWorker due to exception: '
                                '{0} ({1})'.format(e.message,
                                                   traceback.format_exc()))

            self.publish_to_error_queue(json.dumps(
                {self.__class__.__name__: message}),
                header_frame=header_frame
            )

        # Send delivery acknowledgement
        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def run(self):
        """
        Wrapper function that both connects the worker to the RabbitMQ instance
        and starts it consuming messages.
        :return: no return
        """

        self.connect(self.params['RABBITMQ_URL'])
        self.subscribe(self.on_message)


class WriteMetaFileWorker(RabbitMQWorker):
    """
    Writes the full text to file
    """

    def __init__(self, params=None):
        """
        Initialisation function (constructor) of the class

        :param params: dictionary of parameters
        :return: no return
        """
        self.params = params
        from lib import WriteMetaFile
        self.f = WriteMetaFile.extract_content
        self.logger = self.setup_logging()
        self.logger.debug("Initialized")

    def on_message(self, channel, method_frame, header_frame, body):
        """
        Function that is executed on the packet that the worker receives. It
        loads the relevant function from the libraries module, lib. If it fails
        it will publish the message to the error queue.

        :param channel: the channel instance for the connected queue
        :param method_frame: contains delivery information of the packet
        :param header_frame: contains header information of the packet
        :param body: contains the message inside the packet
        :return: no return
        """

        message = json.loads(body)
        try:
            self.logger.debug('WriteMetaFile: type of message: '
                              '{0}, type: {1}'.format(message, type(message)))

            self.results = self.f(message)
            self.logger.debug('Publishing')
            self.publish(self.results)

        except Exception, e:
            self.results = 'Offloading to ErrorWorker due to exception: ' \
                           '{0}'.format(e.message)

            self.logger.warning('Offloading to ErrorWorker due to exception:'
                                ' {0} ({1})'.format(e.message,
                                                    traceback.format_exc()))

            self.publish_to_error_queue(json.dumps(
                {self.__class__.__name__: message}),
                header_frame=header_frame
            )

        # Send delivery acknowledgement
        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def run(self):
        """
        Wrapper function that both connects the worker to the RabbitMQ instance
        and starts it consuming messages.
        :return: no return
        """

        self.connect(self.params['RABBITMQ_URL'])
        self.subscribe(self.on_message)


class ErrorHandlerWorker(RabbitMQWorker):
    """
    Re-runs all individual bibcodes of a payload that failed, to find the single
    payload that was a problem.
    """

    def __init__(self, params):
        """
        Initialisation function (constructor) of the class

        :param params: dictionary of parameters
        :return: no return
        """
        self.params = params
        self.logger = self.setup_logging()
        self.logger.debug('Initialised')

        from pipeline import psettings
        from lib import CheckIfExtract
        from lib import StandardFileExtract
        from lib import WriteMetaFile

        self.params['WORKERS'] = psettings.WORKERS

        self.strategies = {
            'CheckIfExtractWorker': CheckIfExtract.check_if_extract,
            'StandardFileExtractWorker': StandardFileExtract.extract_content,
            'WriteMetaFileWorker': WriteMetaFile.extract_content,
        }

    def on_message(self, channel, method_frame, header_frame, body):
        """
        Function that is executed on the packet that the worker receives. It
        loads the relevant function from the libraries module, lib. If it fails
        it will publish the message to the error queue.

        :param channel: the channel instance for the connected queue
        :param method_frame: contains delivery information of the packet
        :param header_frame: contains header information of the packet
        :param body: contains the message inside the packet
        :return: no return
        """

        self.logger.debug('Error Handler: Got message')

        message = json.loads(body)
        producer = message.keys()[0]

        self.logger.debug('Producer: {0}'.format(producer))
        self.logger.debug('header information: %s' % header_frame.headers)

        if header_frame.headers and 'redelivered' in header_frame.headers \
                and header_frame.headers['redelivered']:

            self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

            self.logger.info('ErrorHandlerWorker: failed bibcode: '
                             '{0}'.format(message[CONSTANTS['BIBCODE']]))

            return

        self.logger.debug('Setting headers')
        properties = pika.spec.BasicProperties(headers={'redelivered': True})

        for individual_payload in message[producer]:

            if producer == self.params['PDF_EXTRACTOR']['class_name']:
                self.logger.debug('Payload: {0}'.format(individual_payload))
                if not message:
                    self.logger.debug(
                        '{0} list is empty, not publishing'.format(producer))
                    continue

                self.logger.debug(
                    'ErrorHandler: Republishing payload to: {0}'.format(
                        self.params['PDF_EXTRACTOR']['routing_key']))

                self.channel.basic_publish(
                    self.params['PDF_EXTRACTOR']['exchange'],
                    self.params['PDF_EXTRACTOR']['routing_key'],
                    json.dumps([individual_payload]), properties=properties
                )

                continue

            bibcode = individual_payload[CONSTANTS['BIBCODE']]
            try:
                self.logger.debug(
                    'ErrorHandler: Trying to fix payload: '
                    '{0}, type: {1}'.format(individual_payload,
                                            type(individual_payload)))

                result = self.strategies[producer](
                    [individual_payload], extract_key=self.params['extract_key']
                )

                self.logger.info('ErrorHandler: completed bibcode: '
                                 '{0}'.format(bibcode))

            except Exception:
                self.logger.error(
                    'ErrorHandler: could not fix this payload: '
                    '{0}: {1}'.format(bibcode, traceback.format_exc())
                )

                continue

            # Re-publish the single record
            if producer == 'CheckIfExtractWorker':

                for key in self.params['WORKERS'][producer]['publish'].keys():
                    for e in self.params['WORKERS'][producer]['publish'][key]:

                        self.logger.debug(
                            'Payload: {0}'.format(json.loads(result[key])))

                        if not json.loads(result[key]):
                            self.logger.debug(
                                '{0} list is empty, not publishing'.format(e))

                            continue

                        self.logger.debug(
                            'ErrorHandler: Republishing payload to: '
                            '{0}'.format(e['routing_key'])
                        )

                        self.channel.basic_publish(e['exchange'],
                                                   e['routing_key'],
                                                   result[key],
                                                   properties=properties)
            else:
                for e in self.params['WORKERS'][producer]['publish']:

                    self.logger.debug(
                        'ErrorHandler: Republishing payload to: '
                        '{0}'.format(e['routing_key']))

                    self.channel.basic_publish(e['exchange'],
                                               e['routing_key'],
                                               result,
                                               properties=properties)

        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        self.logger.debug('Acknowledge delivered')

    def run(self):
        """
        Wrapper function that both connects the worker to the RabbitMQ instance
        and starts it consuming messages.
        :return: no return
        """

        self.connect(self.params['RABBITMQ_URL'])
        self.subscribe(self.on_message)


class ProxyPublishWorker(RabbitMQWorker):
    """
    Publishes all messages to an external queue that exists on another
    RabbitMQ instance.
    """

    def __init__(self, params):
        """
        Initialisation function (constructor) of the class

        :param params: dictionary of parameters
        :return: no return
        """
        self.params = params
        self.logger = self.setup_logging()
        self.logger.debug("Initialized")

        from pipeline import psettings

        self.params['WORKERS'] = psettings.WORKERS

    def on_message(self, channel, method_frame, header_frame, body):
        """
        Function that is executed on the packet that the worker receives. It
        loads the relevant function from the libraries module, lib. If it fails
        it will publish the message to the error queue.

        :param channel: the channel instance for the connected queue
        :param method_frame: contains delivery information of the packet
        :param header_frame: contains header information of the packet
        :param body: contains the message inside the packet
        :return: no return
        """

        worker = RabbitMQWorker()
        worker.connect(self.params['PROXY_PUBLISH']['RABBITMQ_URL'])
        worker.channel.basic_publish(self.params['PROXY_PUBLISH']['exchange'],
                                     self.params['PROXY_PUBLISH']['routing_key'],
                                     body)
        worker.connection.close()

        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        self.logger.debug('Acknowledge delivered')

    def run(self):
        """
        Wrapper function that both connects the worker to the RabbitMQ instance
        and starts it consuming messages.
        :return: no return
        """

        self.connect(self.params['RABBITMQ_URL'])
        self.subscribe(self.on_message)
