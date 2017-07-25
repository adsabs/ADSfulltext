import sys
import os
import json

from mock import patch
import unittest
from adsft import app, tasks
from adsmsg import FulltextUpdate


class TestWorkers(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.proj_home = tasks.app.conf['PROJ_HOME']
        self._app = tasks.app
        self.app = app.ADSFulltextCelery('test', proj_home=self.proj_home, local_config=\
            {
            })
        tasks.app = self.app # monkey-patch the app object


    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.app.close_app()
        tasks.app = self._app



    def test_task_check_if_extract(self):
        with patch.object(tasks, 'task_extract', return_value=None) as task_extract:

            message = {'bibcode': 'fta', 'provider': 'MNRAS',
                       'ft_source': '{}/tests/test_integration/stub_data/full_test.txt'.format(self.proj_home)}
            tasks.task_check_if_extract(message, diagnostics=True)
            self.assertTrue(task_extract.called)
            expected = {'bibcode': 'fta', 'file_format': 'txt',
                        #'index_date': '2017-06-30T22:45:47.800112Z',
                        'UPDATE': 'NOT_EXTRACTED_BEFORE',
                        'meta_path': u'{}/ft/a/meta.json'.format(self.app.conf['FULLTEXT_EXTRACT_PATH']),
                        'ft_source': '{}/tests/test_integration/stub_data/full_test.txt'.format(self.proj_home),
                        'provider': 'MNRAS'}
            actual = task_extract.call_args[0][0]
            self.assertDictContainsSubset(expected, actual)
            self.assertTrue('index_date' in actual)


        with patch.object(tasks, 'task_extract', return_value=None) as task_extract:

            message = {'bibcode': 'fta', 'provider': 'MNRAS',
                       'ft_source': '{}/tests/test_integration/stub_data/full_test.pdf'.format(self.proj_home)}
            tasks.task_check_if_extract(message, diagnostics=True)
            self.assertTrue(task_extract.called)

            expected = {'bibcode': 'fta', 'file_format': 'pdf',
                        #'index_date': '2017-06-30T22:45:47.800112Z',
                        'UPDATE': 'NOT_EXTRACTED_BEFORE',
                        'meta_path': u'{}/ft/a/meta.json'.format(self.app.conf['FULLTEXT_EXTRACT_PATH']),
                        'ft_source': '{}/tests/test_integration/stub_data/full_test.pdf'.format(self.proj_home),
                        'provider': 'MNRAS'}
            actual = task_extract.call_args[0][0]
            self.assertDictContainsSubset(expected, actual)
            self.assertTrue('index_date' in actual)



    def test_task_extract_standard(self):
        with patch('adsft.writer.write_content', return_value=None) as task_write_text:
            msg = {'bibcode': 'fta', 'file_format': 'txt',
                        'index_date': '2017-06-30T22:45:47.800112Z',
                        'UPDATE': 'NOT_EXTRACTED_BEFORE',
                        'meta_path': u'{}/ft/a/meta.json'.format(self.app.conf['FULLTEXT_EXTRACT_PATH']),
                        'ft_source': '{}/tests/test_integration/stub_data/full_test.txt'.format(self.proj_home),
                        'provider': 'MNRAS'}
            with patch.object(tasks, 'task_output_results', return_value=None) as task_output_results:
                tasks.task_extract(msg, diagnostics=True)
                self.assertFalse(task_write_text.called)
                self.assertTrue(task_output_results.called)


    def test_task_extract_pdf(self):
        with patch('adsft.writer.write_content', return_value=None) as task_write_text:
            msg = {'bibcode': 'fta', 'file_format': 'pdf',
                        'index_date': '2017-06-30T22:45:47.800112Z',
                        'UPDATE': 'NOT_EXTRACTED_BEFORE',
                        'meta_path': u'{}/ft/a/meta.json'.format(self.app.conf['FULLTEXT_EXTRACT_PATH']),
                        'ft_source': '{}/tests/test_integration/stub_data/full_test.pdf'.format(self.proj_home),
                        'provider': 'MNRAS'}
            with patch.object(tasks, 'task_output_results', return_value=None) as task_output_results:
                tasks.task_extract(msg, diagnostics=True)
                self.assertFalse(task_write_text.called)
                self.assertTrue(task_output_results.called)

    def test_task_output_results(self):
        with patch('adsft.app.ADSFulltextCelery.forward_message', return_value=None) as forward_message:
            msg = {
                    'bibcode': 'fta',
                    'body': 'Introduction\nTHIS IS AN INTERESTING TITLE\n'
                    }
            tasks.task_output_results(msg, diagnostics=True)
            self.assertFalse(forward_message.called)

if __name__ == '__main__':
    unittest.main()
