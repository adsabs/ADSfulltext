import sys
import os
import json

from mock import patch
import unittest
from adsft import app, tasks
from adsft.models import Base


class TestWorkers(unittest.TestCase):
    
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.proj_home = os.path.join(os.path.dirname(__file__), '../..')
        self._app = tasks.app
        self.app = app.ADSFulltextCelery('test',
            {
            'SQLALCHEMY_URL': 'sqlite:///',
            'SQLALCHEMY_ECHO': False
            })
        tasks.app = self.app # monkey-patch the app object
        Base.metadata.bind = self.app._session.get_bind()
        Base.metadata.create_all()
    
    
    def tearDown(self):
        unittest.TestCase.tearDown(self)
        Base.metadata.drop_all()
        self.app.close_app()
        tasks.app = self._app


    def test_task_hello_world(self):
        
        # just for illustration how to mock multiple objects in one go
        with patch.object(self.app, 'close_app') as example_method, \
            patch.object(tasks.logger, 'info') as logger:
            
            tasks.task_hello_world({'name': 'Elgar'})
            self.assertTrue('Hello Elgar we have recorded' in logger.call_args[0][0])
            


            
            

if __name__ == '__main__':
    unittest.main()