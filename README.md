[![Build Status](https://travis-ci.org/adsabs/ADSfulltext.svg)](https://travis-ci.org/adsabs/ADSfulltext)
[![Coverage Status](https://coveralls.io/repos/adsabs/ADSfulltext/badge.svg)](https://coveralls.io/r/adsabs/ADSfulltext)
[![Stories in Ready](https://badge.waffle.io/adsabs/ADSfulltext.svg?label=ready&title=Ready)](http://waffle.io/adsabs/ADSfulltext)

# ADSfulltext

Article full text extraction pipeline. Set of workers that check the filesystem and convert
binary files into text.



## Notes

The java process subscribes to the queue; that should change!

command=/usr/bin/java -jar /vagrant/target/ADSfulltext-1.0-SNAPSHOT-jar-with-dependencies.jar --consume-queue ; the program (relative uses PATH, can take args)