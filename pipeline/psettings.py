"""
Settings for the rabbitMQ/ADSfulltext
"""

__author__ = 'J. Elliott'
__maintainer__ = 'J. Elliott'
__copyright__ = 'Copyright 2015'
__version__ = '1.0'
__email__ = 'ads@cfa.harvard.edu'
__status__ = 'Production'
__credit__ = ['V. Sudilovsky']
__license__ = 'GPLv3'

# Travis-CI uses guest:guest
# Max message size = 500kb
RABBITMQ_URL = 'amqp://guest:guest@localhost:5672/adsfulltext?' \
               'socket_timeout=10&backpressure_detection=t'

POLL_INTERVAL = 15  # per-worker poll interval (to check health) in seconds.

ERROR_HANDLER = {
    'exchange': 'FulltextExtractionExchange',
    'routing_key': 'ErrorHandlerRoute',
}

PDF_EXTRACTOR = {
    'exchange': 'FulltextExtractionExchange',
    'routing_key': 'PDFFileExtractorRoute',
    'class_name': 'org.adslabs.adsfulltext.PDFExtractList',
}

PROXY_PUBLISH = {
    'exchange': 'MergerPipelineExchange',
    'routing_key': 'ReingestRecordsRoute',
    'queue': 'ReingestRecordsQueue',
    'RABBITMQ_URL': 'amqp://guest:guest@localhost:5672/ADSimportpipeline?'
                    'socket_timeout=10&backpressure_detection=t',
}

RABBITMQ_ROUTES = {
    'EXCHANGES': [
        {
            'exchange': 'FulltextExtractionExchange',
            'exchange_type': 'direct',
            'passive': False,
            'durable': True,
            },
        ],
    'QUEUES': [
        {
            'queue': 'CheckIfExtractQueue',
            'durable': True,
            },
        {
            'queue': 'PDFFileExtractorQueue',
            'durable': True,
            },
        {
            'queue': 'StandardFileExtractorQueue',
            'durable': True,
            },
        {
            'queue': 'WriteMetaFileQueue',
            'durable': True,
            },
        {
            'queue': 'ErrorHandlerQueue',
            'durable': True,
            },
        {
            'queue': 'ProxyPublishQueue',
            'durable': True,
            },
        ],
    'BINDINGS': [
        {
            'queue': 'CheckIfExtractQueue',
            'exchange': 'FulltextExtractionExchange',
            'routing_key': 'CheckIfExtractRoute',
            },
        {
            'queue': 'PDFFileExtractorQueue',
            'exchange': 'FulltextExtractionExchange',
            'routing_key': 'PDFFileExtractorRoute',
            },
        {
            'queue': 'StandardFileExtractorQueue',
            'exchange': 'FulltextExtractionExchange',
            'routing_key': 'StandardFileExtractorRoute',
            },
        {
            'queue': 'WriteMetaFileQueue',
            'exchange': 'FulltextExtractionExchange',
            'routing_key': 'WriteMetaFileRoute',
            },
        {
            'queue': 'ErrorHandlerQueue',
            'exchange': 'FulltextExtractionExchange',
            'routing_key': 'ErrorHandlerRoute',
            },
        {
            'queue': 'ProxyPublishQueue',
            'exchange': 'FulltextExtractionExchange',
            'routing_key': 'ProxyPublishRoute',
            },
        ],
    }

WORKERS = {
    'CheckIfExtractWorker': {
        'concurrency': 1,
        'publish': {
            'PDF': [
                {
                    'exchange': 'FulltextExtractionExchange',
                    'routing_key': 'PDFFileExtractorRoute',
                    }
            ],
            'Standard': [
                {
                    'exchange': 'FulltextExtractionExchange',
                    'routing_key': 'StandardFileExtractorRoute',
                    }
            ],
            },
        'subscribe': [
            {'queue': 'CheckIfExtractQueue',},
            ],
        },
    'StandardFileExtractWorker': {
        'concurrency': 1,
        'publish': [
            {
                'exchange': 'FulltextExtractionExchange',
                'routing_key': 'WriteMetaFileRoute',
                },
            ],
        'subscribe': [
            {'queue': 'StandardFileExtractorQueue',},
            ],
        },
    'WriteMetaFileWorker': {
        'concurrency': 1,
        'publish': [
            {
                'exchange': 'FulltextExtractionExchange',
                'routing_key': 'ProxyPublishRoute',
                },
            ],
        'subscribe': [
            {'queue': 'WriteMetaFileQueue',},
            ],
        },
    'ErrorHandlerWorker': {
        'concurrency': 1,
        'publish': [],
        'subscribe': [
            {'queue': 'ErrorHandlerQueue',},
            ],
        },
    'ProxyPublishWorker': {
        'concurrency': 1,
        'publish': [],
        'subscribe': [
            {'queue': 'ProxyPublishQueue',},
            ],
        },
    }


# For production/testing environment
try:
    from local_psettings import *

except ImportError as e:
    pass
