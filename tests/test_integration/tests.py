import unittest
import time
import json
import os
from pipeline import psettings
from pipeline.workers import RabbitMQWorker, CheckIfExtractWorker, StandardFileExtractWorker, WriteMetaFileWorker
from pipeline.ADSfulltext import TaskMaster
from run import publish, read_links_from_file
from settings import META_CONTENT, PROJ_HOME


class TestExtractWorker(unittest.TestCase):

    def setUp(self):
        # Load the extraction worker
        check_params = psettings.WORKERS['CheckIfExtractWorker']
        standard_params = psettings.WORKERS['StandardFileExtractWorker']
        writer_params = psettings.WORKERS['WriteMetaFileWorker']

        for params in [check_params, standard_params, writer_params]:
            params['RABBITMQ_URL'] = psettings.RABBITMQ_URL
            params['extract_key'] = "FULLTEXT_EXTRACT_PATH_UNITTEST"
            params['TEST_RUN'] = True

        self.check_worker = CheckIfExtractWorker(params=check_params)
        self.standard_worker = StandardFileExtractWorker(params=standard_params)
        self.standard_worker.logger.debug("params: %s" % standard_params)
        self.meta_writer = WriteMetaFileWorker(params=writer_params)

    def tearDown(self):

        if os.path.exists('/vagrant/tests/test_unit/stub_data/te/st/1/'):
            os.remove('/vagrant/tests/test_unit/stub_data/te/st/1/meta.json')
            os.remove('/vagrant/tests/test_unit/stub_data/te/st/1/fulltext.txt')
            os.rmdir('/vagrant/tests/test_unit/stub_data/te/st/1/')

        # Purge the queues if they have content
        channel_list = [[self.check_worker.channel, 'CheckIfExtractQueue'],
                        [self.standard_worker.channel, 'StandardFileExtractorQueue'],
                        [self.meta_writer.channel, 'WriteMetaFileQueue'],
                        ]

        for channel_link, queue_name in channel_list:
            single_connection = channel_link.queue_purge(queue=queue_name)

    def test_extraction_of_non_extracted(self):

        # user loads the list of full text files and publishes them to the first queue
        test_publish = 'tests/test_integration/stub_data/fulltext_single_document.links'
        records = read_links_from_file(test_publish)

        with open(os.path.join(PROJ_HOME, test_publish), "r") as f:
            lines = f.readlines()
            nor = len(lines)

        number_of_PDFs = len(list(filter(lambda x: x.lower().endswith('.pdf'),
                                         [i.strip().split("\t")[-2] for i in lines])))
        number_of_standard_files = nor - number_of_PDFs

        self.assertEqual(len(records.bibcode), nor)

        # The pipeline converts the input into a payload expected by the workers
        records.make_payload()
        self.assertTrue(len(records.payload)>0)

        # Queues and routes are switched on so that they can allow workers to connect
        TM = TaskMaster(psettings.RABBITMQ_URL, psettings.RABBITMQ_ROUTES, psettings.WORKERS)
        TM.initialize_rabbitmq()

        # The worker connects to the queue
        publish_worker = RabbitMQWorker()
        ret_queue = publish_worker.connect(psettings.RABBITMQ_URL)
        self.assertTrue(ret_queue)

        # External worker publishes the payload created before to the RabbitMQ queue
        # for the workers to start consuming
        ret = publish(publish_worker, records.payload, exchange='FulltextExtractionExchange',
                      routing_key='CheckIfExtractRoute')
        self.assertTrue(ret)
        time.sleep(10)

        # Worker receives packet of information and checks to see if it needs to be updated
        ## see: http://stackoverflow.com/questions/22061082/\
        ## getting-pika-exceptions-connectionclosed-error-while-using-rabbitmq-in-python
        print('starting check worker...')
        self.check_worker.run()

        # We pause to simulate the asynchronous running of the workers. This is not needed when the workers
        # are listening continuously.
        time.sleep(10)

        # Check to see if the correct number of updates got published to the next queue
        ## Re-declare the queue with passive flag
        standard_queue = self.check_worker.channel.queue_declare(
            queue="StandardFileExtractorQueue",
            passive=True
            )

        pdf_queue = self.check_worker.channel.queue_declare(
            queue="PDFFileExtractorQueue",
            passive=True
            )

        self.assertTrue(standard_queue.method.message_count == number_of_standard_files,
                        "Standard queue should have at least %d message, but it has: %d" %
                        (number_of_standard_files, standard_queue.method.message_count))
        self.assertTrue(pdf_queue.method.message_count == number_of_PDFs,
                        "PDF queue should have at least %d message, but it has: %d" %
                        (number_of_PDFs, pdf_queue.method.message_count))

        # Double check with the worker output
        pdf_res = json.loads(self.check_worker.results["PDF"])
        standard_res = json.loads(self.check_worker.results["Standard"])

        if pdf_res:
            pdf_res = len(pdf_res)
        else:
            pdf_res = 0

        self.assertEqual(pdf_res, number_of_PDFs, 'Expected number of PDFs: %d' % number_of_PDFs)
        self.assertEqual(len(standard_res), number_of_standard_files, 'Expected number of normal formats: %d' %
                         number_of_standard_files)

        # There should be no errors at this stage
        queue_error = self.check_worker.channel.queue_declare(
            queue="ErrorHandlerQueue",
            passive=True
            )
        self.assertTrue(queue_error.method.message_count == 0,
                        "Should be 0, but it is: %d" % queue_error.method.message_count)

        # Now the next worker collects the list of files that need to be extracted. The Standard
        # Extractor should extract the content of the given payload and so the number of outputs
        # should match the number before. Given we don't expect any errors here!
        print('starting extractor worker')
        self.standard_worker.run()
        number_of_standard_files_2 = len(json.loads(self.standard_worker.results))
        self.assertTrue(number_of_standard_files_2, number_of_standard_files)

        # After the extractor, the meta writer should write all the payloads to disk in the correct
        # folders
        print('starting meta writer...')
        self.meta_writer.run()

        time.sleep(5)
        self.assertTrue(os.path.exists('/vagrant/tests/test_unit/stub_data/te/st/1/meta.json'))
        self.assertTrue(os.path.exists('/vagrant/tests/test_unit/stub_data/te/st/1/fulltext.txt'))

if __name__ == "__main__":
    unittest.main()