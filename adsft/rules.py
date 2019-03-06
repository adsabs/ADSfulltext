META_CONTENT = {
    'xml': {
        'fulltext': {
            'xpath': ['//body',
                      '//section[@type="body"]',
                      '//journalarticle-body',
                      '//bdy',
                      '//app-group'
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
                      '//appendices',
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
    'pdf-grobid': {'grobid_fulltext': ['']},
}
