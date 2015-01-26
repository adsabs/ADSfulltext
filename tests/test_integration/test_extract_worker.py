import unittest
from lib import CheckIfExtract
from settings import PROJ_HOME
from pipeline import psettings
from pipeline.workers import RabbitMQWorker, CheckIfExtractWorker
from run import publish, read_links_from_file

class TestExtractWorker(unittest.TestCase):

	def setUp(self):
		# Load the extraction worker
		self.worker = CheckIfExtractWorker()

	def test_extraction_of_non_extracted(self):

		# user loads the list of full text files
		test_publish = 'tests/test_integration/stub_data/fulltext.links'
		records = read_links_from_file(test_publish, stream_format='file')
		self.assertEqual(len(records.bibcode), 3)

		# Converts the input into a user defined payload
		records.make_payload()
		self.assertTrue(len(records.payload)>0)

		# The worker connects to the queue
		publish_worker = RabbitMQWorker()
		ret_queue = publish_worker.connect(psettings.RABBITMQ_URL)
		self.assertTrue(ret_queue)


		# External worker publishes to the rabbitmq queue
		# For the testing, passive should be False, i.e., we want it to create the queue
		ret = publish(publish_worker, records.payload, exchange='FulltextExtractionExchange', routing_key='CheckIfExtractQueue', passive=False)
		self.assertTrue(ret)

		# Worker receives packet of information

		# Worker checks to see if this full text needs to be updated
		# extract = self.extraction_worker.f()

		# Worker needs to be updated
		# self.assertTrue(extract, 'File output should not exist, it should need to be extracted, however, returns False')

		# Worker closes
		self.assertFail()


if __name__ == "__main__":
	unittest.main()