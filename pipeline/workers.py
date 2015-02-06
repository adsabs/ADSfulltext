"""
This contains the classes required for each worker, which are all inheriting from the RabbitMQ class.

Each Workers functions are defined inside the lib/ folder.

Same schema is used as defined within ADSImportpipeline
"""

import pika
import json
import utils


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

    def publish(self, message, topic=False, **kwargs):

        if topic:
            self.logger.debug('Using topic in publish')
            for key in self.params['publish'].keys():
                self.logger.debug('Using key: %s' % key)
                for e in self.params['publish'][key]:
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
            #self.publish_to_error_queue(json.dumps({self.__class__.__name__:message}),header_frame=header_frame)

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
            #self.publish_to_error_queue(json.dumps({self.__class__.__name__:message}),header_frame=header_frame)

        # Send delivery acknowledgement
        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def run(self):
        self.connect(self.params['RABBITMQ_URL'])
        self.subscribe(self.on_message)


class StandardFileExtractWorker(RabbitMQWorker):

    """Check if extractor work. Checks if the file needs to be extracted and pushes to the correct following queue."""

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
            #self.publish_to_error_queue(json.dumps({self.__class__.__name__:message}),header_frame=header_frame)

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
            self.results = self.f(message)
            self.logger.debug("Publishing")
            self.publish(self.results)

        except Exception, e:
            import traceback
            self.results = "Offloading to ErrorWorker due to exception: %s" % e.message
            self.logger.warning("Offloading to ErrorWorker due to exception: %s (%s)" % (e.message, traceback.format_exc()))
            #self.publish_to_error_queue(json.dumps({self.__class__.__name__:message}),header_frame=header_frame)

        # Send delivery acknowledgement
        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def run(self):
        self.connect(self.params['RABBITMQ_URL'])
        self.subscribe(self.on_message)