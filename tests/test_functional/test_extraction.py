import run
import os
import time
import subprocess
import sys
from lib.test_base import TestGeneric
from settings import PROJ_HOME, CONSTANTS
from lib import CheckIfExtract as check_if_extract


class TestExtractWorker(TestGeneric):

    def setUp(self):
        self.expected_folders = []
        # Start the pipeline
        self.supervisor_ADS_full_text('start')
        time.sleep(3)

    def tearDown(self):
        self.connect_publisher()
        self.purge_all_queues()
        self.clean_up_path(self.expected_folders)

        # Stop the pipeline
        self.supervisor_ADS_full_text('stop')



    def supervisor_ADS_full_text(self, action):

        accepted_actions = ['stop', 'start']
        if action not in accepted_actions:
            print 'You can only use: %s' % accepted_actions
            sys.exit(0)

        process = subprocess.Popen(['supervisorctl', '-c', '/vagrant/supervisord.conf', action, 'ADSfulltext'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        output, error = process.communicate()

        if action not in output:
            print 'ADSfull text could not be started correctly, exiting'
            sys.exit(0)

    def test_functionality_of_the_system_on_non_existent_files(self):

        full_text_links = 'tests/test_functional/stub_data/fulltext_functional_tests.links'
        # Obtain the parameters to publish to the queue
        # Expect that the records are split into the correct number of
        # packet sizes
        run.run(full_text_links=full_text_links,
                 packet_size=10)

        time.sleep(60)

        self.expected_folders = self.calculate_expected_folders(full_text_links)

        for expected_f in self.expected_folders:
            self.assertTrue(os.path.exists(expected_f), 'Could not find: %s' % expected_f)


if __name__ == "__main__":
    unittest.main()