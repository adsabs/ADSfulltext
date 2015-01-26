'''
Settings for the rabbitMQ/ADSfulltext
'''

RABBITMQ_URL = 'amqp://username:password@localhost:5672/%2F' #?socket_timeout=10&backpressure_detection=t' #Max message size = 500kb

# For production/testing environment
try:
	from local_psettings import *
except ImportError as e:
	pass