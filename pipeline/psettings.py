'''
Settings for the rabbitMQ/ADSfulltext
'''

RABBITMQ_URL = 'amqp://username:password@localhost:5672/%2F' #?socket_timeout=10&backpressure_detection=t' #Max message size = 500kb


RABBITMQ_ROUTES = {
  'EXCHANGES':[
    {
      'exchange': 'FulltextExtractionExchange',
      'exchange_type': 'direct',
      'passive': False,
      'durable': True,
    },
  ],
  'QUEUES':[
    {
      'queue': 'CheckIfExtractQueue',
      'durable': True,
    },
    # {
    #   'queue': 'PDFFileExtractorQueue',
    #   'durable': True,
    # },
     {
       'queue': 'StandardFileExtractorQueue',
       'durable': True,
     },
    # {
    #   'queue': 'WriteMetaFileQueue',
    #   'durable': True,
    # },
    # {
    #   'queue': 'ErrorHandlerQueue',
    #   'durable': True,
    # },     
  ],
  'BINDINGS':[
    {
      'queue':        'CheckIfExtractQueue',
      'exchange':     'FulltextExtractionExchange',
      'routing_key':  'CheckIfExtractRoute',
    },
    # {
    #   'queue':        'PDFFileExtractorQueue',
    #   'exchange':     'FulltextExtractionExchange',
    #   'routing_key':  'PDFFileExtractorRoute',
    # },
     {
       'queue':        'StandardFileExtractorQueue',
       'exchange':     'FulltextExtractionExchange',
       'routing_key':  'StandardFileExtractorRoute',
     },
    # {
    #   'queue':        'WriteMetaFileQueue',
    #   'exchange':     'FulltextExtractionExchange',
    #   'routing_key':  'WriteMetaFileRoute',
    # },
    # {
    #   'queue':        'ErrorHandlerQueue',
    #   'exchange':     'FulltextExtractionExchange',
    #   'routing_key':  'ErrorHandlerRoute',
    # },
  ],
}

WORKERS = {
#   'ErrorHandlerWorker': { 
#     'concurrency': 2,
#     'publish': [
#     ],
#     'subscribe': [
#       {'queue': 'ErrorHandlerQueue',},
#     ],
#   },

  'CheckIfExtractWorker': { 
    'concurrency': 1,
    'publish': [
      {'exchange': 'FulltextExtractionExchange', 'routing_key': 'StandardFileExtractorRoute',},
    ],
    'subscribe': [
      {'queue': 'CheckIfExtractQueue',},
    ],
  },

#   'ReadRecordsWorker': { 
#     'concurrency': 4,
#     'publish': [
#       {'exchange': 'MergerPipelineExchange', 'routing_key': 'UpdateRecordsRoute',},
#     ],
#     'subscribe': [
#       {'queue': 'ReadRecordsQueue',},
#     ],
#   },

#   'UpdateRecordsWorker': {
#     'concurrency': 2,
#     'publish': [
#       {'exchange': 'MergerPipelineExchange','routing_key': 'MongoWriteRoute',},
#     ],
#     'subscribe': [
#       {'queue': 'UpdateRecordsQueue',},
#     ],
#   },
  
#   'MongoWriteWorker': {
#     'concurrency': 1,
#     'publish': [
#       {'exchange': 'MergerPipelineExchange','routing_key': 'SolrUpdateRoute',},
#     ],
#     'subscribe': [
#       {'queue':'MongoWriteQueue',},
#     ],
#   },

#   'SolrUpdateWorker': {
#     'concurrency': 7,
#     'publish': [],
#     'subscribe': [
#       {'queue':'SolrUpdateQueue',},
#     ],
#   }, 

#   'DeletionWorker': {
#     'concurrency': 1,
#     'publish': [],
#     'subscribe': [
#       {'queue':'DeletionQueue',},
#     ],
#   }, 
}



# For production/testing environment
try:
	from local_psettings import *
except ImportError as e:
	pass