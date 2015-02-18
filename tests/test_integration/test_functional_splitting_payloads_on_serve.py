import run
import os
import time
from base import IntegrationTest
from settings import PROJ_HOME, CONSTANTS
from lib import CheckIfExtract as check_if_extract


class TestExtractWorker(IntegrationTest):

    def setUp(self):
        pass

    def tearDown(self):
        self.connect_publisher()
        self.purge_all_queues()

    def calculate_expected_folders(self, full_text_links):

        with open(os.path.join(PROJ_HOME, full_text_links)) as inf:
            lines = inf.readlines()

        expected_paths = [check_if_extract.create_meta_path({CONSTANTS['BIBCODE']: line.strip().split('\t')[0]},
                                                            extract_key='FULLTEXT_EXTRACT_PATH_UNITTEST').replace('meta.json', '')
                          for line in lines]

        return expected_paths

    def test_functionality_of_the_system_on_non_existent_files(self):

        full_text_links = 'tests/test_integration/stub_data/fulltext_functional_tests.links'
        # Obtain the parameters to publish to the queue
        # Expect that the records are split into the correct number of
        # packet sizes
        run.main(full_text_links=full_text_links,
                 packet_size=10)

        # time.sleep(10)

        expected_folders = self.calculate_expected_folders(full_text_links)

        for expected_f in expected_folders:
            self.assertTrue(os.path.exists(expected_f), 'Could not find: %s' % expected_f)

if __name__ == "__main__":
    unittest.main()