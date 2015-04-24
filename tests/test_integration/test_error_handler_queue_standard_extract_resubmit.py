"""
Integration test that sends packets that cause the StandardExtract workers to
crash. The ErrorHandler worker should then correctly extract the content that is
perfectly fine.
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
    Class for testing that the ErrorWorker can accept and correct packets that
    were meant to processed by the StandardExtract worker.
    """

    def setUp(self):
        """
        Generic set up of the class. It first calls the generic super class's
        set up. Following that it creates a link to the all.links file. Finally,
        it determines the expected paths and files that will be generated from
        the tests.

        :return: no return
        """

        super(TestExtractWorker, self).setUp()
        self.test_publish = os.path.join(
            PROJ_HOME,
            'tests/test_integration/stub_data/'
            'fulltext_error_handling_standard_extract_resubmitted.links'
        )
        self.expected_paths = self.calculate_expected_folders(self.test_publish)

    def tearDown(self):
        """
        Generic tear down of the class. It removes the files and paths created
        in the test. It then calls the super class's tear down afterwards.

        :return: no return
        """

        self.clean_up_path(self.expected_paths)
        super(TestExtractWorker, self).tearDown()

    def test_extraction_of_non_extracted(self):
        """
        Submits a packet to the RabbitMQ that contains 1 fine bibcode and 1 bad
        bibcode. The bad bibcode should make the StandardExtract worker crash
        and it should resubmit the packet to RabbitMQ.
        The ErrorWorker should then fix the normal content and ignore the bad
        content. When this finishes it cleans up the relevant files and paths.

        :return: no return
        """

        # user loads the list of full text files and publishes them to the first
        # queue
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
        pdf_res = json.loads(self.check_worker.results["PDF"])
        standard_res = json.loads(self.check_worker.results["Standard"])

        extract_type = 'NOT_EXTRACTED_BEFORE'
        for res in standard_res:
            self.assertEqual(
                res[CONSTANTS['UPDATE']],
                extract_type,
                'This should be {0}, but is in fact: {1}'
                .format(extract_type, res[CONSTANTS['UPDATE']])
            )

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

        # The error handler should resubmit each individual payload back to the
        # queue that failed
        standard_queue = self.check_worker.channel.queue_declare(
            queue="WriteMetaFileQueue",
            passive=True
            )
        self.assertTrue(
            standard_queue.method.message_count,
            'WriteMetaFileQueue should have at least 1 message, but it has: '
            '{0:d}'.format(standard_queue.method.message_count)
        )

        # StandardExtractor should then work its magic on the single
        # resubmission
        print('starting meta writer')
        self.meta_writer.run()

        for path in [self.expected_paths[1]]:
            self.assertTrue(
                os.path.exists(path),
                'Meta path not created: {0}'.format(path)
            )


if __name__ == '__main__':
    unittest.main()