#!/bin/bash

test_list=`ls tests/test_integration/test*.py`

for test in $test_list
do
	echo $test
	nosetests $test
done
