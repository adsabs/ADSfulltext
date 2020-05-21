import os
import spacy

# ============================= INITIALIZATION ==================================== #
# - Use app logger:
#import logging
#logger = logging.getLogger('ads-fulltext')
# - Or individual logger for this file:
from adsputils import setup_logging, load_config
proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), '../'))
config = load_config(proj_home=proj_home)
logger = setup_logging(__name__, proj_home=proj_home,
                        level=config.get('LOGGING_LEVEL', 'INFO'),
                        attach_stdout=config.get('LOG_STDOUT', False))


# =============================== FUNCTIONS ======================================= #

def get_facilities(model, text):

    """
    purpose: to identify facilities within the text
    input: model loaded from disk, text to process
    return: list of facilities identified with custom spacy ner model
    """

    doc = model(text)

    facilities = []

    for ent in doc.ents:
        facilities.append(ent.text)

    return facilities

def load_model(dir):

    return spacy.load(dir)
