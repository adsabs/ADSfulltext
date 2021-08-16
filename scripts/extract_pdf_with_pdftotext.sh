#!/bin/bash

# Call the PDF extractor and returns (writes into STDOUT) its output

if [ ! -e $1 ]; then
        exit 127 # not found
fi

EXITCODE=0
STD_OUT="$(mktemp)"

#/usr/bin/pdftotext -enc UTF-8 -eol unix -q "$1"  -

timeout -s SIGINT 30s /usr/bin/pdftotext -enc UTF-8 -eol unix -q "$1"  - > $STD_OUT

if [ $? -eq 124 ]
then
   VECTOR_FREE="$(mktemp)"
   gs -q -o $VECTOR_FREE -sDEVICE=pdfwrite -dFILTERVECTOR "$1"
   timeout -s SIGINT 30s /usr/bin/pdftotext -enc UTF-8 -eol unix -q "$VECTOR_FREE" - > $STD_OUT
   EXITCODE=$?

   rm $VECTOR_FREE

   if [ $EXITCODE -eq 124 ]
   then
        echo "PDFTOTEXT ERROR! Can't process file $1 within 30 seconds!"
        rm $STD_OUT
        exit $EXITCODE
   fi

fi

cat $STD_OUT
rm $STD_OUT

exit $EXITCODE
