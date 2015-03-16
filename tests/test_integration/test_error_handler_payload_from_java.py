from lib.test_base import *
import json
from pika.spec import BasicProperties

class TestExtractWorker(TestGeneric):

    def tearDown(self):
        pass
        #super(TestExtractWorker, self).tearDown()

    def test_extraction_of_non_extracted(self):

        # Fake message from Java pipeline
        print('Generating fake data')
        fake_payload = {"PDFFileExtractorWorker": [{"ft_source": "/file.pdf"}]}
        fake_payload = json.dumps(fake_payload)
        prop = BasicProperties(headers={"SENT_FROM": "JAVA_PDF_QUEUE"})

        # Submit to ErrorQueue
        print('Publishing to the queue')
        self.publish_worker.channel.basic_publish(exchange=self.params['ERROR_HANDLER']['exchange'],
                                                routing_key=self.params['ERROR_HANDLER']['routing_key'],
                                                body=fake_payload,
                                                properties=prop,
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
        self.assertTrue(queue_pdf.method.message_count == expected,
                        "Should be %d, but it is: %d" % (expected, queue_pdf.method.message_count))





if __name__ == "__main__":
    unittest.main()