import unittest
import os
import re

from adsft import utils, checker
from adsft.tests import test_base

class TestCheckIfExtracted(test_base.TestUnit):
    """
    Tests the CheckIfExtract worker's methods, i.e., the unit functions.
    """

    def test_file_not_extracted_before(self):
        """
        Tests the meta_output_exists function. It should find that there is not
        already a meta file that exists, which is defined in test_file_stub.

        :return: no return
        """
        FileInputStream = utils.FileInputStream(self.test_file_stub)
        FileInputStream.extract()

        payload = FileInputStream.payload[0]

        exists = checker.meta_output_exists(
            payload,
            self.app.conf['FULLTEXT_EXTRACT_PATH']
        )

        self.assertEqual(exists, False)


    def test_file_extracted_before(self):
        """
        Tests the meta_output_exists function. It should find that there is
        already a meta file that exists, which is defined in test_file_exists.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(self.test_file_exists)
        FileInputStream.extract()

        payload = FileInputStream.payload[0]

        exists = checker.meta_output_exists(
            payload,
            self.app.conf['FULLTEXT_EXTRACT_PATH']
        )

        self.assertEqual(
            exists,
            True,
            'Could not establish that this file has been extracted before'
        )


    def test_file_extract_meta(self):
        """
        Tests the load_meta_file function. Should load the meta file that exists
        on disk and checks that there is actually some content extracted.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(self.test_file_exists)
        FileInputStream.extract()

        payload = FileInputStream.payload[0]

        content = checker.load_meta_file(
            payload,
            self.app.conf['FULLTEXT_EXTRACT_PATH']
        )

        self.assertTrue(
            len(content) > 0,
            'Did not extract the meta data correctly'
        )


    def test_file_should_be_updated_if_missing_fulltext(self):
        """
        Tests the meta_needs_update function. Loads some meta content from disk,
        and then copies everything but the full text path to a new meta content
        dictionary. The meta_needs_update function should then determine that
        there is no full text content and supply the MISSING_FULL_TEXT flag.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(self.test_file_exists)
        FileInputStream.extract()

        meta_content = checker.load_meta_file(
            FileInputStream.payload[0],
            self.app.conf['FULLTEXT_EXTRACT_PATH']
        )

        new_meta_content = {}

        for key in meta_content.keys():
            if key != 'ft_source':
                new_meta_content[key] = meta_content[key]

        updated = checker.meta_needs_update(
            FileInputStream,
            new_meta_content,
            self.app.conf['FULLTEXT_EXTRACT_PATH']
        )

        self.assertEqual(updated,
                         'MISSING_FULL_TEXT',
                         'The ft_source should need updating, not {0}'
                         .format(updated))


    def test_file_should_be_updated_if_content_differs_to_input(self):
        """
        Tests the meta_needs_update function. Loads some meta content from disk,
        and then modifies the full text path to be different. The meta_needs_
        update function should then determine that the full text content differs
        and supply the DIFFERING_FULL_TEXT flag.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(self.test_file_exists)
        FileInputStream.extract()
        payload = FileInputStream.payload[0]

        meta_content = checker.load_meta_file(
            payload,
            self.app.conf['FULLTEXT_EXTRACT_PATH']
        )

        meta_content['ft_source'] = ''

        updated = checker.meta_needs_update(
            payload,
            meta_content,
            self.app.conf['FULLTEXT_EXTRACT_PATH']
        )

        self.assertEqual(updated,
                         'DIFFERING_FULL_TEXT',
                         'The ft_source should need updating, not {0}'
                         .format(updated)
        )


    def test_file_should_be_updated_if_content_is_stale(self):
        """
        Tests the meta_needs_update function. Loads meta data from the disk, and
        finds the full text path. Opens the full text file and writes some fresh
        content so that it is more new than the meta data file. This will result
        in the meta_needs_update supplying the STALE_CONTENT flag.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(self.test_file_exists)
        FileInputStream.extract()

        # Ensure the PDF more new than the meta.json
        payload = FileInputStream.payload[0]
        with open(payload['ft_source'], 'w') as not_stale:
            not_stale.write('PDF')

        # Not a nicer way to do this without cleaning up some tests
        meta_content = checker.load_meta_file(
            payload,
            self.app.conf['FULLTEXT_EXTRACT_PATH']
        )

        meta_content['ft_source'] \
            = os.path.join(self.app.conf['PROJ_HOME'], meta_content['ft_source'])

        updated = checker.meta_needs_update(
            payload,
            meta_content,
            self.app.conf['FULLTEXT_EXTRACT_PATH']
        )

        self.assertEqual(updated,
                         'STALE_CONTENT',
                         'The file content should be stale, not {0} ({1}\n{2})'
                         .format(updated, payload, meta_content)
                         )

    def test_file_should_be_extracted(self):
        """
        Tests the check_if_extract function. Calculates how many references
        there are to PDFs, and the remainder are 'Standard files', e.g., XML,
        HTTP, HTML, etc. From this payload, it runs check_if_extract and ensures
        that all of the outputs contain an expected UPDATE flag, and that there
        are the correct number of PDFs in the PDF queue, and the right number of
        StandardFiles in the StandardFiles queue.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(self.test_file)
        FileInputStream.extract()

        with open(self.test_file, 'r') as in_f:
            text = in_f.read()
        pdf_re = re.compile('pdf')
        pdf_number = len(pdf_re.findall(text))
        standard_number = \
            len([i for i in text.split('\n') if i != '']) - pdf_number

        payload = checker.check_if_extract(
            FileInputStream.payload, self.app.conf['FULLTEXT_EXTRACT_PATH']

        )
        pdf_payload = payload['PDF']
        standard_payload = payload['Standard']

        if pdf_payload:

            pdf_compare = [
                content for content in payload['PDF']
                if content['UPDATE']
                in [u'STALE_CONTENT',
                    u'DIFFERING_FULL_TEXT',
                    u'MISSING_FULL_TEXT"'
                    u'NOT_EXTRACTED_BEFORE']
            ]

        else:
            pdf_compare = []

        if standard_payload:

            standard_compare = [
                content for content in payload['Standard']
                if content['UPDATE']
                in [u'STALE_CONTENT',
                    u'DIFFERING_FULL_TEXT',
                    u'MISSING_FULL_TEXT',
                    u'NOT_EXTRACTED_BEFORE']
            ]

        else:
            standard_compare = []

        self.assertTrue(len(pdf_compare) == pdf_number, pdf_number)
        self.assertTrue(len(standard_compare) == standard_number)

    def test_output_dictionary_contains_everything_we_need(self):
        """
        Tests the check_if_extract function. Runs the function on a stub file
        that contains one document and then ensures that the output dictionary
        contains all the expected meta data. It also checks that the correct
        file format has been associated to it.

        :return: no return
        """

        FileInputStream = utils.FileInputStream(self.test_single_document)
        FileInputStream.extract()

        payload = checker.check_if_extract(
            FileInputStream.payload, self.app.conf['FULLTEXT_EXTRACT_PATH']
        )

        expected_content = ['ft_source', 'bibcode',
                            'provider', 'file_format',
                            'UPDATE', 'meta_path',
                            'index_date']
        expected_content = [unicode(i) for i in expected_content]
        expected_content.sort()

        actual_content = payload['Standard'][0].keys()
        actual_format = payload['Standard'][0]['file_format']

        actual_content.sort()
        self.assertListEqual(actual_content, expected_content)
        self.assertEqual(actual_format, 'txt')

    def test_that_no_payload_gets_sent_if_there_is_no_content(self):
        """
        Tests check_if_extract function. The stub data contains no PDF files.
        This means there should be nothing inside the PDF list returned within
        the payload. If there is, there is a problem.

        :return: no return
        """
        FileInputStream = utils.FileInputStream(self.test_single_document)
        FileInputStream.extract()

        payload = checker.check_if_extract(
            FileInputStream.payload, self.app.conf['FULLTEXT_EXTRACT_PATH']
        )

        self.assertFalse(payload['PDF'])
        self.assertTrue(len(payload['Standard']) != 0)

    def test_that_file_should_be_updated_if_forced(self):
        """
        If the dictionary contains a force value in the update keyword, then
        the worker should pass on the content regardless of whether it passes
        any other checks
        :return: no return
        """

        FileInputStream_true = utils.FileInputStream(self.test_file_exists)
        FileInputStream_true.extract(force_extract=True)

        FileInputStream_false = utils.FileInputStream(self.test_file_exists)
        FileInputStream_false.extract(force_extract=False)

        payload_true = checker.check_if_extract(
            FileInputStream_true.payload,
            self.app.conf['FULLTEXT_EXTRACT_PATH']
        )
        first_doc_true = payload_true['PDF'][0]

        payload_false = checker.check_if_extract(
            FileInputStream_false.payload,
            self.app.conf['FULLTEXT_EXTRACT_PATH']
        )
        first_doc_false = payload_true['PDF'][0]


        self.assertTrue(first_doc_true['UPDATE'],
                        'FORCE_TO_EXTRACT')
        self.assertTrue(len(payload_false['PDF']) != 0)

        self.assertTrue(first_doc_false['UPDATE'],
                        'DIFFERING_FULL_TEXT')
        self.assertTrue(len(payload_false['PDF']) != 0)
            

if __name__ == '__main__':
    unittest.main()