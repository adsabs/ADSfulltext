import sys
import os
import json

from mock import patch
import unittest
from adsft import app, tasks


class TestWorkers(unittest.TestCase):
    
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.proj_home = os.path.join(os.path.dirname(__file__), '../..')
        self._app = tasks.app
        self.app = app.ADSFulltextCelery('test', local_config=\
            {
            })
        tasks.app = self.app # monkey-patch the app object
    
    
    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.app.close_app()
        tasks.app = self._app


            


            
            

if __name__ == '__main__':
    unittest.main()