import unittest
import time
import json
from lib import CheckIfExtract
from settings import PROJ_HOME
from pipeline import psettings
from pipeline.workers import RabbitMQWorker, CheckIfExtractWorker
from pipeline.ADSfulltext import TaskMaster
from run import publish, read_links_from_file
from pika.adapters import SelectConnection

class TestExtractWorker(unittest.TestCase):

	def setUp(self):
		# Load the extraction worker
		params = psettings.WORKERS['CheckIfExtractWorker']
		params['RABBITMQ_URL'] = psettings.RABBITMQ_URL
		params['extract_key'] = "FULLTEXT_EXTRACT_PATH_UNITTEST"
		self.worker = CheckIfExtractWorker(params=params)

	def test_extraction_of_non_extracted(self):

		# user loads the list of full text files
		test_publish = 'tests/test_integration/stub_data/fulltext.links'
		records = read_links_from_file(test_publish)
		self.assertEqual(len(records.bibcode), 5)

		# Converts the input into a user defined payload
		records.make_payload()
		self.assertTrue(len(records.payload)>0)

		# Queues and routes are started
		TM = TaskMaster(psettings.RABBITMQ_URL, psettings.RABBITMQ_ROUTES, psettings.WORKERS)
		TM.initialize_rabbitmq()

		# The worker connects to the queue
		publish_worker = RabbitMQWorker()
		ret_queue = publish_worker.connect(psettings.RABBITMQ_URL)
		self.assertTrue(ret_queue)

		# External worker publishes to the rabbitmq queue
		ret = publish(publish_worker, records.payload, exchange='FulltextExtractionExchange', routing_key='CheckIfExtractRoute')
		self.assertTrue(ret)
		time.sleep(10)

		# Worker receives packet of information and checks to see if it needs to be updated
		# time.sleep(5) do not use time.sleep, see: http://stackoverflow.com/questions/22061082/getting-pika-exceptions-connectionclosed-error-while-using-rabbitmq-in-python
		self.worker.run()
		time.sleep(10)

		# Check to see if the correct number of updates got published to the next queue
		# Re-declare the queue with passive flag
		queue = self.worker.channel.queue_declare(
	        queue="StandardFileExtractorQueue",
	        passive=True
    		)


		# results = json.loads(self.worker.results)
		# self.assertIn('STALE_CONTENT', results, "Result was different to what was expected: %s" % results)

		expected_results = [{"bibcode": "test", "ft_source": "/vagrant/tests/test_unit/stub_data/te/st/test.pdf", "provider": "MNRAS", \
								"UPDATE": "STALE_CONTENT"},
							{"bibcode": "test", "ft_source": "tests/test_unit/stub_data/te/st/test.pdf", "provider": "MNRAS", \
								"UPDATE": "DIFFERING_FULL_TEXT"},
							{"bibcode": "test1", "ft_source": "tests/test_unit/stub_data/te/st/test.ocr", "provider": "MNRAS", \
								"UPDATE": "NOT_EXTRACTED_BEFORE"},
							{"bibcode": "test3", "ft_source": "/vagrant/tests/test_unit/stub_data/te/st/test.pdf", "provider": "MNRAS", \
								"UPDATE": "MISSING_FULL_TEXT"},
							]

		self.assertEqual(json.loads(self.worker.results), expected_results, 'Type of output: %s, type of expected: %s' % (type(self.worker.results), type(expected_results)))
		# self.assertEqual(self.worker.results, 'pass')
		self.assertTrue(queue.method.message_count==1, "Should be 1, but it is: %d" % queue.method.message_count)

		# Clean-up for next test: should be removed when next queue implemented
		self.worker.channel.queue_purge(queue="StandardFileExtractorQueue")

		# There should be no errors at this stage
		queue_error = self.worker.channel.queue_declare(
	        queue="ErrorHandlerQueue",
	        passive=True
    		)
		self.assertTrue(queue_error.method.message_count==0, "Should be 0, but it is: %d" % queue_error.method.message_count)


		# Worker checks to see if this full text needs to be updated
		# extract = self.extraction_worker.f()

		# Worker needs to be updated
		# self.assertTrue(extract, 'File output should not exist, it should need to be extracted, however, returns False')

		# Worker closes
		# self.fail('finish the tests')


if __name__ == "__main__":
	unittest.main()