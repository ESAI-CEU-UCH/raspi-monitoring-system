#!/bin/bash
# Plug/unplug at 3 seconds intervals, and then:
sudo stty -F /dev/ttyUSB0 ispeed 115200 ospeed 115200 cs8 -parenb
