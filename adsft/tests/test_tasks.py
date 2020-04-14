import sys
import os
import json


import unittest
from mock import patch
from adsft import app, tasks, checker, ner, writer
from adsmsg import FulltextUpdate
import httpretty
import spacy
from spacy.tokens import Doc


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
                'RUN_NER_FACILITIES_AFTER_EXTRACTION': True,
                'RUN_NLP_AFTER_EXTRACTION': True,
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
            with patch.object(tasks.task_output_results, 'delay', return_value=None) as task_output_results, \
                    patch.object(tasks.task_identify_facilities, 'delay', return_value=None) as identify_facilities, \
                    patch.object(tasks.task_apply_nlp_technqiues, 'delay', return_value=None) as apply_nlp:
                        tasks.task_extract(msg)
                        self.assertTrue(task_write_text.called)
                        self.assertTrue(identify_facilities.called)
                        self.assertTrue(apply_nlp.called)
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
            with patch.object(tasks.task_identify_facilities, 'delay', return_value=None) as identify_facilities, \
                    patch.object(tasks.task_output_results, 'delay', return_value=None) as task_output_results, \
                    patch.object(tasks.task_apply_nlp_technqiues, 'delay', return_value=None) as apply_nlp:
                        tasks.task_extract(msg)
                        self.assertTrue(identify_facilities.called)
                        self.assertTrue(apply_nlp.called)
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
                    'body': u'Introduction\nTHIS IS AN INTERESTING TITLE\n'
                    }
            tasks.task_output_results(msg)
            self.assertTrue(forward_message.called)
            actual = forward_message.call_args[0][0]
            #self.assertEqual(u'Introduction\n\nTHIS IS AN INTERESTING TITLE\n', actual['fulltext'])
            self.assertTrue(isinstance(actual, FulltextUpdate))
            self.assertEqual(actual.bibcode, msg['bibcode'])
            self.assertEqual(actual.body, msg['body'])

    def test_task_identify_facilities(self):

        with patch('adsft.writer.write_file', return_value=None) as task_write_text:
            msg = {
                    'bibcode': 'fta',
                    'file_format': 'pdf',
                    'meta_path': u'{}/ft/a/meta.json'.format(self.app.conf['FULLTEXT_EXTRACT_PATH']),
                    'acknowledgements': 'We thank the Alma team.',
                    }

            with patch('adsft.checker.load_meta_file', return_value=msg) as load_meta:
                msg = {
                        'bibcode': 'fta',
                        'file_format': 'pdf',
                        'meta_path': u'{}/ft/a/meta.json'.format(self.app.conf['FULLTEXT_EXTRACT_PATH']),
                        'acknowledgements': u'We thank the Alma team.',
                        'fulltext': u'Introduction\nTHIS IS AN INTERESTING TITLE\n'
                        }

                with patch('adsft.reader.read_content', return_value=msg) as read_content:
                    facs = ['facility0', 'facility1', 'facility1']

                    with patch('adsft.ner.get_facilities', return_value=facs) as get_facs:
                        tasks.task_identify_facilities(msg)
                        self.assertTrue(load_meta.called)
                        self.assertTrue(read_content.called)
                        self.assertTrue(get_facs.called)
                        self.assertTrue(task_write_text.called)

                        actual = task_write_text.call_args[0][1]
                        self.assertEqual(actual['facility-ack'], list(set(facs)))
                        self.assertEqual(actual['facility-ft'], list(set(facs)))

                    # test when facilties are not found, this will test the logic with logs when we move to python3
                    with patch('adsft.ner.get_facilities', return_value=[]) as get_facs:
                        tasks.task_identify_facilities(msg)
                        # use logging to check logic here when we switch to python3

                # send empty acknowledgements, test logging in python3
                msg = {
                        'bibcode': 'fta',
                        'file_format': 'pdf',
                        'meta_path': u'{}/ft/a/meta.json'.format(self.app.conf['FULLTEXT_EXTRACT_PATH']),
                        }

                with patch('adsft.checker.load_meta_file', return_value=msg) as load_meta:
                    tasks.task_identify_facilities(msg)
                    # use logging to check logic here when we switch to python3

    def test_task_apply_nlp(self):

        msg = {
                'bibcode': 'fta',
                'file_format': 'pdf',
                'meta_path': u'{}/ft/a/meta.json'.format(self.app.conf['FULLTEXT_EXTRACT_PATH']),
                'acknowledgements': u'We thank the Alma team.',
                'fulltext': u'Introduction\nTHIS IS AN INTERESTING TITLE\nThe Hubble Space Telescope was launched in 1990.'
                }

        with patch('adsft.writer.write_file', return_value=None) as task_write_text, \
                patch('adsft.checker.load_meta_file', return_value=None) as load_meta, \
                patch('adsft.reader.read_content', return_value=msg) as read_content:
                    tasks.task_apply_nlp_technqiues(read_content())
                    self.assertTrue(load_meta.called)
                    self.assertTrue(read_content.called)
                    self.assertTrue(task_write_text.called)
                    actual = task_write_text.call_args
                    self.assertEqual(os.path.dirname(msg['meta_path'])+'/nlp.bin', actual[0][0])

                    model = spacy.load(tasks.app.conf['NLP_MODEL'])
                    doc = Doc(model.vocab).from_bytes(actual[0][1])
                    tokens = [tok.text for tok in doc]
                    ents = [(ent.text, ent.label_) for ent in doc.ents]
                    chunks = [chunk.text for chunk in doc.noun_chunks]
                    sents = [(sent.text, sent.start_char, sent.end_char) for sent in doc.sents]
                    self.assertEqual(tokens, [u'Introduction',
                                                    u'\n',
                                                    u'THIS',
                                                    u'IS',
                                                    u'AN',
                                                    u'INTERESTING',
                                                    u'TITLE',
                                                    u'\n',
                                                    u'The',
                                                    u'Hubble',
                                                    u'Space',
                                                    u'Telescope',
                                                    u'was',
                                                    u'launched',
                                                    u'in',
                                                    u'1990',
                                                    u'.'])
                    self.assertEqual(ents, [(u'1990', u'DATE')])
                    self.assertEqual(chunks, [u'Introduction',
                                                    u'AN INTERESTING TITLE',
                                                    u'The Hubble Space Telescope'])
                    self.assertEqual(sents, [(u'Introduction\n', 0, 13),
                                                    (u'THIS IS AN INTERESTING TITLE\n', 13, 42),
                                                    (u'The Hubble Space Telescope was launched in 1990.', 42, 90)])



if __name__ == '__main__':
    unittest.main()
