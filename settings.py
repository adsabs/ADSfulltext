"""
Settings that are expected to be changed by the user. They influence the system
as a whole
"""

__author__ = 'J. Elliott'
__maintainer__ = 'J. Elliott'
__copyright__ = 'Copyright 2015'
__version__ = '1.0'
__email__ = 'ads@cfa.harvard.edu'
__status__ = 'Production'
__credit__ = ['V. Sudilovsky']
__license__ = 'GPLv3'

import os

FULLTEXT_EXTRACT_PATH = '/vagrant/live'
FULLTEXT_EXTRACT_PATH_UNITTEST = 'tests/test_unit/stub_data'

PROJ_HOME = os.path.dirname(os.path.realpath(__file__))

config = {
    'FULLTEXT_EXTRACT_PATH': FULLTEXT_EXTRACT_PATH,
    'FULLTEXT_EXTRACT_PATH_UNITTEST':
        os.path.join(PROJ_HOME, FULLTEXT_EXTRACT_PATH_UNITTEST),
    'LOGGING_LEVEL': 'INFO',
}

CONSTANTS = {
    'META_PATH': 'meta_path',
    'FILE_SOURCE': 'ft_source',
    'BIBCODE': 'bibcode',
    'PROVIDER': 'provider',
    'UPDATE': 'UPDATE',
    'FULL_TEXT': 'fulltext',
    'FORMAT': 'file_format',
    'TIME_STAMP': 'index_date',
    'ACKNOWLEDGEMENTS': 'acknowledgements',
    'DATASET': 'dataset',
}

META_CONTENT = {
    'xml': {
        'fulltext': {
            'xpath': ['//body',
                      '//section[@type="body"]',
                      '//journalarticle-body'
                      ],
            'type': 'string',
            'info': '',
            },
        'acknowledgements': {
            'xpath': ['//ack',
                      '//section[@type="acknowledgments"]',
                      '//subsection[@type="acknowledgement" '
                      'or @type="acknowledgment"]'
                      ],
            'type': 'string',
            'info': '',
            },
        'dataset': {
            'xpath': ['//named-content[@content-type="dataset"]'],
            'type': 'list',
            'info': 'xlink:href',
        }
    },
    'teixml': {
        'fulltext': {
            'xpath': ['//body',
                      ],
            'type': 'string',
            'info': '',
            },
        'acknowledgements': {
            'xpath': ['//div[@type="acknowledgement"]',
                      ],
            'type': 'string',
            'info': '',
            },
    },
    'xmlelsevier': {
        'fulltext': {
            'xpath': ['//body',
                      '//raw-text',
                      ],
            'type': 'string',
            'info': '',
            },
        'acknowledgements': {
            'xpath': ['//acknowledgment',
                      '//ack',
                      '//section[@type="acknowledgments"]',
                      '//subsection[@type="acknowledgement" '
                      'or @type="acknowledgment"]',
                      '//*[local-name()="acknowledgment"]'
                      ],
            'type': 'string',
            'info': '',
            },
        'dataset': {
            'xpath': ['//named-content[@content-type="dataset"]'],
            'type': 'list',
            'info': 'xlink:href',
        }
    },
    'html': {
        'introduction': [
            '//h2[contains(.,"ntroduction")]',
            '//h3[contains(.,"ntroduction")]',
            '//p[contains(.,"Abstract")]',
            ],
        'references': [
            '//h2[contains(.,"References")]'
        ],
        'table': [
            '//table'
        ],
        'table_links': [
            '//a[contains(@href, "TABLE_NAME")]'
        ],
        'head': [
            '//head'
        ]
    },
    'txt': {'fulltext': ['']},
    'ocr': {'fulltext': ['']},
    'http': {'fulltext': ['']},
    'pdf': {'fulltext': ['']},
}


# For production/testing environment
try:
    from local_settings import *

except ImportError as e:
    pass
