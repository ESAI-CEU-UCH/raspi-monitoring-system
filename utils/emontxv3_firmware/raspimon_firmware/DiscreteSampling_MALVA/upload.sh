#!/bin/bash
dev=$1
if [[ -z $dev ]]; then
    dev=/dev/ttyUSB0
fi
avrdude -v -c arduino -p ATMEGA328P -P $dev -b 115200 -U flash:w:DiscreteSampling.cpp.hex
