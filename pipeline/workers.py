"""
This contains the classes required for each worker, which are all inheriting from the RabbitMQ class.

Each Workers functions are defined inside the lib/ folder.

Same schema is used as defined within ADSImportpipeline
"""

import pika
import json
import utils
import sys


class RabbitMQWorker(object):
    """Base worker class. Defines the plumbing to communicate with rabbitMQ"""

    def __init__(self, params=None):
        self.params = params
        self.logger = None

    def setup_logging(self, level='DEBUG'):
        return utils.setup_logging(__file__, self.__class__.__name__)

    def connect(self, url, confirm_delivery=False):
        """Connect to RabbitMQ on <url>, and confirm the delivery"""
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(url))
            self.channel = self.connection.channel()
            if confirm_delivery:
                self.channel.confirm_delivery()
            self.channel.basic_qos(prefetch_count=1)
            return True

        except:
            print sys.exc_info()
            return False

    def publish_to_error_queue(self, message, exchange=None, routing_key=None, **kwargs):
        if not exchange:
            exchange = self.params['ERROR_HANDLER']['exchange']
        if not routing_key:
            routing_key = self.params['ERROR_HANDLER']['routing_key']
        self.logger.info('exchange, routing key: %s, %s' % (routing_key, exchange))
        self.channel.basic_publish(exchange, routing_key, message, properties=kwargs['header_frame'])

    def publish(self, message, topic=False, **kwargs):
        if topic:
            self.logger.debug('Using topic in publish')
            for key in self.params['publish'].keys():
                self.logger.debug('Using key: %s' % key)
                for e in self.params['publish'][key]:

                    if not json.loads(message[key]):
                        self.logger.debug('%s list is empty, not publishing' % e)
                        continue

                    self.logger.debug("Using exchange: %s" % e)
                    self.channel.basic_publish(e['exchange'], e['routing_key'], message[key])
        else:
            for e in self.params['publish']:
                self.logger.debug('Basic publish')
                self.channel.basic_publish(e['exchange'], e['routing_key'], message)

    def subscribe(self, callback, **kwargs):
        """Note that the same callback will be called for every entry in subscribe."""
        for e in self.params['subscribe']:
            self.logger.debug("Subscribing to: %s" % e['queue'])
            self.channel.basic_consume(callback, queue=e['queue'], **kwargs)
            if not self.params.get('TEST_RUN', False):
                self.channel.start_consuming()

    def declare_all(self, exchanges, queues, bindings):
        [self.channel.exchange_declare(**e) for e in exchanges]
        [self.channel.queue_declare(**q) for q in queues]
        [self.channel.queue_bind(**b) for b in bindings]


class CheckIfExtractWorker(RabbitMQWorker):
    """Checks if the file needs to be extracted and pushes to the correct extraction queue."""

    def __init__(self, params=None):
        self.params = params
        from lib import CheckIfExtract
        self.f = CheckIfExtract.check_if_extract
        self.logger = self.setup_logging()
        self.logger.debug("Initialized")

    def on_message(self, channel, method_frame, header_frame, body):
        message = json.loads(body)
        try:
            self.logger.debug("Running on message")
            self.results = self.f(message, self.params['extract_key'])
            self.publish(self.results, topic=True)

        except Exception, e:
            import traceback
            self.results = "Offloading to ErrorWorker due to exception: %s" % e.message
            self.logger.warning("Offloading to ErrorWorker due to exception: %s (%s)" % (e.message, traceback.format_exc()))
            self.publish_to_error_queue(json.dumps({self.__class__.__name__: message}), header_frame=header_frame)

        # Send delivery acknowledgement
        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def run(self):
        self.connect(self.params['RABBITMQ_URL'])
        self.subscribe(self.on_message)


class StandardFileExtractWorker(RabbitMQWorker):

    """Extracts the full text from the given location and pushes to the writing queue."""

    def __init__(self, params=None):
        self.params = params
        from lib import StandardFileExtract
        self.f = StandardFileExtract.extract_content
        self.logger = self.setup_logging()
        self.logger.debug("Initialized")

    def on_message(self, channel, method_frame, header_frame, body):
        message = json.loads(body)
        try:
            self.results = self.f(message)
            self.logger.debug("Publishing")
            self.publish(self.results)

        except Exception, e:
            import traceback
            self.results = "Offloading to ErrorWorker due to exception: %s" % e.message
            self.logger.warning("Offloading to ErrorWorker due to exception: %s (%s)" % (e.message, traceback.format_exc()))
            self.publish_to_error_queue(json.dumps({self.__class__.__name__: message}), header_frame=header_frame)

        # Send delivery acknowledgement
        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def run(self):
        self.connect(self.params['RABBITMQ_URL'])
        self.subscribe(self.on_message)


class WriteMetaFileWorker(RabbitMQWorker):
    def __init__(self, params=None):
        self.params = params
        from lib import WriteMetaFile
        self.f = WriteMetaFile.extract_content
        self.logger = self.setup_logging()
        self.logger.debug("Initialized")

    def on_message(self, channel, method_frame, header_frame, body):
        message = json.loads(body)
        try:
            self.logger.info('WriteMetalFile: type of message: %s, type: %s' % (message, type(message)))
            self.results = self.f(message)
            self.logger.debug("Publishing")
            self.publish(self.results)

        except Exception, e:
            import traceback
            self.results = "Offloading to ErrorWorker due to exception: %s" % e.message
            self.logger.warning("Offloading to ErrorWorker due to exception: %s (%s)" % (e.message, traceback.format_exc()))
            self.publish_to_error_queue(json.dumps({self.__class__.__name__: message}), header_frame=header_frame)

        # Send delivery acknowledgement
        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def run(self):
        self.connect(self.params['RABBITMQ_URL'])
        self.subscribe(self.on_message)


class ErrorHandlerWorker(RabbitMQWorker):

    def __init__(self, params):
        self.params = params
        self.logger = self.setup_logging()
        self.logger.debug("Initialized")

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
        self.logger.info('Got message')

        message = json.loads(body)
        producer = message.keys()[0]

        if header_frame.headers and 'redelivered' in header_frame.headers and header_frame.headers['redelivered']:
            self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            self.logger.info("ErrorHandler: Fail: %s" % message)
            return

        P = pika.spec.BasicProperties(headers={'redelivered': True})

        for individual_payload in message[producer]:
            try:
                self.logger.info('ErrorHandler: Trying to fix payload: %s, type: %s' % (individual_payload, type(individual_payload)))
                result = self.strategies[producer]([individual_payload], self.params['extract_key'])
                self.logger.info('ErrorHandler: Fixed payload: %s, type: %s' % (result, type(result)))
            except Exception, e:
                import traceback
                self.logger.error('ErrorHandler could not fix this payload: %s: %s' % (individual_payload, traceback.format_exc()))
                continue

            #Re-publish the single record
            self.logger.info('Problem producer: %s' % producer)
            if producer == 'CheckIfExtractWorker':

                for key in self.params['WORKERS'][producer]['publish'].keys():
                    for e in self.params['WORKERS'][producer]['publish'][key]:

                        self.logger.info('Payload: %s' % json.loads(result[key]))
                        if not json.loads(result[key]):
                            self.logger.debug('%s list is empty, not publishing' % e)
                            continue

                        self.logger.info('ErrorHandler: Republishing payload to: %s' % e['routing_key'])
                        self.channel.basic_publish(e['exchange'], e['routing_key'], result[key])
            else:
                for e in self.params['WORKERS'][producer]['publish']:
                    self.logger.info('ErrorHandler: Republishing payload to: %s' % e['routing_key'])
                    self.channel.basic_publish(e['exchange'], e['routing_key'], result, properties=P)

        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        self.logger.info('Acknowledge delivered')

    def run(self):
        self.connect(self.params['RABBITMQ_URL'])
        self.subscribe(self.on_message)