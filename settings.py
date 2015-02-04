"""
Settings that are expected to be changed by the user. They influence the system as a whole
"""

import os

FULLTEXT_EXTRACT_PATH = ""
FULLTEXT_EXTRACT_PATH_UNITTEST = "tests/test_unit/stub_data"

PROJ_HOME = os.path.dirname(os.path.realpath(__file__))

config = {
    "FULLTEXT_EXTRACT_PATH": PROJ_HOME + "/"+ FULLTEXT_EXTRACT_PATH,
    "FULLTEXT_EXTRACT_PATH_UNITTEST": PROJ_HOME + "/" + FULLTEXT_EXTRACT_PATH_UNITTEST,
}

CONSTANTS = {
    "META_PATH": "meta_path",
    "FILE_SOURCE": "ft_source",
    "BIBCODE": "bibcode",
    "PROVIDER": "provider",
    "UPDATE": "UPDATE",
}

META_CONTENT = {
    "XML": {
        "fulltext": ['//body','//section[@type="body"]', '//journalarticle-body'],
        "acknowledgements": ['//ack', '//section[@type="acknowledgments"]', '//subsection[@type="acknowledgement" or @type="acknowledgment"]'],
        "dataset": ['//named-content[@content-type="dataset"]'],
    },
    "HTML": {
        "introduction": ['//h2[contains(.,"ntroduction")]',
                         '//h2[contains(.,"ntroduction")]',
                         '//p[contains(.,"Abstract")]',
                         ],
        "references": ['//h2[contains(.,"References")]'],
        "table": ['//table'],
        "table_links": ['//a[contains(@href, "TABLE_NAME")]'],
        "head": ['//head']
    }
}


# For production/testing environment
try:
    from local_settings import *
except ImportError as e:
    pass