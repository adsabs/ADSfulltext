"""
CheckIfExtract Worker Functions

These are the functions for the CheckIfExtract class. This worker should determine if the record selected by the given BibCode should be modified or not based on a given timing criteria (or changleable if required).
"""

import os
from datetime import datetime
from settings import config

def file_last_modified_time(file_input):
    """
    stat a file to get last mod time
    """
    from stat import ST_MTIME
    mtime = os.stat(file_input)[ST_MTIME]
    return datetime.fromtimestamp(mtime)


def create_meta_path(file_input, extract_key="FULLTEXT_EXTRACT_PATH"):

	import ptree
	ptr = ptree.id2ptree(file_input.bibcode)
	extract_path = config[extract_key] + ptr + "meta.json"
	
	return extract_path

def meta_output_exists(file_input, extract_key="FULLTEXT_EXTRACT_PATH"):

	meta_full_path = create_meta_path(file_input, extract_key)

	if os.path.isfile(meta_full_path):
		return True
	else:
		return False

def load_meta_file(file_input, extract_key="FULLTEXT_EXTRACT_PATH"):

	import json
	from dateutil.parser import parse
	meta_full_path = create_meta_path(file_input, extract_key)

	content = None

	try:
		with open(meta_full_path) as f:
			content = json.loads(f.read())
	except IOError:
		print "IOError: Json content could not be loaded", meta_full_path
	except:
		print "Unexpected error"

	return content

def meta_needs_update(file_input, meta_content, extract_key="FULLTEXT_EXTRACT_PATH"):

	import sys
	from dateutil.parser import parse

	# Obtain the indexed date within the meta file
	try:
		meta_date = parse(meta_content["index_date"])
	except KeyError:
		print "Malformed meta-file"
	except:
		print "Unexpected error", sys.exc_info()

	print meta_content
	# No extraction exists
	if 'ft_source' not in meta_content:
		return 'MISSING_FULL_TEXT'

	# Full text file path has changed
	if meta_content['ft_source'] != file_input.full_text_path:
		return 'DIFFERING_FULL_TEXT'

	# Content is considered 'stale'
	delta_comp_time = datetime.utcnow() - datetime.now()
	
	print meta_content
	ft_source_last_modified = file_last_modified_time(meta_content['ft_source'])
	ft_source_last_modified += delta_comp_time

	meta_path = create_meta_path(file_input, extract_key=extract_key)

	meta_json_last_modified = file_last_modified_time(meta_path)

	# If the source content is more new than the last time it was extracted
	if ft_source_last_modified > meta_json_last_modified:
		return 'STALE_CONTENT'


	# # return False

def check_file_exists(file_input):
	return 0

def check_if_extract(file_input):
	return 0