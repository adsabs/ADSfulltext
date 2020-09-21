#!/bin/bash

# Call the PDF extractor and returns (writes into STDOUT) its output

if [ ! -e $1 ]; then
	exit 127 # not found
fi

/usr/local/bin/pdftotext -enc UTF-8 -eol unix -q "$1"  -
