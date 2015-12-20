#!/usr/bin/env python2.7
"""Publishes readings from Plugwise circles.

Plugwise data is published under topics::

    BASETOPIC/plugwise/NAME1/power1s/MACADDRESS1 {"timestamp":t1,"data":power1s}
    BASETOPIC/plugwise/NAME1/power8s/MACADDRESS1 {"timestamp":t1,"data":power8s}
    BASETOPIC/plugwise/NAME1/state/MACADDRESS1   {"timestamp":t1,"data":state}
    ...
    BASETOPIC/plugwise/NAME2/power1s/MACADDRESS2 {"timestamp":t2,"data":power1s}
    BASETOPIC/plugwise/NAME2/power8s/MACADDRESS2 {"timestamp":t2,"data":power8s}
    BASETOPIC/plugwise/NAME2/state/MACADDRESS2   {"timestamp":t2,"data":state}
    ...

This sequence is a time series of power consumption and state values. State
value messages are only sended if state changes from previous and current read.

Looking into code and `Plugwise-2-py <https://github.com/SevenW/Plugwise-2-py>`_
it seems that 1 second sampling period is allowed but 8-10 seconds would obtain
better resolution from pulse counters.

"""

# Copyright (C) 2015 Miguel Lorenzo, Francisco Zamora-Martinez
# Use of this source code is governed by the GPLv3 license found in the LICENSE file.

import json
import time
import traceback

import raspi_mon_sys.LoggerClient as LoggerClient
import raspi_mon_sys.plugwise.api as plugwise_api
import raspi_mon_sys.Scheduler as Scheduler
import raspi_mon_sys.Utils as Utils

# Plugwise connection configuration.
MAX_TIME_BETWEEN_READINGS = 1800
DEFAULT_POWER_TOLERANCE = 0.0
DEFAULT_SERIAL_PORT = "/dev/ttyUSB0" # USB port used by Plugwise receiver
OUTPUT_LIST = [ {"key":0,"suffix":"1s"}, {"key":1,"suffix":"8s"} ]

topic = Utils.gettopic("plugwise/{0}/{1}/{2}")
logger = None
client = None
config = None
device = None
circles_config = None
circles = None
verbose = False

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
    global config
    global device
    global circles_config
    global circles
    logger  = LoggerClient.open("PlugwiseMonitor")
    if not verbose: logger.config(logger.levels.WARNING, logger.schedules.DAILY)
    config  = Utils.getconfig("plugwise", logger)
    client  = Utils.getpahoclient(logger, __configure)
    assert config is not None
    device  = plugwise_api.Stick(logger, DEFAULT_SERIAL_PORT)

    # circles_config is a list of dictionaries: name, mac, desc.  state field is
    # added in next loop to track its value so it can be used to only send
    # messages in state transitions. power1s and power8s field is used to check
    # the relative difference in power in order to reduce the network overhead.
    circles_config = config["circles"]
    circles = []
    for circle_data in circles_config:
        mac = circle_data["mac"]
        circles.append( plugwise_api.Circle(logger, mac, device, {
            "name" : circle_data["name"],
            "location" : circle_data["desc"],
            "always_on" : "False",
            "production" : "True"
        }) )
        circle_data["state"] = "NA"
        for v in OUTPUT_LIST:
            circle_data["power" + v["suffix"]] = -10000.0
            circle_data["when" + v["suffix"]] = 0.0

    client.loop_start()

def stop():
    client.disconnect()
    logger.close()

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
            last_powers = [ config["power"+x["suffix"]] for x in OUTPUT_LIST ]
            last_state = config["state"]
            try:
                reading = c.get_power_usage()
                powers  = [ reading[x["key"]] for x in OUTPUT_LIST ]
                state   = c.get_info()['relay_state']
                alert_below_th = config.get("alert_below_threshold", None)
                for i,p in enumerate(powers):
                    p = max(0, p)
                    key = OUTPUT_LIST[i]["key"]
                    suffix = OUTPUT_LIST[i]["suffix"]
                    if alert_below_th is not None and p < alert_below_th:
                        logger.alert("Value %f %s for circle %s registered with name %s is below threshold %f",
                                     float(p), suffix, mac, name, float(alert_below_th))
                    if Utils.compute_relative_difference(last_powers[i], p) > config.get("tolerance",DEFAULT_POWER_TOLERANCE) or t - config["when"+suffix] > MAX_TIME_BETWEEN_READINGS:
                        usage_message = { 'timestamp' : t, 'data': p }
                        messages.append( (topic.format(name, "power"+suffix, mac), usage_message) )
                        config["power"+suffix] = p
                        config["when"+suffix] = t
                # check state transition before message is appended
                if state != last_state:
                    state_message = { 'timestamp' : t, 'data' : state }
                    messages.append( (topic.format(name, "state", mac), state_message) )
                    config["state"] = state # track current state value
            except:
                print "Unexpected error:", traceback.format_exc()
                logger.info("Error happened while processing circles data: %s", traceback.format_exc())
        for top,message in messages:
            client.publish(top, json.dumps(message))
    except:
        print "Unexpected error:", traceback.format_exc()
        logger.error("Error happened while processing circles data")
        raise

if __name__ == "__main__":
    start()
    Scheduler.start()
    Scheduler.repeat_o_clock(config["period"], publish)
    try:
        while True:
            time.sleep(60)
    except:
        Scheduler.stop()
        stop()
