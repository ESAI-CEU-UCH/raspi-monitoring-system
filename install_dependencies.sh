#!/bin/bash
# Executes installation of needed dependencies.
# pip install uuid
pip install enum paho-mqtt pytz
aptitude install python-zmq screen autossh mongodb-clients libmongo-client0 python-pymongo minicom python-crcmod python-serial python-lxml nodejs nodejs-legacy npm
