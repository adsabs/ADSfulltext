"""
Functional test

Loads the ADSfulltext workers for both the Python and Java code. It then injects
a number of full text articles to be extracted onto the RabbitMQ instance. Once
extracted, it checks that the full text file and the meta.json file have been
written to disk. It then shuts down all of the workers.
"""

__author__ = 'J. Elliott'
__maintainer__ = 'J. Elliott'
__copyright__ = 'Copyright 2015'
__version__ = '1.0'
__email__ = 'ads@cfa.harvard.edu'
__status__ = 'Production'
__license__ = 'GPLv3'

import sys
import os

PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)

import run
import os
import time
import subprocess
import string
import unittest
from lib.test_base import TestGeneric
from settings import PROJ_HOME, CONSTANTS


class TestExtractWorker(TestGeneric):
    """
    Class for testing the overall functionality of the ADSfull text pipeline.
    The interaction between the Python workers, Java workers, and the RabbitMQ
    instance.
    """

    def setUp(self):
        """
        Sets up the Python and Java workers using supervisorctl. It then sleeps
        before allowing the rest of the tests to proceed to ensure that the
        workers have started correctly.

        :return: no return
        """
        self.expected_folders = []
        # Start the pipeline
        try:
            self.supervisor_ADS_full_text(action='start', pipeline='Group')

        except:
            print("WARNING: COULD NOT START TESTING PIPELINE")
            pass
        # try:
        #     self.supervisor_ADS_full_text(action='start', pipeline='Java')
        # except:
        #     print "WARNING: COULD NOT START JAVA PIPELINE"
        #     pass
        time.sleep(3)

    def tearDown(self):
        """
        Tears down the relevant parts after the test has finished. It first
        tries to empty all of the queues. It then tries to delete the relevant
        content that was written to disk during the extraction. Finally, it
        stops the workers using supervisorctl.

        :return: no return
        """

        self.connect_publisher()
        self.purge_all_queues()
        self.clean_up_path(self.expected_folders)

        # Stop the pipeline
        try:
            self.supervisor_ADS_full_text(action='stop', pipeline='Group')

        except:
            print("WARNING: COULD NOT STOP TESTING PIPELINE")
            pass
        # try:
        #     self.supervisor_ADS_full_text(action='stop', pipeline='Python')
        # except:
        #     print "WARNING: COULD NOT STOP PYTHON PIPELINE"
        #     pass

    def helper_make_link(self, outfile):
        """
        Helper function that writes the all.links file. This file contains the
        list of bibcodes, path to file, and provider. This ensures there is no
        hard coding.

        :param outfile: name of file to be made
        :return: no return
        """

        letter_list = string.ascii_lowercase
        with open(
                "{home}/{filename}".format(home=PROJ_HOME, filename=outfile),
                'w'
        ) as f_out:

            for letter in string.ascii_lowercase:
                if letter == 'u':
                    break

                f_out.write(
                    'ft{letter}\t'
                    '{home}/tests/test_integration/stub_data/full_test.txt\t'
                    'MNRAS\n'
                    .format(letter=letter, home=PROJ_HOME)
                )

                letter_list = letter_list[1:]

            for letter in letter_list:
                f_out.write(
                    'ft{letter}\t'
                    '{home}/src/test/resources/test_doc.pdf\t'
                    'MNRAS\n'
                    .format(letter=letter, home=PROJ_HOME)
                )

    def supervisor_ADS_full_text(self, action, pipeline):
        """
        Helper function that uses subprocess to start/stop the ADSfulltext
        pipeline using supervisorctl.

        :param action: 'start' or 'stop' the pipeline
        :param pipeline: supervisorctl group name to start or stop
        :return: no return
        """

        pipeline_d = {'Python': 'ADSfulltext',
                      'Java': 'ADSfulltextPDFLIVE',
                      'Group': 'GroupADSfulltextTEST:*'}

        accepted_actions = ['stop', 'start']
        if action not in accepted_actions:
            print 'You can only use: %s' % accepted_actions
            return

        process = subprocess.Popen(['supervisorctl',
                                    '-c',
                                    '/etc/supervisord.conf',
                                    action,
                                    pipeline_d[pipeline]],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        output, error = process.communicate()

        if action not in output:
            raise Exception(
                'ADSfull text could not be started correctly, exiting',
                output,
                error
            )

    def test_functionality_of_the_system_on_non_existent_files(self):
        """
        Main test, it makes the all.links file, runs the injection of the
        bibcodes to the RabbitMQ instance using the run module, then waits
        for the articles full text to be extracted. Finally, it deletes the old
        files and folders.

        :return: no return
        """

        full_text_links = \
            'tests/test_functional/stub_data/fulltext_functional_tests.links'

        # Obtain the parameters to publish to the queue
        # Expect that the records are split into the correct number of
        # packet sizes
        self.helper_make_link(outfile=full_text_links)
        run.run(full_text_links=os.path.join(PROJ_HOME, full_text_links),
                packet_size=10,
                force_extract=False)

        time.sleep(40)

        self.expected_folders = self.calculate_expected_folders(full_text_links)

        for expected_f in self.expected_folders:
            self.assertTrue(
                os.path.exists(expected_f),
                'Could not find: {0}'
                .format(expected_f)
            )
            self.assertTrue(
                os.path.exists(os.path.join(expected_f, 'meta.json')),
                'Could not find: {0}'
                .format(os.path.join(expected_f, 'meta.json'))
            )
            self.assertTrue(
                os.path.exists(os.path.join(expected_f, 'fulltext.txt')),
                'Could not find: {0}'
                .format(os.path.join(expected_f, 'fulltext.txt'))
            )


if __name__ == '__main__':
    unittest.main()

