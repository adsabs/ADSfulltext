from .models import KeyValue
from adsputils import ADSCelery
import os

class ADSFulltextCelery(ADSCelery):

    pass

# ============================= INITIALIZATION ==================================== #

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), '../'))
app = ADSFulltextCelery('ads-fulltext', proj_home=proj_home)
logger = app.logger

