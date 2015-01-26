'''
Routine obtains and publishes the desired file list to the RabbitMQ to be full text extracted
'''

import utils
from pipeline import psettings

def publish(w, records, sleep=5, max_queue_size=100000, url=psettings.RABBITMQ_URL, 
			exchange='FulltextExtractionExchange', routing_key='CheckIfExtractQueue', passive=True):
	
	'''
	This is the unique publish method for the initial publish of input to the full text extraction queue
	'''	

	#Treat CheckIfExtractQueue a bit differently, since it can consume messages at a much higher rate
	response = w.channel.queue_declare(queue=routing_key, passive=passive)
	
	# while response.method.message_count >= max_queue_size:
	# 	time.sleep(sleep)
	# 	response = w.channel.queue_declare(queue=routing_key, passive=True)
	

	ret = w.channel.basic_publish(exchange, routing_key, records)

	return ret

def read_links_from_file(file_input, stream_format):

	FileInputStream = utils.FileInputStream(file_input, stream_format=stream_format)
	FileInputStream.extract()

	return FileInputStream