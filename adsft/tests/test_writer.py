import unittest
import os

from adsft import writer
from adsft.tests import test_base
import json






class TestWriteMetaFileWorker(test_base.TestUnit):
    """
    Class that tests the methods used to write meta files and the full text
    content to disk, and pass on to other relevant RabbitMQ queues.
    """

    def setUp(self):
        """
        Generic setup of the test class. Makes a dictionary item that the worker
        would expect to receive from the RabbitMQ instance. Loads the relevant
        worker as well into a class attribute so it is easier to access.

        :return: no return
        """
        super(TestWriteMetaFileWorker, self).setUp()
        self.dict_item = {
            'meta_path': os.path.join(
                self.app.conf['PROJ_HOME'], 'tests/test_unit/stub_data/te/st/1/meta.json'
            ),
            'fulltext': 'hehehe I am the full text',
            'file_format': 'xml',
            'ft_source': '/vagrant/source.txt',
            'bibcode': 'MNRAS2014',
            'provider': 'MNRAS',
            'UPDATE': 'MISSING_FULL_TEXT',
            'lang': 'en'
        }

        self.meta_file = self.dict_item['meta_path']

        self.bibcode_pair_tree = \
            self.dict_item['meta_path'].replace('meta.json', '')

        self.full_text_file = self.bibcode_pair_tree + 'fulltext.txt'

        self.acknowledgement_file = \
            self.bibcode_pair_tree + 'acknowledgements.txt'

    def tearDown(self):
        """
        Generic tear down of the test class. It deletes the meta.json file, the
        full text file, and the root directory that contains these files.

        :return: no return
        """
        try:
            os.remove(self.meta_file)
        except OSError:
            pass

        try:
            os.remove(self.full_text_file)
        except OSError:
            pass

        try:
            os.rmdir(self.bibcode_pair_tree)
        except OSError:
            pass

    def test_loads_the_content_correctly_and_makes_folders(self):
        """
        Tests the write_content method. Checks that the folder to contain the
        full text and meta data is created.

        :return: no return
        """

        content = writer.write_content(self.dict_item)

        self.assertTrue(os.path.exists(self.bibcode_pair_tree),
                        msg=os.path.exists(self.bibcode_pair_tree))

    def test_loads_the_content_correctly_and_makes_meta_file(self):
        """
        Tests the write_content method. Checks that the meta_file is created and
        is saved to disk.

        :return: no return
        """

        content = writer.write_content(self.dict_item)

        self.assertTrue(os.path.exists(self.meta_file),
                        msg=os.path.exists(self.meta_file))

    def test_loads_the_content_correctly_and_makes_full_text_file(self):
        """
        Tests the write_content method. Checks that the full text file is
        created and saved to disk.

        :return: no return
        """

        content = writer.write_content(self.dict_item)

        self.assertTrue(os.path.exists(self.full_text_file),
                        msg=os.path.exists(self.full_text_file))

    def test_pipeline_extract_content_extracts_fulltext_correctly(self):
        """
        Tests the extract_content method. Checks that the full text written to
        disk matches the ful text that we expect to be written to disk.

        N. B.
        Do not let the name extract_content portray anything. It is simply to
        keep the same naming convention as the other workers. extract_content
        is the main method the worker will run.

        :return: no return
        """

        self.dict_item['file_format'] = 'txt'
        pipeline_payload = [self.dict_item]

        return_payload = writer.extract_content(pipeline_payload)

        self.assertTrue(return_payload, 1)

        full_text = ''
        with open(
                self.dict_item['meta_path']
                        .replace('meta.json', 'fulltext.txt'), 'r'
        ) as full_text_file:

            full_text = full_text_file.read()

        self.assertEqual(self.dict_item['fulltext'], full_text)

    def test_pipeline_extract_content_extracts_meta_text_correctly(self):
        """
        Tests the extract_content method. Checks that the meta.json file written
        to disk contains the content that we expect to be there.

        N. B.
        Do not let the name extract_content portray anything. It is simply to
        keep the same naming convention as the other workers. extract_content
        is the main method the worker will run.

        :return: no return
        """

        self.dict_item['file_format'] = 'txt'
        pipeline_payload = [self.dict_item]

        return_payload = writer.extract_content(pipeline_payload)

        self.assertTrue(return_payload, 1)

        meta_dict = {}
        with open(self.dict_item['meta_path'], 'r') as meta_file:
            meta_dict = json.load(meta_file)

        self.assertEqual(
            self.dict_item['ft_source'],
            meta_dict['ft_source']
        )
        self.assertEqual(
            self.dict_item['bibcode'],
            meta_dict['bibcode']
        )
        self.assertEqual(
            self.dict_item['provider'],
            meta_dict['provider']
        )
        self.assertEqual(
            self.dict_item['UPDATE'],
            meta_dict['UPDATE']
        )
        self.assertEqual(
            self.dict_item['lang'],
            meta_dict['lang']
        )

    def pipeline_extract(self, format_):
        """
        Helper function that writes a meta.json and checks that the content on
        disk matches what we expect to be there.

        N. B.
        Do not let the name extract_content portray anything. It is simply to
        keep the same naming convention as the other workers. extract_content
        is the main method the worker will run.

        :param format_: file format to be in the meta.json
        :return: no return
        """

        self.dict_item['file_format'] = format_
        pipeline_payload = [self.dict_item]

        return_payload = writer.extract_content(pipeline_payload)

        self.assertTrue(return_payload == '["MNRAS2014"]')

        meta_dict = {}
        with open(self.dict_item['meta_path'], 'r') as meta_file:
            meta_dict = json.load(meta_file)

        self.assertEqual(
            self.dict_item['ft_source'],
            meta_dict['ft_source']
        )
        self.assertEqual(
            self.dict_item['bibcode'],
            meta_dict['bibcode']
        )
        self.assertEqual(
            self.dict_item['provider'],
            meta_dict['provider']
        )
        self.assertEqual(
            self.dict_item['UPDATE'],
            meta_dict['UPDATE']
        )
        self.assertEqual(
            self.dict_item['lang'],
            meta_dict['lang']
        )

    def test_pipeline_extract_works_for_all_formats(self):
        """
        Tests the extract_content method. Runs the extract_content method on all
        the possible types of extensions to ensure that no strange behaviour
        occurs.

        :return: no return
        """

        for format_ in ['txt', 'xml', 'xmlelsevier', 'ocr', 'html', 'http']:
            try:
                self.pipeline_extract(format_)
            except Exception:
                raise Exception

    def test_acknowledgements_file_is_created(self):
        """
        Tests the extract_content method. Checks that both a fulltext.txt and a
        acknowledgements.txt file is created (if there is actual content for the
        acknowledgements).

        N. B.
        Do not let the name extract_content portray anything. It is simply to
        keep the same naming convention as the other workers. extract_content
        is the main method the worker will run.

        :return: no return
        """

        self.dict_item['acknowledgements'] = "Thank you"
        return_payload = writer.extract_content([self.dict_item])

        self.assertTrue(os.path.exists(self.full_text_file),
                        msg=os.path.exists(self.full_text_file))
        self.assertTrue(os.path.exists(self.acknowledgement_file),
                        msg=os.path.exists(self.acknowledgement_file))

    def test_temporary_file_is_made_and_moved(self):
        """
        Tests the extract_content method. Checks that when the worker writes to
        disk, that it first generates a temporary output file, and then moves
        that file to the expected output name.

        N. B.
        Do not let the name extract_content portray anything. It is simply to
        keep the same naming convention as the other workers. extract_content
        is the main method the worker will run.

        :return: no return
        """

        writer.extract_content([self.dict_item])
        os.remove(self.meta_file)

        temp_path = self.meta_file.replace('meta.json', '')
        temp_file_name = writer.write_to_temp_file(self.dict_item, temp_path)
        self.assertTrue(os.path.exists(temp_file_name))

        writer.move_temp_file_to_file(temp_file_name, self.meta_file)
        self.assertFalse(os.path.exists(temp_file_name))
        self.assertTrue(os.path.exists(self.meta_file))

    def test_file_is_compressed(self):
        """
        Tests the compress_file method.

        :return: no return
        """

        writer.write_file(self.dict_item['meta_path'], [self.dict_item], compress=True)
        self.assertTrue(os.path.exists(self.dict_item['meta_path']+'.gz'))


    def test_write_worker_returns_content(self):
        """
        Tests the extract_content method. Checks that the payload that the
        worker returns, that will go on to another RabbitMQ queue, is in the
        format that we expect.

        N. B.
        Do not let the name extract_content portray anything. It is simply to
        keep the same naming convention as the other workers. extract_content
        is the main method the worker will run.

        :return: no return
        """

        payload = writer.extract_content([self.dict_item])
        self.assertTrue(
            payload == '["MNRAS2014"]', 'Length does not match: {0}'
            .format(payload)
        )

if __name__ == '__main__':
    unittest.main()
