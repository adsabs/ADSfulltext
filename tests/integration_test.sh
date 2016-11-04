#!/bin/bash

test_list=`ls tests/test_integration/test*.py`

for test in $test_list
do
	echo $test
	#/proj.adswhy/opt/Python-2.7.8/bin/nosetests $test
	coverage run -p --source=. $test
done
