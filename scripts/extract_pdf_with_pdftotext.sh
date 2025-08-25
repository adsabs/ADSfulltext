#!/bin/bash

# Call the PDF extractor and returns (writes into STDOUT) its output

if [ ! -e $1 ]; then
        exit 127 # not found
fi

# If PDFTOTEXT_TIMEOUT is null or unset, use 30s as timeout. The 30s
# was selected not to exclude articles that take longer processing
# (~10 or so seconds) but to limit the vector graphics stripping just
# to ones that are hanging
PDFTOTEXT_TIMEOUT=${PDFTOTEXT_TIMEOUT:-30s}
EXITCODE=0
STD_OUT="$(mktemp)"


# If it doesn't finish processing in 30 seconds assume that vector
# graphics is blocking processing and proceed to strip it
# (temporarily) with ghostscript, then reprocess

timeout -s SIGINT $PDFTOTEXT_TIMEOUT /usr/bin/pdftotext -enc UTF-8 -eol unix -q "$1"  - > $STD_OUT

if [ $? -eq 124 ]
then

    # try reprocessing, this time without vector graphics. 
    # If it still hangs after some time, error out with a note!
    # Note: you need to apply a timeout to /usr/bin/gs as well here!

    VECTOR_FREE="$(mktemp)"
    timeout -s SIGINT $PDFTOTEXT_TIMEOUT /usr/bin/gs -q -o $VECTOR_FREE -sDEVICE=pdfwrite -dFILTERVECTOR "$1" 
    EXITCODE=$?

    if [ $EXITCODE -eq 124 ]
    then
        echo "GHOSTSCRIPT ERROR! Can't process file $1 within 30 seconds!"
        rm $STD_OUT
        rm $VECTOR_FREE
        exit $EXITCODE
    else
        timeout -s SIGINT $PDFTOTEXT_TIMEOUT /usr/bin/pdftotext -enc UTF-8 -eol unix -q "$VECTOR_FREE" - > $STD_OUT
        EXITCODE=$?

        rm $VECTOR_FREE

        if [ $EXITCODE -eq 124 ]
        then
            echo "PDFTOTEXT ERROR! Can't process file $1 within 30 seconds!"
            rm $STD_OUT
            exit $EXITCODE
        fi
    fi
fi

cat $STD_OUT
rm $STD_OUT

exit $EXITCODE
