#!/bin/bash
avrdude -v -c arduino -p ATMEGA328P -P /dev/ttyUSB0 -b 115200 -U flash:w:DiscreteSampling.cpp.hex
