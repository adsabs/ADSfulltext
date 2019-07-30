'''The xpath order is very important here because we are appending all of the results
for each xpath, rather than taking the first one that returns something other than null.
If the order is changed specifically for app-group we will have to modify our unique test.'''
META_CONTENT = {
    'xml': {
        'fulltext': {
            'tag': ['ads-body',
                      'section',
                      'journalarticle-body type:body',
                      'bdy',
                      'app-group'
            ],
            'type': 'string',
            'info': '',
            },
        'acknowledgements': {
            'tag': ['ack',
                      'section type:acknowledgments',
                      'subsection type:acknowledgement',
                      'None type="acknowledgement"'
            ],
            'type': 'string',
            'info': '',
            },
        'dataset': {
            'tag': ['named-content content-type:dataset'],
            'type': 'list',
            'info': 'xlink:href',
        }
    },
    'teixml': {
        'fulltext': {
            'tag': ['body'],
            'type': 'string',
            'info': '',
            },
        'acknowledgements': {
            'tag': ['div type:acknowledgement'],
            'type': 'string',
            'info': '',
            },
    },
    'xmlelsevier': {
        'fulltext': {
            'tag': ['ads-body',
                        'body',
                        'ja:body',
                        'ja:raw-text',
                        'ce:appendices'
            ],
            'type': 'string',
            'info': '',
            },
        'acknowledgements': {
            'tag': ['ce:acknowledgment',
                      'ce:ack',
                      'section type:acknowledgments',
                      'subsection type:acknowledgement'
            ],
            'type': 'string',
            'info': '',
            },
        'dataset': {
            'tag': ['named-content content-type:dataset'],
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
