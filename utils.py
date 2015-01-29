import os
import sys
from settings import config, PROJ_HOME

class FileInputStream(object):

	def __init__(self, input_stream, stream_format="txt"):
		self.input_stream = input_stream
		self.raw = ""
		self.bibcode = ""
		self.full_text_path = ""
		self.provider = ""
		self.stream_format = stream_format

	def print_info(self):
		print "Bibcode: %s" % self.bibcode
		print "Full text path: %s" % self.full_text_path
		print "Provider: %s" % self.provider
		print "Raw content: %s" % self.raw

	def extract(self):

		if self.stream_format == "txt":
			try:
				self.bibcode, self.full_text_path, self.provider = [i.strip() for i in self.input_stream.split("\t") if i != ""]
				self.raw = self.input_stream
			except ValueError:
				print "Value error (most likely not tab delimited), traceback:", self.input_stream, sys.exc_info()
			except:
				print "Unexpected error", sys.exc_info()

		elif self.stream_format == "file":

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
						raw.append(l)


				self.bibcode, self.full_text_path, self.provider = bibcode, full_text_path, provider
				self.raw = raw

			except IOError:
				print in_file, sys.exc_info()

		elif self.stream_format == 'list':
			try:
				self.bibcode, self.full_text_path, self.provider = self.input_stream
				self.raw = '\t'.join(self.input_stream)
			except:
				raise IOError('Wrong format given: %s' % (self.input_stream))

		else:
			raise KeyError

		return self.bibcode, self.full_text_path, self.provider, self.raw

	def make_payload(self):

		'''
		Convert the file stream input to a payload form defined below
		'''
		
		import json
		# self.payload = zip(self.bibcode, self.full_text_path, self.provider)
		self.payload = json.dumps(self.raw)

		return self.payload