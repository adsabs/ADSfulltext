from lib.test_base import *


class TestExtractWorker(TestGeneric):

    def setUp(self):

        super(TestExtractWorker, self).setUp()

        self.test_publish = os.path.join(PROJ_HOME, 'tests/test_integration/stub_data/fulltext_xml_doc_with_acknowledgement.links')
        self.expected_paths = self.calculate_expected_folders(self.test_publish)

    def tearDown(self):

        self.clean_up_path(self.expected_paths)

        super(TestExtractWorker, self).tearDown()

    def test_extraction_of_non_extracted(self):

        # user loads the list of full text files and publishes them to the first queue
        records = read_links_from_file(self.test_publish)

        self.helper_get_details(self.test_publish)
        self.assertEqual(len(records.bibcode), self.nor,
                         "The number of records should match the number of lines. It does not: %d [%d]"
                         % (len(records.bibcode),self.nor))

        # The pipeline converts the input into a payload expected by the workers
        records.make_payload()
        self.assertTrue(len(records.payload)>0)

        # External worker publishes the payload created before to the RabbitMQ queue
        # for the workers to start consuming
        ret = publish(self.publish_worker, records.payload, exchange='FulltextExtractionExchange',
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

        self.assertTrue(standard_queue.method.message_count == self.number_of_standard_files,
                        "Standard queue should have at least %d message, but it has: %d" %
                        (self.number_of_standard_files, standard_queue.method.message_count))
        self.assertTrue(pdf_queue.method.message_count == self.number_of_PDFs,
                        "PDF queue should have at least %d message, but it has: %d" %
                        (self.number_of_PDFs, pdf_queue.method.message_count))

        # Double check with the worker output
        pdf_res = json.loads(self.check_worker.results["PDF"])
        standard_res = json.loads(self.check_worker.results["Standard"])

        self.assertTrue('NOT_EXTRACTED_BEFORE',
                        'This should be NOT_EXTRACTED_BEFORE, but is in fact: %s' % standard_res[0][CONSTANTS['UPDATE']])

        if pdf_res:
            pdf_res = len(pdf_res)
        else:
            pdf_res = 0

        self.assertEqual(pdf_res, self.number_of_PDFs, 'Expected number of PDFs: %d' % self.number_of_PDFs)
        self.assertEqual(len(standard_res), self.number_of_standard_files, 'Expected number of normal formats: %d' %
                         self.number_of_standard_files)

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
        self.assertTrue(number_of_standard_files_2, self.number_of_standard_files)

        # After the extractor, the meta writer should write all the payloads to disk in the correct
        # folders
        print('starting meta writer...')
        self.meta_writer.run()

        time.sleep(5)

        for path in self.expected_paths:
            self.assertTrue(os.path.exists(os.path.join(path, 'meta.json')), "Meta file not created: %s" % path)
            self.assertTrue(os.path.exists(os.path.join(path, 'fulltext.txt')), "Full text file not created: %s" % path)
            self.assertTrue(os.path.exists(os.path.join(path, 'acknowledgements.txt')), "Acknowledgements file not created: %s" % path)


if __name__ == "__main__":
    unittest.main()