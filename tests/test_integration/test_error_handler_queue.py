"""
Integration test that sends packets that cause the StandardExtract workers to
crash. Then it checks that the ErrorHandler receives the packet and then
processes it.
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


class TestExtractWorker(TestGeneric):
    """
    Class that tests that the ErrorHandler can handle packets that were sent
    by the StandardExtract workers.
    """

    def tearDown(self):
        """
        Generic tear down of the class. It calls the super class's tear down
        afterwards.

        :return: no return
        """

        super(TestExtractWorker, self).tearDown()

    def test_extraction_of_non_extracted(self):
        """
        Publishes to the CheckIfExtract queue a list that contains 1 good and 1
        bad bibcode. It then checks that the ErrorHandler receives and processes
        the bad bibcode that causes the StandardExtract worker to crash.

        :return: no return
        """

        test_publish = os.path.join(
            PROJ_HOME,
            'tests/test_integration/stub_data/fulltext_error_handling.links'
        )

        # user loads the list of full text files and publishes them to the first
        #  queue
        records = read_links_from_file(test_publish)

        self.helper_get_details(test_publish)
        self.assertEqual(
            len(records.bibcode),
            self.nor,
            'The number of records should match the number of lines. It does '
            'not: {0:d} [{1:d}]'.format(len(records.bibcode), self.nor)
        )

        # The pipeline converts the input into a payload expected by the workers
        records.make_payload()
        self.assertTrue(len(records.payload) > 0)

        # External worker publishes the payload created before to the RabbitMQ
        # queue for the workers to start consuming
        ret = publish(self.publish_worker,
                      records.payload,
                      exchange='FulltextExtractionExchange',
                      routing_key='CheckIfExtractRoute')
        self.assertTrue(ret)
        time.sleep(10)

        # Worker receives packet of information and checks to see if it needs to
        #  be updated
        print('starting check worker...')
        self.check_worker.run()

        # We pause to simulate the asynchronous running of the workers. This is
        # not needed when the workers are listening continuously.
        print('sleeping')
        time.sleep(10)
        print('continuing')
        # Check to see if the correct number of updates got published to the
        # next queue
        # Re-declare the queue with passive flag
        standard_queue = self.check_worker.channel.queue_declare(
            queue="StandardFileExtractorQueue",
            passive=True
            )

        pdf_queue = self.check_worker.channel.queue_declare(
            queue="PDFFileExtractorQueue",
            passive=True
            )

        self.assertTrue(
            standard_queue.method.message_count,
            'Standard queue should have at least 1 message, but it has: {0:d}'
            .format(standard_queue.method.message_count)
        )

        # Double check with the worker output
        pdf_res = json.loads(self.check_worker.results['PDF'])
        standard_res = json.loads(self.check_worker.results['Standard'])

        extract_type = 'NOT_EXTRACTED_BEFORE'
        for res in standard_res:
            self.assertEqual(
                res[CONSTANTS['UPDATE']],
                extract_type,
                'This should be %s, but is in fact: {0}'
                .format(extract_type, res[CONSTANTS['UPDATE']])
            )

        if pdf_res:
            pdf_res = len(pdf_res)
        else:
            pdf_res = 0

        # Now the next worker collects the list of files that need to be
        # extracted. The StandardExtractor should extract the content of the
        # given payload and so the number of outputs should match the number
        # before. Given we don't expect any errors here!
        print('starting extractor worker...')
        self.standard_worker.run()
        print('sleeping')
        time.sleep(10)
        print('continuing')

        # There should be no errors at this stage
        queue_error = self.check_worker.channel.queue_declare(
            queue="ErrorHandlerQueue",
            passive=True
            )
        self.assertTrue(
            queue_error.method.message_count == 1,
            'Should be 1, but it is: {0:d}'
            .format(queue_error.method.message_count)
        )

        print('starting error handler')
        self.error_worker.run()
        time.sleep(10)
        queue_error = self.check_worker.channel.queue_declare(
            queue="ErrorHandlerQueue",
            passive=True
            )
        self.assertTrue(
            queue_error.method.message_count == 0,
            'Should be 0, but it is: {0:d}'
            .format(queue_error.method.message_count)
        )

if __name__ == '__main__':
    unittest.main()