from adsputils import setup_logging
import spacy
import os
import pkgutil

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

    model = None
    packageExists = pkgutil.find_loader(dir) is not None
    dirExists = os.path.isdir(dir)

    if dirExists or packageExists:
        model = spacy.load(dir)

    return model
