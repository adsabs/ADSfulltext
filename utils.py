import os
import sys
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
	fn = os.path.join(os.path.dirname(file_), '..', 'logs', '%s.log' % name_)
	rfh = ConcurrentRotatingFileHandler(filename=fn, maxBytes=2097152, backupCount=5, mode='a') #2MB file
	rfh.setFormatter(formatter)
	LOGGER.handlers = []
	LOGGER.addHandler(rfh)
	LOGGER.setLevel(level)
	return LOGGER

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

		in_file = PROJ_HOME + "/" + self.input_stream
		try:
			with open(in_file) as f:
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

	def make_payload(self):

		'''
		Convert the file stream input to a payload form defined below
		'''
		
		import json
		# self.payload = zip(self.bibcode, self.full_text_path, self.provider)
		self.payload = json.dumps(self.raw)

		return self.payload