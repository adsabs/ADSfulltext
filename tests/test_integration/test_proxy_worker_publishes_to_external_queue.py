"""
Integration test that checks that the ProxyWorker sends the bibcodes to the
external queue that is defined in the psettings.py.
"""

__author__ = 'J. Elliott'
__maintainer__ = 'J. Elliott'
__copyright__ = 'Copyright 2015'
__version__ = '1.0'
__email__ = 'ads@cfa.harvard.edu'
__status__ = 'Production'
__license__ = 'GPLv3'

import sys
import os

PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)

from lib.test_base import *
import pika


class TestExtractWorker(TestGeneric):
    """
    Class to test that ProxyWorker can publish the correct bibcodes to an
    external queue.
    """

    def setUp(self):
        """
        Generic set up of the class. It first calls the generic super class's
        set up. Following that it creates a link to the all.links file. Then,
        it determines the expected paths and files that will be generated from
        the tests. Creates the exchanges, queues, and bindings that are needed
        for the ProxyWorker to receive messages from the ProxyQueue.

        :return: no return
        """

        super(TestExtractWorker, self).setUp()

        self.test_publish = os.path.join(
            PROJ_HOME,
            'tests/test_integration/stub_data/fulltext_single_document.links'
        )
        self.expected_paths = self.calculate_expected_folders(self.test_publish)

        # Override the default settings of params so that it does not mess with
        # the queue system that is already in place
        FAKE_PROXY_PUBLISH = {
            'exchange': 'MergerPipelineExchange',
            'routing_key': 'MongoWriteRoute',
            'queue': 'MongoWriteQueue',
            'RABBITMQ_URL': 'amqp://admin:password@localhost:5672/'
                            'external_vhost?'
                            'socket_timeout=10&backpressure_detection=t',
        }
        self.params['PROXY_PUBLISH'] = FAKE_PROXY_PUBLISH

        # Create the MergerPipelineExchange and relevant fake queue
        self.worker = RabbitMQWorker()
        self.worker.connect(self.params['PROXY_PUBLISH']['RABBITMQ_URL'])
        self.worker.channel.exchange_declare(
            exchange=self.params['PROXY_PUBLISH']['exchange'],
            exchange_type='direct',
            passive=False,
            durable=True
        )
        self.worker.channel.queue_declare(self.params['PROXY_PUBLISH']['queue'],
                                          durable=True)
        self.worker.channel.queue_bind(
            queue=self.params['PROXY_PUBLISH']['queue'],
            exchange=self.params['PROXY_PUBLISH']['exchange'],
            routing_key=self.params['PROXY_PUBLISH']['routing_key']
        )

    def tearDown(self):
        """
        Generic tear down of the class. It removes the files and paths created
        in the test. It then calls the super class's tear down afterwards. It
        finally deletes the queues and exchanges that were created for the test.

        :return: no return
        """
        self.clean_up_path(self.expected_paths)
        #
        # if os.path.exists(self.meta_path):
        #     os.remove(os.path.join(self.meta_path, 'fulltext.txt'))
        #     os.remove(os.path.join(self.meta_path, 'meta.json'))
        #     os.rmdir(self.meta_path)

        super(TestExtractWorker, self).tearDown()

        self.worker.channel.queue_delete(
            queue=self.params['PROXY_PUBLISH']['queue']
        )

        self.worker.channel.exchange_delete(
            exchange=self.params['PROXY_PUBLISH']['exchange']
        )

    def helper_sleep(self):
        """
        Helper function that makes the script sleep a given number of seconds

        :return: no return
        """

        time_sleep = 5
        time.sleep(time_sleep)

    def helper_count_queue(self, queue_name, worker):
        """
        Helper function to count the number of packets on a queue

        :param queue_name: name of the queue
        :param worker: worker to use to get the number of packets
        :return: the number of packets on the queue
        """
        # There should be no errors at this stage
        queue_error = worker.channel.queue_declare(
            queue=queue_name,
            passive=True
            )

        return queue_error.method.message_count

    def test_extraction_of_non_extracted(self):
        """
        When a file is successfully extracted to disk, the ProxyWorker should
        receive the list of bibcodes, so that they can be sent to the Solr queue
        to be updated there. This tests that the ProxyWorker can send the
        bibcodes to the relevant external queue.

        :return: no return
        """


        # user loads the list of full text files and publishes them to the first
        #  queue
        records = read_links_from_file(self.test_publish)

        self.helper_get_details(self.test_publish)
        self.assertEqual(
            len(records.bibcode),
            self.nor,
            'The number of records should match the number of lines. '
            'It does not: {0:d} [{1:d}]'.format(len(records.bibcode), self.nor)
        )

        # The pipeline converts the input into a payload expected by the workers
        records.make_payload()
        self.assertTrue(len(records.payload)>0)

        # External worker publishes the payload created before to the RabbitMQ
        # queue for the workers to start consuming
        ret = publish(self.publish_worker,
                      records.payload,
                      exchange='FulltextExtractionExchange',
                      routing_key='CheckIfExtractRoute')
        self.assertTrue(ret)
        self.helper_sleep()

        # Worker receives packet of information and checks to see if it needs to
        #  be updated
        ## see: http://stackoverflow.com/questions/22061082/\
        ## getting-pika-exceptions-connectionclosed-error-while-using-rabbitmq-
        # in-python
        print('starting check worker...')
        self.check_worker.run()

        # We pause to simulate the asynchronous running of the workers. This is
        # not needed when the workers are listening continuously.
        self.helper_sleep()

        # Check to see if the correct number of updates got published to the
        # next queue
        # Re-declare the queue with passive flag
        standard_count = self.helper_count_queue(
            queue_name='StandardFileExtractorQueue',
            worker=self.check_worker
        )
        pdf_count = self.helper_count_queue(queue_name='PDFFileExtractorQueue',
                                            worker=self.check_worker)

        self.assertTrue(standard_count == self.number_of_standard_files,
                        'Standard queue should have at least {0:d} message,'
                        ' but it has: {1:d}'
                        .format(self.number_of_standard_files, standard_count))

        self.assertTrue(pdf_count == self.number_of_PDFs,
                        'PDF queue should have at least {0:d} message, '
                        'but it has: {1:d}'
                        .format(self.number_of_PDFs, pdf_count))

        # Double check with the worker output
        pdf_res = json.loads(self.check_worker.results["PDF"])
        standard_res = json.loads(self.check_worker.results["Standard"])

        self.assertTrue('NOT_EXTRACTED_BEFORE',
                        'This should be NOT_EXTRACTED_BEFORE, '
                        'but is in fact: {0}'
                        .format(standard_res[0][CONSTANTS['UPDATE']]))

        if pdf_res:
            pdf_res = len(pdf_res)
        else:
            pdf_res = 0

        self.assertEqual(
            pdf_res,
            self.number_of_PDFs,
            'Expected number of PDFs: {0}'.format(self.number_of_PDFs)
        )
        self.assertEqual(
            len(standard_res),
            self.number_of_standard_files,
            'Expected number of normal formats: {0}'
            .format(self.number_of_standard_files)
        )

        message_count = self.helper_count_queue(queue_name='ErrorHandlerQueue',
                                                worker=self.check_worker)
        self.assertTrue(
            message_count == 0,
            'ErrorHandlerQueue Should be 0, but it is: {0:d}'
            .format(message_count)
        )

        # Now the next worker collects the list of files that need to be
        # extracted. The Standard Extractor should extract the content of the
        # given payload and so the number of outputs should match the number
        # before. Given we don't expect any errors here!
        print('starting extractor worker')
        self.standard_worker.run()
        number_of_standard_files_2 = \
            len(json.loads(self.standard_worker.results))
        self.assertTrue(number_of_standard_files_2,
                        self.number_of_standard_files)

        # After the extractor, the meta writer should write all the payloads to
        # disk in the correct
        # folders
        print('starting meta writer...')
        self.meta_writer.run()

        self.helper_sleep()

        for path in self.expected_paths:
            self.assertTrue(
                os.path.exists(os.path.join(path, 'meta.json')),
                'Meta file not created: {0}'.format(path)
            )
            self.assertTrue(
                os.path.exists(os.path.join(path, 'fulltext.txt')),
                'Full text file not created: {0}'.format(path)
            )

        message_count = self.helper_count_queue(queue_name='ProxyPublishQueue',
                                                worker=self.meta_writer)
        self.assertTrue(message_count == 1,
                        'ProxyPublishQueue Should be 1, but it is: {0}'
                        .format(message_count))

        print('starting proxy worker')
        self.proxy_worker.run()

        message_count = self.helper_count_queue(queue_name='ProxyPublishQueue',
                                                worker=self.proxy_worker)
        self.assertTrue(message_count == 0,
                        'ProxyPublishQueue Should be 0, but it is: {0}'
                        .format(message_count))

        # Have to write in full given this is not needed in the pipeline
        external_connection = pika.BlockingConnection(
            pika.URLParameters(self.params['PROXY_PUBLISH']['RABBITMQ_URL'])
        )
        external_channel = external_connection.channel()
        message_count = external_channel.queue_declare(
            queue=self.params['PROXY_PUBLISH']['queue'],
            passive=True
        ).method.message_count

        self.assertTrue(
            message_count == 1,
            '{0} Should be 1, but it is: {1:d}'
            .format(self.params['PROXY_PUBLISH']['queue'], message_count)
        )

        self.helper_sleep()

if __name__ == '__main__':
    unittest.main()