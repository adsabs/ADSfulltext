'''
This contains the classes required for each worker, which are all inheriting from the RabbitMQ class.

Each Workers functions are defined inside the lib/ folder.

Same schema is used as defined within ADSImportpipeline
'''

import pika

class RabbitMQWorker(object):
	'''
	Base worker class. Defines the plumbing to communicate with rabbitMQ
	'''
	def __init__(self, params=None):
		self.params = params

	def connect(self, url, confirm_delivery=False):
		'''
		Connect to RabbitMQ on <url>, and confirm the delivery
		'''
		try:
			self.connection = pika.BlockingConnection(pika.URLParameters(url))
			self.channel = self.connection.channel()
		
			if confirm_delivery:
				self.channel.confirm_delivery()
			
			self.channel.basic_qos(prefetch_count=1)

			return True

		except:
			print sys.exc_info()
			return False

class CheckIfExtractWorker(RabbitMQWorker):
	'''
	Check if extractor work. Checks if the file needs to be extracted and pushes to the correct following queue.
	Inherits from the base class; RabbitMQWorker.
	'''
	def __init__(self, params=None):
		self.params = params
		from lib import CheckIfExtract
		self.f = CheckIfExtract.check_if_extract

