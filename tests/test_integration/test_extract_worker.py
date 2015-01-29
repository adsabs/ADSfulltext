import unittest
import time
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
		self.worker = CheckIfExtractWorker(params=params)

	def test_extraction_of_non_extracted(self):

		# user loads the list of full text files
		test_publish = 'tests/test_integration/stub_data/fulltext.links'
		records = read_links_from_file(test_publish, stream_format='file')
		self.assertEqual(len(records.bibcode), 3)

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

		# Worker checks to see if this full text needs to be updated
		# extract = self.extraction_worker.f()

		# Worker needs to be updated
		# self.assertTrue(extract, 'File output should not exist, it should need to be extracted, however, returns False')

		# Worker closes
		# self.fail('finish the tests')


if __name__ == "__main__":
	unittest.main()