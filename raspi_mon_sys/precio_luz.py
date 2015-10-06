#!/usr/bin/env python

# Copyright (C) 2015 Miguel Lorenzo
# Use of this source code is governed by the MIT license found in the LICENSE file.

#Recoje el precio de la luz en para el dia siguiente y lo publica mediante MQTT



import time
import paho.mqtt.client as mqtt
import json
import urllib2

url = 'https://www.esios.ree.es/es/analisis/1013?vis=1&start_date=06-10-2015T00%3A00&end_date=06-10-2015T23%3A00&compare_start_date=05-10-2015T00%3A00&groupby=hour#JSON'
response = urllib2.urlopen(url)
