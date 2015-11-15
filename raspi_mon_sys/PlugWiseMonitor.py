#!/usr/bin/env python2.7
"""Recovers power measurments from plugwise circles to mqtt


"""

# Copyright (C) 2015 Miguel Lorenzo
# Use of this source code is governed by the MIT license found in the LICENSE file.

import datetime
import paho.mqtt.client as mqtt
import time
import traceback
from plugwise import *
import plugwise.util

import raspi_mon_sys.MailLoggerClient as MailLogger
import raspi_mon_sys.Utils as Utils

logger = MailLogger.open("PlugWiseMonitor")
topic = Utils.gettopic("Plugwise/{0}")

#plugwise reader configuration
DEFAULT_SERIAL_PORT = "/dev/ttyUSB0" #defines the USB serial port used
macs = ["000D6F00029C19F9","000D6F0003562CBD"] #defines the macs of the devices that will be polled
device = DEFAULT_SERIAL_PORT
device = Stick(device)

def __on_connect(client, userdata, rc):
    logger.info("Connected to MQTT broker")

def __configure(client):
    client.on_connect = __on_connect

def publish(day_offset):
    """Publishes the power measurment of a certain plugwise."""
    try:
        client = Utils.getpahoclient(logger, __configure)
    except:
        logger.error("Error when connecting with MQTT broker")
        raise
    readings = {};
   for mac in macs:
        c = Circle(mac, device)
        try:
            readings[mac] = c.get_power_usage()
        except ValueError:
            logger.error("Unable to retrieve power measurement for circle: {0}".format(mac))
        
    for circle_mac,rea in readings:
        client.publish(topic.format(circle_mac), rea)
    logger.info("Power measurement published")
    client.disconnect()
