#!/bin/bash
dev=$1
if [[ -z $dev ]]; then
    dev=/dev/ttyUSB0
fi
minicom -b 9600 -D $dev
