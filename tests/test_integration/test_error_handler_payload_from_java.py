"""
Integration test that sends packets to the ErrorHandler as if they were sent by
the Java PDFWorker. The ErrorHandler should not crash and it should send it back
to the PDFQueue for the Java PDFWorker to try again.
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
import json


class TestExtractWorker(TestGeneric):
    """
    Class that tests that the ErrorHandler worker receives and handles packets
    that are sent by the Java PDFWorker.
    """

    def tearDown(self):
        """
        Generic tear down of the class. Currently, there is no tear down
        carried out, and it skips the super class's tear down method.

        :return: no return
        """
        pass
        super(TestExtractWorker, self).tearDown()

    def test_extraction_of_non_extracted(self):
        """
        Generates and publishes fake data that would come from the Java
        PDFWorker. Then it ensures the ErrorHandlerWorker resubmits this to the
        PDFQueue rather than try to process it, itself.

        :return: no return
        """

        # Fake message from Java pipeline
        print('Generating fake data')
        fake_payload = {
            self.params['PDF_EXTRACTOR']['class_name']: [
                {"ft_source": "/file.pdf"}
            ]
        }
        fake_payload = json.dumps(fake_payload)

        # Submit to ErrorQueue
        print('Publishing to the queue')
        self.publish_worker.channel.basic_publish(
            exchange=self.params['ERROR_HANDLER']['exchange'],
            routing_key=self.params['ERROR_HANDLER']['routing_key'],
            body=fake_payload,
        )
        # Run the ErrorHandler
        print('starting error handler')
        self.error_worker.run()

        time.sleep(7)

        # Check that the ErrorHandler returns it to the queue
        queue_pdf = self.publish_worker.channel.queue_declare(
            queue="PDFFileExtractorQueue",
            passive=True
            )
        expected = 1
        self.assertTrue(
            queue_pdf.method.message_count == expected,
            'Should be {0:d}, but it is: {1:d}'
            .format(expected, queue_pdf.method.message_count)
        )


if __name__ == '__main__':
    unittest.main()