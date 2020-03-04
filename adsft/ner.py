from adsputils import setup_logging
import spacy

logger = setup_logging(__name__)

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
