import unittest
import time
import json
import os
import lib.CheckIfExtract as check_if_extract
from pipeline import psettings
from pipeline.workers import RabbitMQWorker, CheckIfExtractWorker, \
    StandardFileExtractWorker, WriteMetaFileWorker, ErrorHandlerWorker
from pipeline.ADSfulltext import TaskMaster
from run import publish, read_links_from_file
from settings import META_CONTENT, PROJ_HOME, CONSTANTS


def build_links(test_name):

        integration_path = 'tests/test_integration/stub_data/'
        integration_files = [
        {'fulltext_single_document.links': {'bibcode': ['test1',],
                                             'file': ['tests/test_unit/stub_data/test.txt'],
                                             'provider': ['MNRAS']}},

        {'fulltext_xml_doc_with_acknowledgement.links': {'bibcode': ['test1'],
                                             'file': ['tests/test_integration/stub_data/full_test_elsevier.xml'],
                                             'provider': ['MNRAS']}},

        {'fulltext_range_of_formats.links': {'bibcode': ['full1', 'full2', 'full3', 'full4', 'full5', 'full6'],
                                             'file': ['tests/test_integration/stub_data/full_test.txt',
                                                      'tests/test_integration/stub_data/full_test.ocr',
                                                      'tests/test_integration/stub_data/full_test.xml',
                                                      'tests/test_integration/stub_data/full_test_elsevier.xml',
                                                      'tests/test_integration/stub_data/full_test.html',
                                                      'tests/test_integration/stub_data/full_test.pdf',],
                                             'provider': ['MNRAS', 'MNRAS','MNRAS','Elsevier','MNRAS','MNRAS']}},

        {'fulltext_error_handling_standard_extract_resubmitted.links': {'bibcode': ['full1', 'full2'],
                                             'file': ['tests/test_integration/stub_data/does_not_exist.xml',
                                                      'tests/test_integration/stub_data/full_test.ocr'],
                                             'provider': ['Elsevier', 'MNRAS']}},

        {'fulltext_error_handling.links': {'bibcode': ['full1'],
                                             'file': ['tests/test_integration/stub_data/does_not_exist.xml'],
                                             'provider': ['Elsevier']}},

        {'fulltext_exists_txt.links': {'bibcode': ['test4'],
                                             'file': ['tests/test_unit/stub_data/test.txt'],
                                             'provider': ['TEST']}},

        {'fulltext_exists.links': {'bibcode': ['test'],
                                             'file': ['tests/test_unit/stub_data/te/st/test.pdf'],
                                             'provider': ['TEST']}},

        {'fulltext.links': {'bibcode': ['test1'],
                                             'file': ['tests/test_unit/stub_data/test.txt'],
                                             'provider': ['MNRAS']}},

        {'fulltext_stub.links': {'bibcode': ['2015MNRAS.446.4239E'],
                                             'file': ['test.pdf'],
                                             'provider': ['MNRAS']}},

        {'fulltext_exists.links': {'bibcode': ['test'],
                                             'file': ['tests/test_unit/stub_data/te/st/test.pdf'],
                                             'provider': ['TEST']}},

        {'fulltext_wrong.links': {'bibcode': ['test'],
                                             'file': ['tests/test_unit/stub_data/te/st/test.ocr'],
                                             'provider': ['']}}
        ]


        stub_data = {
            'integration': {'path': integration_path,
                            'files': integration_files}
        }

        path = stub_data[test_name]['path']
        files = stub_data[test_name]['files']

        for file_dictionary in files:

            file_name = file_dictionary.keys()[0]
            file_ = file_dictionary[file_name]

            test_bibcode_ = file_['bibcode']
            test_file_ = file_['file']
            test_provider_ = file_['provider']

            links_file_path = os.path.join(PROJ_HOME, path) + file_name

            if not os.path.exists(links_file_path):
                with open(links_file_path, 'w') as output_file:
                    for i in range(len(test_bibcode_)):

                        output_string = "%s\t%s\t%s\n" % (test_bibcode_[i], os.path.join(PROJ_HOME, test_file_[i]), test_provider_[i])
                        output_file.write(output_string)


class TestUnit(unittest.TestCase):

    def setUp(self):
        build_links(test_name='integration')


class TestGeneric(unittest.TestCase):

    def setUp(self):

        # Build the link files
        build_links(test_name='integration')

        # Load the extraction worker
        check_params = psettings.WORKERS['CheckIfExtractWorker']
        standard_params = psettings.WORKERS['StandardFileExtractWorker']
        writer_params = psettings.WORKERS['WriteMetaFileWorker']
        error_params = psettings.WORKERS['ErrorHandlerWorker']

        for params in [check_params, standard_params, writer_params, error_params]:
            params['RABBITMQ_URL'] = psettings.RABBITMQ_URL
            params['ERROR_HANDLER'] = psettings.ERROR_HANDLER
            params['extract_key'] = "FULLTEXT_EXTRACT_PATH_UNITTEST"
            params['TEST_RUN'] = True

        self.check_worker = CheckIfExtractWorker(params=check_params)
        self.standard_worker = StandardFileExtractWorker(params=standard_params)
        self.standard_worker.logger.debug("params: %s" % standard_params)
        self.meta_writer = WriteMetaFileWorker(params=writer_params)
        self.error_worker = ErrorHandlerWorker(params=error_params)
        self.meta_path = ''
        self.channel_list = None

        # Queues and routes are switched on so that they can allow workers to connect
        TM = TaskMaster(psettings.RABBITMQ_URL, psettings.RABBITMQ_ROUTES, psettings.WORKERS)
        TM.initialize_rabbitmq()

        self.connect_publisher()

    def connect_publisher(self):
        # The worker connects to the queue
        self.publish_worker = RabbitMQWorker()
        self.ret_queue = self.publish_worker.connect(psettings.RABBITMQ_URL)

    def purge_all_queues(self):
        for queue in psettings.RABBITMQ_ROUTES['QUEUES']:
            _q = queue['queue']
            self.publish_worker.channel.queue_purge(queue=_q)

    def tearDown(self):
        # Purge the queues if they have content
        self.purge_all_queues()

    def helper_get_details(self, test_publish):

        with open(os.path.join(PROJ_HOME, test_publish), "r") as f:
            lines = f.readlines()
            self.nor = len(lines)

        self.bibcode, self.ft_source, self.provider = lines[0].strip().split("\t")
        self.bibcode_list = [i.strip().split('\t')[0] for i in lines]

        self.test_expected = check_if_extract.create_meta_path(
            {"bibcode": self.bibcode}, extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST')


        self.meta_list = [check_if_extract.create_meta_path(
            {"bibcode": j}, extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST').replace('meta.json', '')
                          for j in self.bibcode_list]


        self.meta_path = self.test_expected.replace('meta.json', '')

        self.number_of_PDFs = len(list(filter(lambda x: x.lower().endswith('.pdf'),
                                         [i.strip().split("\t")[-2] for i in lines])))
        self.number_of_standard_files = self.nor - self.number_of_PDFs

    def calculate_expected_folders(self, full_text_links):

        with open(os.path.join(PROJ_HOME, full_text_links), "r") as inf:
            lines = inf.readlines()

        expected_paths = [check_if_extract.create_meta_path({CONSTANTS['BIBCODE']: line.strip().split('\t')[0]},
                                                            extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST').replace('meta.json', '')
                          for line in lines]

        return expected_paths

    def clean_up_path(self, paths):

        for path in paths:
            if os.path.exists(path):
                meta = os.path.join(path, 'meta.json')
                fulltext = os.path.join(path, 'fulltext.txt')
                dataset = os.path.join(path, 'dataset.txt')
                acknowledgements = os.path.join(path, 'acknowledgements.txt')

                file_list = [meta, fulltext, dataset, acknowledgements]
                for file_ in file_list:
                    if os.path.exists(file_):
                        os.remove(file_)
                os.rmdir(path)

                print 'deleted: %s and its content' % path
            else:
                print 'Could not delete %s, does not exist' % path

