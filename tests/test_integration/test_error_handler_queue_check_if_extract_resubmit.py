"""
Integration test that sends packets that cause the CheckIfExtract workers to
crash. The ErrorHandler worker should then correctly process the payload that is
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
from datetime import datetime


class TestExtractWorker(TestGeneric):
    """
    Class that tests the ErrorHandler worker can fix the bibcodes that are fine
    when the bad bibcode in the packet causes the CheckIfExtract worker to fail.
    """

    def setUp(self):
        """
        Generic set up of the class. It first calls the generic super class's
        set up. Following that it creates a link to the all.links file. Next, it
        modifies the meta.json so that it does not contain all the information
        it should, which will crash the CheckIfExtract worker. Finally, it
        determines the expected paths and files that will be generated from
        the tests.

        :return: no return
        """

        super(TestExtractWorker, self).setUp()

        test_file = os.path.join(PROJ_HOME,
                                 'tests/test_unit/stub_data/te/st/meta.json')
        with open(test_file) as f:
            meta_stored = json.load(f)
        meta_stored.pop(CONSTANTS['TIME_STAMP'], None)

        self.meta_path_ = test_file.replace('/te/st/meta.json', '/fu/ll/2/')

        if not os.path.exists(self.meta_path_):
            os.makedirs(self.meta_path_)

        with open(os.path.join(self.meta_path_, 'meta.json'), 'w') as f:
            json.dump(meta_stored, f)


    def tearDown(self):
        """
        Generic tear down of the class. It removes the files and paths created
        in the test. It then calls the super class's tear down afterwards.

        :return: no return
        """

        self.clean_up_path([self.meta_path_])
        super(TestExtractWorker, self).tearDown()

    def test_extraction_of_non_extracted(self):
        """
        Tests the situation that the CheckIfExtract worker fails on a given
        payload. This worker then resubmits the packet to the ErrorWorker, which
        will fix any of the contents that is formatted correctly. Once finished,
        it will clean up any of the files that it generated.

        :return: no return
        """


        # Obtain non-fake parameters
        test_publish = os.path.join(
            PROJ_HOME,
            'tests/test_integration/stub_data/'
            'fulltext_error_handling_standard_extract_resubmitted.links'
        )
        record = read_links_from_file(test_publish).raw[1]

        fake_payload = [
            {
                CONSTANTS['BIBCODE']: 'full4',
                CONSTANTS['FILE_SOURCE']: '',
                CONSTANTS['PROVIDER']: 'MNRAS',
                CONSTANTS['TIME_STAMP']: datetime.utcnow().isoformat()
            },
            record
        ]

        ret = publish(self.publish_worker,
                      [json.dumps(fake_payload)],
                      exchange='FulltextExtractionExchange',
                      routing_key='CheckIfExtractRoute')
        self.assertTrue(ret)
        time.sleep(10)

        # Worker receives packet of information and checks to see if it needs to
        #  be updated
        print('starting writer worker...')
        self.check_worker.run()

        # We pause to simulate the asynchronous running of the workers. This is
        # not needed when the workers are listening continuously.
        print('sleeping')
        time.sleep(10)
        print('continuing')
        # Check to see if the correct number of updates got published to the
        # next queue
        # Re-declare the queue with passive flag
        error_queue = self.check_worker.channel.queue_declare(
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
        time.sleep(5)

        # The failing one should fail, but the non-failing one should pass
        # This means the writing to file should work correctly
        standard_queue = self.check_worker.channel.queue_declare(
            queue="StandardFileExtractorQueue",
            passive=True
            )

        self.assertTrue(
            standard_queue.method.message_count,
            'Standard queue should have at least 1 message, but it has: {0:d}'
            .format(standard_queue.method.message_count)
        )


if __name__ == '__main__':
    unittest.main()
