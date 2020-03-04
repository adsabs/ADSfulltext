import sys
import os
import json

from mock import patch
import unittest
from adsft import app, tasks, checker
from adsmsg import FulltextUpdate
import httpretty


class TestWorkers(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.proj_home = tasks.app.conf['PROJ_HOME']
        self.grobid_service = tasks.app.conf['GROBID_SERVICE']
        self._app = tasks.app
        self.app = app.ADSFulltextCelery('test', proj_home=self.proj_home, local_config=\
            {
                "CELERY_ALWAYS_EAGER": False,
                "CELERY_EAGER_PROPAGATES_EXCEPTIONS": False,
            })
        tasks.app = self.app # monkey-patch the app object


    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.app.close_app()
        tasks.app = self._app



    def test_task_check_if_extract(self):
        with patch.object(tasks.task_extract, 'delay', return_value=None) as task_extract:

            message = {'bibcode': 'fta', 'provider': 'MNRAS',
                       'ft_source': '{}/tests/test_integration/stub_data/full_test.txt'.format(self.proj_home)}
            tasks.task_check_if_extract(message)
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


        with patch.object(tasks.task_extract, 'delay', return_value=None) as task_extract:

            message = {'bibcode': 'fta', 'provider': 'MNRAS',
                       'ft_source': '{}/tests/test_integration/stub_data/full_test.pdf'.format(self.proj_home)}
            tasks.task_check_if_extract(message)
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
            msg = {'bibcode': 'fta', 'file_format': 'xml',
                        'index_date': '2017-06-30T22:45:47.800112Z',
                        'UPDATE': 'NOT_EXTRACTED_BEFORE',
                        'meta_path': u'{}/ft/a/meta.json'.format(self.app.conf['FULLTEXT_EXTRACT_PATH']),
                        'ft_source': '{}/tests/test_integration/stub_data/full_test.xml'.format(self.proj_home),
                        'provider': 'MNRAS'}
            with patch.object(tasks.task_output_results, 'delay', return_value=None) as task_output_results:
                tasks.task_extract(msg)
                self.assertTrue(task_write_text.called)
                actual = task_write_text.call_args[0][0]

                self.assertEqual(u'I. INTRODUCTION INTRODUCTION GOES HERE Manual Entry TABLE I. TEXT a NOTES a TEXT\nAPPENDIX: APPENDIX TITLE GOES HERE APPENDIX CONTENT', actual['fulltext'])
                self.assertEqual(u'Acknowledgments WE ACKNOWLEDGE.', actual['acknowledgements'])
                self.assertEqual([u'ADS/Sa.CXO#Obs/11458'], actual['dataset'])
                self.assertTrue(task_output_results.called)


    def test_task_extract_pdf(self):
        if self.grobid_service is not None:
            httpretty.enable()
            expected_grobid_fulltext = "<hello/>"
            httpretty.register_uri(httpretty.POST, self.grobid_service,
                           body=expected_grobid_fulltext,
                           status=200)
        with patch('adsft.writer.write_content', return_value=None) as task_write_text:
            msg = {'bibcode': 'fta', 'file_format': 'pdf',
                        'index_date': '2017-06-30T22:45:47.800112Z',
                        'UPDATE': 'NOT_EXTRACTED_BEFORE',
                        'meta_path': u'{}/ft/a/meta.json'.format(self.app.conf['FULLTEXT_EXTRACT_PATH']),
                        'ft_source': '{}/tests/test_integration/stub_data/full_test.pdf'.format(self.proj_home),
                        'provider': 'MNRAS'}
            with patch.object(tasks.task_output_results, 'delay', return_value=None) as task_output_results:
                with patch.object(tasks.task_output_results, 'delay', return_value=None) as task_output_results:
                    tasks.task_extract(msg)
                self.assertTrue(task_write_text.called)
                actual = task_write_text.call_args[0][0]
                #self.assertEqual(u'Introduction\nTHIS IS AN INTERESTING TITLE\n', actual['fulltext']) # PDFBox
                self.assertEqual(u'Introduction THIS IS AN INTERESTING TITLE', actual['fulltext']) # pdftotext
                if self.grobid_service is not None:
                    self.assertEqual(expected_grobid_fulltext, actual['grobid_fulltext'])
                self.assertTrue(task_output_results.called)

    def test_task_output_results(self):
        with patch('adsft.app.ADSFulltextCelery.forward_message', return_value=None) as forward_message:
            msg = {
                    'bibcode': 'fta',
                    'body': 'Introduction\nTHIS IS AN INTERESTING TITLE\n'
                    }
            tasks.task_output_results(msg)
            self.assertTrue(forward_message.called)
            actual = forward_message.call_args[0][0]
            #self.assertEqual(u'Introduction\n\nTHIS IS AN INTERESTING TITLE\n', actual['fulltext'])
            self.assertTrue(isinstance(actual, FulltextUpdate))
            self.assertEqual(actual.bibcode, msg['bibcode'])
            self.assertEqual(actual.body, msg['body'])

    def test_task_identify_facilities(self):
        with patch('adsft.writer.write_content', return_value=None) as task_write_text:
            msg = {
                    'bibcode': 'fta',
                    'acknowledgements': 'We thank the Alma team.',
                    'fulltext': 'Introduction\nTHIS IS AN INTERESTING TITLE\n'
                    }

            with patch('adsft.checker.load_meta_file', return_value=msg) as load_meta:
                facs = ['facility0', 'facility1', 'facility1']

                with patch('adsft.ner.get_facilities', return_value=facs) as get_facs:
                    tasks.task_identify_facilities(msg)
                    self.assertTrue(task_write_text.called)
                    actual = task_write_text.call_args[0][0]
                    self.assertEqual(actual['facility-ack'], list(set(facs)))
                    self.assertEqual(actual['facility-ft'], list(set(facs)))

                # should test the logging when we move to python3
                with patch('adsft.ner.get_facilities', return_value=[]) as get_facs:
                    tasks.task_identify_facilities(msg)

            # send empty acknowledgements and fulltext, test logging in python3
            msg = {
                    'bibcode': 'fta',
                    }

            with patch('adsft.checker.load_meta_file', return_value=msg) as load_meta:
                tasks.task_identify_facilities(msg)


if __name__ == '__main__':
    unittest.main()
