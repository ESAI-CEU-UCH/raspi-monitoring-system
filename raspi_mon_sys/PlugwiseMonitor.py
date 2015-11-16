#!/usr/bin/env python2.7
"""Publishes readings from Plugwise circles.

Plugwise data is published under topics::

    BASETOPIC/plugwise/MACADDRESS1/NAME1/power1s/value {"timestamp":t1,"data":power1}
    BASETOPIC/plugwise/MACADDRESS1/NAME1/state/value   {"timestamp":t1,"data":state1}
    ...
    BASETOPIC/plugwise/MACADDRESS1/NAME2/power1s/value {"timestamp":t2,"data":power2}
    BASETOPIC/plugwise/MACADDRESS1/NAME2/state/value   {"timestamp":t2,"data":state2}
    ...

This sequence is a time series of power consumption and state values. State
value messages are only sended if state changes from previous and current read.

Looking into code and `Plugwise-2-py <https://github.com/SevenW/Plugwise-2-py>`_
it seems that 1 second sampling period is allowed.
"""

# Copyright (C) 2015 Miguel Lorenzo, Francisco Zamora-Martinez
# Use of this source code is governed by the GPLv3 license found in the LICENSE file.

import time

import raspi_mon_sys.MailLoggerClient as MailLogger
import raspi_mon_sys.plugwise.api as plugwise_api
import raspi_mon_sys.Utils as Utils

# Plugwise connection configuration.
DEFAULT_SERIAL_PORT = "/dev/ttyUSB0" # USB port used by Plugwise receiver
topic = Utils.gettopic("plugwise/{0}/{1}/{2}")
logger = None
client = None
device = None
circles_config = None
circles = None

def __on_connect(client, userdata, rc):
    # We will use this topic to send on/off commands to our circles.
    client.subscribe("plugwise/#")

def __on_message(client, userdata, msg):
    #print(msg.topic+" "+str(msg.payload))
    pass

def __configure(client):
    client.on_connect = __on_connect
    client.on_message = __on_message

def start():
    """Connects with logging server, loads plugwise network configuration and
    connects with MQTT broker."""
    global logger
    global client
    global device
    global circles_config
    global circles
    logger  = MailLogger.open("PlugwiseMonitor")
    config  = Utils.getconfig("plugwise", logger)
    client  = Utils.getpahoclient(logger, __configure)
    assert config is not None
    device  = plugwise_api.Stick(DEFAULT_SERIAL_PORT)

    # circles_config is a list of dictionaries: name, mac, desc.
    # state field is added in next loop to track its value so it can be used to
    # only send messages in state transitions.
    circles_config = config.circles
    circles = []
    for circle_data in circles_config:
        mac = circle_data["mac"]
        circles.append( plugwise_api.Circle(mac, device) )
        circle_data["state"] = "NA"

    client.loop_start()

def publish():
    """Publishes circle messages via MQTT."""
    try:
        # All circles messages are generated together and before sending data
        # via MQTT. This way sending data overhead is ignored and we expect
        # similar timestamps between all circles.
        messages = []
        for i,c in enumerate(circles):
            config = circles_config[i]
            t    = time.time()
            mac  = config["mac"]
            name = config["name"]
            last_state = config["state"]
            power   = c.get_power_usage()
            power1s = power[0]
            state   = c.get_info()['relay_state']
            power1s_usage_message = { 'timestamp' : t, 'data': power1s }
            messages.append( (topic.format(mac, name, "power1s"), power1s_usage_message) )
            # check state transition before message is appended
            if state != last_state:
                state_message = { 'timestamp' : t, 'data' : state }
                messages.append( (topic.format(mac, name, "state"), state_message) )
                config["state"] = state # track current state value
        for topic,message in messages:
            client.publish(topic, message)
    except:
        logger.error("Error happened while processing circles data")
        raise
