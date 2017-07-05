#!/bin/bash

# Call the PDF extractor and returns (writes into STDOUT) its output

# modify these lines if you need to change java/locations etc.

java=java
home=`dirname "$BASH_SOURCE"`
jar=$home/../target/ADSfulltext-1.2-SNAPSHOT-jar-with-dependencies.jar
input=$0

#echo "java=$java home=$home jar=$jar input=$input"

if [ ! -e $1 ]; then
	exit 127 # not found
fi



$java -jar $jar "$1"