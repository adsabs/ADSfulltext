"""
CheckIfExtract Worker Functions

These are the functions for the CheckIfExtract class. This worker should determine if the record selected by the given BibCode should be modified or not based on a given timing criteria (or changleable if required).
"""

import os
from settings import config

class FileInputStream(object):

	def __init__(self, input_stream, stream_format="txt"):
		self.input_stream = input_stream
		self.bibcode = ""
		self.full_text_path = ""
		self.provider = ""
		self.stream_format = stream_format

	def extract(self):

		if self.stream_format == "txt":
			try:
				self.bibcode, self.full_text_path, self.provider = [i.strip() for i in self.input_stream.split(" ") if i != ""]
			except ValueError:
				pass
			except:
				pass

		return self.bibcode, self.full_text_path, self.provider


def create_meta_path(file_input):

	import ptree
	ptree = ptree.id2ptree(file_input.bibcode)
	extract_path = os.path.join(config["FULLTEXT_EXTRACT_PATH"] + ptree, 'meta.json')

	return extract_path

def meta_output_exists(file_input):

	meta_full_path = create_meta_path(file_input)

	print meta_full_path

	if os.path.isfile(meta_full_path):
		return True
	else:
		return False

def check_file_exists(file_input):
	return 0