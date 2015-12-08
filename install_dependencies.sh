#!/bin/bash
# Executes installation of needed dependencies.
# pip install uuid
# influxdb is available under raspbian apt, but it is an old version :(
pip install enum paho-mqtt pytz influxdb
aptitude install python-zmq screen autossh mongodb-clients libmongo-client0 python-pymongo minicom python-crcmod python-serial python-lxml nodejs nodejs-legacy npm python-ntplib
