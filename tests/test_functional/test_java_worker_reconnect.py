"""
Functional test

A test to check that the Java workers will not die on supervisord when trying to
reconnect to the RabbitMQ instance, even if it is offline.

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

import time
import subprocess
import unittest
from lib.test_base import TestGeneric
from settings import PROJ_HOME, CONSTANTS


class TestExtractWorker(TestGeneric):
    """
    Class for testing the restarting of the Java workers.
    """

    def setUp(self):
        """
        :return: no return
        """

    def tearDown(self):
        """

        :return: no return
        """

    def supervisor_ADS_full_text(self, action, pipeline):
        """
        Helper function that uses subprocess to start/stop the ADSfulltext
        pipeline using supervisorctl.

        :param action: 'start' or 'stop' the pipeline
        :param pipeline: supervisorctl group name to start or stop
        :return: no return
        """

        pipeline_d = {'Python': 'ADSfulltext',
                      'Java': 'GroupADSfulltextTEST:ADSfulltextPDFLIVE_00',
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

    def test_the_java_workers_do_not_die_if_rabbitmq_is_down(self):
        """
        Test to ensure that the java workers attempt to reconnect to the
        RabbitMQ instance even if it is offline.

        :return: no return
        """

        start_rabbitmq = subprocess.Popen([
            'docker',
            'start',
            'dockerfile-rabbitmq'
        ])
        start_output, start_error = start_rabbitmq.communicate()

        self.supervisor_ADS_full_text('start', 'Java')

        stop_rabbitmq = subprocess.Popen([
            'docker',
            'stop',
            'dockerfile-rabbitmq'
        ])
        stop_output, stop_error = stop_rabbitmq.communicate()

        for i in range(20):
            status_java = subprocess.Popen(
                ['supervisorctl',
                 'status',
                 'GroupADSfulltextTEST:ADSfulltextPDFLIVE_00'
                 ],
                stdout=subprocess.PIPE
            )
            status_output, status_error = status_java.communicate()
            print(status_output, status_error)

            self.assertFalse(
                'FATAL' in status_output,
                'Output: {0}, Error: {1}'.format(status_output, status_error)
            )

            time.sleep(1)


if __name__ == '__main__':
    unittest.main()