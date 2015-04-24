"""
Integration test that sends packets that cause the WriteMetaFile workers to
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
    were meant to be processed by the WriteMetaFile worker.
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
        self.expected_paths = [
            self.calculate_expected_folders(self.test_publish)[1]
        ]

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
        bibcode. The bad bibcode should make the WriteMetaFile worker and it
        should resubmit the packet to RabbitMQ. The ErrorWorker should then fix
        the normal content and ignore the bad content. When this finishes it
        cleans up the relevant files and paths.

        :return: no return
        """

        # Obtain non-fake parameters

        record = read_links_from_file(self. test_publish).raw[1]
        record[CONSTANTS['META_PATH']] = \
            check_if_extract.create_meta_path(
                record,
                extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST'
            )

        record[CONSTANTS['FULL_TEXT']] = 'Full text'
        record[CONSTANTS['FORMAT']] = 'ocr'

        # Currently hard coded as this scenario should not develop naturally
        # This is just to trigger a fail within the WriteMetaFileWorker
        # The key point is that it will be missing a full_text keyword which is
        # needed
        fake_payload = [
            {
                CONSTANTS['BIBCODE']: 'full1',
                CONSTANTS['FILE_SOURCE']: '',
                CONSTANTS['PROVIDER']: 'MNRAS',
                CONSTANTS['META_PATH']: '/vagrant/tests/test_unit/fu/ll/'
            },
            record
        ]

        ret = publish(self.publish_worker,
                      [json.dumps(fake_payload)],
                      exchange='FulltextExtractionExchange',
                      routing_key='WriteMetaFileRoute')
        self.assertTrue(ret)
        time.sleep(10)

        # Worker receives packet of information and checks to see if it needs to
        #  be updated
        print('starting writer worker...')
        self.meta_writer.run()

        # We pause to simulate the asynchronous running of the workers. This is
        # not needed when the workers
        # are listening continuously.
        print('sleeping')
        time.sleep(10)
        print('continuing')
        # Check to see if the correct number of updates got published to the
        # next queue
        # Re-declare the queue with passive flag
        error_queue = self.meta_writer.channel.queue_declare(
            queue="ErrorHandlerQueue",
            passive=True
            )

        self.assertTrue(
            error_queue.method.message_count,
            'Error queue should have at least 1 message, but it has: {0:d}'
            .format(error_queue.method.message_count)
        )

        # Ensure the error worker runs on it, it should fail a second time in a
        # row
        self.error_worker.run()

        # The failing one should fail, but the non-failing one should pass
        # This means the writing to file should work correctly
        for path in self.expected_paths:
            self.assertTrue(os.path.exists(path))

        error_queue = self.meta_writer.channel.queue_declare(
            queue="ProxyPublishQueue",
            passive=True
            )

        self.assertTrue(
            error_queue.method.message_count,
            'Proxy publish queue should have at least 1 message, but it has: '
            '{0:d}'.format(error_queue.method.message_count)
        )

if __name__ == '__main__':
    unittest.main()