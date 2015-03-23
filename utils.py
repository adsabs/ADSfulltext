import sys
import os
import logging
from settings import config, PROJ_HOME
from logging import handlers
from cloghandler import ConcurrentRotatingFileHandler


def setup_logging(file_, name_, level='DEBUG'):

    level = getattr(logging, level)

    logfmt = '%(levelname)s\t%(process)d [%(asctime)s]:\t%(message)s'
    datefmt= '%m/%d/%Y %H:%M:%S'
    formatter = logging.Formatter(fmt=logfmt, datefmt=datefmt)
    LOGGER = logging.getLogger(name_)
    fn_path = os.path.join(os.path.dirname(file_), PROJ_HOME, 'logs')
    if not os.path.exists(fn_path):
        os.makedirs(fn_path)
    fn = os.path.join(fn_path, '%s.log' % name_)
    rfh = ConcurrentRotatingFileHandler(filename=fn, maxBytes=2097152, backupCount=5, mode='a') #2MB file
    rfh.setFormatter(formatter)
    LOGGER.handlers = []
    LOGGER.addHandler(rfh)
    LOGGER.setLevel(level)
    return LOGGER


def overrides(interface_class):
    """
    To be used as a decorator, it allows the explicit declaration you are overriding the method of class
    from the one it has inherited. It checks that the name you have used matches that in the parent
    class and returns an assertion error if not
    """
    def overrider(method):
        assert(method.__name__ in dir(interface_class))
        return method
    return overrider


class FileInputStream(object):

    def __init__(self, input_stream):
        self.input_stream = input_stream
        self.raw = ""
        self.bibcode = ""
        self.full_text_path = ""
        self.provider = ""

    def print_info(self):
        print "Bibcode: %s" % self.bibcode
        print "Full text path: %s" % self.full_text_path
        print "Provider: %s" % self.provider
        print "Raw content: %s" % self.raw

    def extract(self):

        # in_file = PROJ_HOME + "/" + self.input_stream
        in_file = self.input_stream
        try:
            with open(in_file, 'r') as f:
                input_lines = f.readlines()

                raw = []
                bibcode, full_text_path, provider = [], [], []
                for line in input_lines:

                    l = [i for i in line.strip().split('\t') if i != ""]
                    bibcode.append(l[0])
                    full_text_path.append(l[1])
                    provider.append(l[2])
                    raw.append({"bibcode": bibcode[-1], "ft_source": full_text_path[-1], "provider": provider[-1]})

            self.bibcode, self.full_text_path, self.provider = bibcode, full_text_path, provider
            self.raw = raw

        except IOError:
            print in_file, sys.exc_info()

        return self.bibcode, self.full_text_path, self.provider, self.raw

    def make_payload(self, **kwargs):

        '''
        Convert the file stream input to a payload form defined below
        '''

        import json
        if 'packet_size' in kwargs:
            self.payload = [json.dumps(self.raw[i:i+kwargs['packet_size']])
                            for i in range(0, len(self.raw), kwargs['packet_size'])]
        else:
            # self.payload = zip(self.bibcode, self.full_text_path, self.provider)
            self.payload = [json.dumps(self.raw)]

        return self.payload

    # def split_payload(self):
