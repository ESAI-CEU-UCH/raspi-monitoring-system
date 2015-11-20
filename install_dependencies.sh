#!/bin/bash
# Executes installation of needed dependencies.
# pip install uuid
pip install enum paho-mqtt
aptitude install python-zmq screen autossh mongodb-clients libmongo-client0 python-pymongo minicom python-crcmod python-serial python-lxml
