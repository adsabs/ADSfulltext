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


class TestGeneric(unittest.TestCase):

    def setUp(self):
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