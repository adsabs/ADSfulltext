"""
CheckIfExtract Worker Functions

These are the functions for the CheckIfExtract class. This worker should determine if the record selected by the given BibCode should be modified or not based on a given timing criteria (or changleable if required).
"""

import os
import utils
import json
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

	from dateutil.parser import parse
	meta_full_path = create_meta_path(file_input, extract_key)

	content = None

	try:
		with open(meta_full_path) as f:
			content = json.loads(f.read())
	except IOError:
		raise IOError("IOError: Json content could not be loaded: \n%s, \n%s" % (meta_full_path, file_input.raw))
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

	# No extraction exists
	if 'ft_source' not in meta_content:
		return 'MISSING_FULL_TEXT'

	# Full text file path has changed
	if meta_content['ft_source'] != file_input.full_text_path:
		return 'DIFFERING_FULL_TEXT'

	# Content is considered 'stale'
	delta_comp_time = datetime.utcnow() - datetime.now()
	
	ft_source_last_modified = file_last_modified_time(meta_content['ft_source'])
	ft_source_last_modified += delta_comp_time

	meta_path = create_meta_path(file_input, extract_key=extract_key)

	meta_json_last_modified = file_last_modified_time(meta_path)

	# If the source content is more new than the last time it was extracted
	if ft_source_last_modified > meta_json_last_modified:
		return 'STALE_CONTENT'

def check_if_extract(message_list, extract_key="FULLTEXT_EXTRACT_PATH"):
	
	NEEDS_UPDATE = ["MISSING_FULL_TEXT", "DIFFERING_FULL_TEXT", "STALE_CONTENT"]

	file_list = [utils.FileInputStream(i, stream_format='list') for i in message_list]
	publish_list = []

	for message in message_list:
		file_ = utils.FileInputStream(message, stream_format='list')
		file_.extract()
	 	meta_content = load_meta_file(file_, extract_key=extract_key)
	 	update = meta_needs_update(file_, meta_content, extract_key="FULLTEXT_EXTRACT_PATH")

	 	if update in NEEDS_UPDATE:
	 		publish_list.append([file_.bibcode, file_.full_text_path, file_.provider])

	return json.dumps(publish_list)