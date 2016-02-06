#!/usr/bin/env python2.7
"""This module publishes the data related with Open Energy Monitor devices.

This code is an adaptation of `emonhub <https://github.com/emonhub/emonhub>`_.

This module executes its own thread which publishes data following the
schedule configured at open energy monitor devices.

Open energy monitor data is published under topics::

    BASETOPIC/rfemon/NAME/NODE_ID/KEY {"timestamp":timestamp,"data":data}

EmonTxV3 sends the following data list::

   [1447689007.43, 10, -2, 0, 0, 0, 25236, 3000, 3000, 3000, 3000, 3000, 3000, 1, -27, 8]

0. Timestamp.
1. NodeID.
2. CT1 RealPower (when using AC transformer) in W.
3. CT2 RealPower (when using AC transformer) in W.
4. CT3 RealPower (when using AC transformer) in W.
5. CT4 RealPower (when using AC transformer) in W.
6. VRMS (if using AC transformer) in V [x0.01].
7. Temp1 (currently not connected).
8. Temp2 (currently not connected).
9. Temp3 (currently not connected).
10. Temp4 (currently not connected).
11. Temp5 (currently not connected).
12. Temp6 (currently not connected).
13. Pulse count (currently not connected).
14. Signal strength in DB.
15. Message number.

EmonTH22 sends the following data list::

   [1447688997.86, 19, 215, 0, 488, 30, -32, 7]

0. Timestamp.
1. NodeID.
2. Temperature in C [x0.1].
3. Outdoor temperature.
4. Humidity in % [x0.1].
5. Battery power.
6. Signal strength in DB.
7. Message number.

The MongoDB contains a document where data captured by RFM69Pi is described.
This document contains a `node2keys` dictionary similar to the following one::

    "node2keys" : { "19" : [ {"key":2, "name":"temp", "mul":0.1, "add":0.0 } ] }

This dictionary is indexed by nodeId and contains information of indexes at
values list (`key`), the `name` used to publish this data, and an optional
linear transformation applied to the data (`mul` and `add`).
"""

import json
import serial
import time
import threading

import raspi_mon_sys.emonhub.emonhub_interfacer as emonhub_interfacer
import raspi_mon_sys.LoggerClient as LoggerClient
import raspi_mon_sys.Utils as Utils

MAX_TIME_BETWEEN_READINGS = 1800 # 30 minutes
DEFAULT_POWER_TOLERANCE = 0.0
MAX_TIME_WITHOUT_READ = 300 # 5 minutes

com_port = "/dev/ttyAMA0"
com_baud = 38400
timeout = 0

client = None
iface = None
is_running = False
logger = None

def __build_null_values(node2keys):
    t = time.time()
    values = []
    for nodeId,node in node2keys.iteritems():
        current_values = { 0:t, 1:int(nodeId) }
        for conf in node:
            current_values[conf["key"]] = None
        values.append( current_values )
    return values

def __try_open(logger):
    try:
        iface = emonhub_interfacer.EmonHubJeeInterfacer("raspimon", logger,
                                                        com_port, com_baud)
    except:
        iface = None
        logger.alert("Unable to open connection with RF device")
    return iface

def __process(logger, client, iface, nodes, node2keys):
    last_timestamp = time.time()
    topic = Utils.gettopic("rfemon/{0}/{1}/{2}")
    while is_running:
        if iface is None:
            time.sleep(0.1)
            iface = __try_open(logger)
            continue
        # Execute run method
        iface.run()
        # Read socket
        current_values = iface.read()
        if current_values is None and time.time() - last_timestamp > MAX_TIME_WITHOUT_READ:
            current_values = __build_null_values(node2keys)
            logger.alert("No values read for a long time, probably something is wrong with RF device")
            iface.close()
            time.sleep(0.1)
            iface = __try_open(logger)
        elif current_values is not None:
            current_values = [ current_values ]
        # If complete and valid data values were received
        if current_values is not None:
            for values in current_values:
                logger.debug(str(values))
                t      = values[0]
                nodeId = values[1]
                for conf in node2keys[str(nodeId)]:
                    last_data = conf["data"]
                    key       = conf["key"]
                    name      = conf["name"]
                    mul       = conf.get("mul", 1.0)
                    add       = conf.get("add", 0.0)
                    v         = values[key]
                    if v is not None: v = (v + add) * mul
                    alert_below_th = conf.get("alert_below_threshold", None)
                    if alert_below_th is not None and v is not None and v < alert_below_th:
                        logger.alert("Value %f for nodeId %d key %d registered with name %s is below threshold %f",
                                     float(v), nodeId, key, name, float(alert_below_th))
                    if Utils.compute_relative_difference(last_data, v) > conf.get("tolerance",DEFAULT_POWER_TOLERANCE) or t - conf["when"] > MAX_TIME_BETWEEN_READINGS:
                        message = { 'timestamp' : t, 'data' : v }
                        client.publish(topic.format(name, nodeId, key), json.dumps(message))
                        conf["data"] = v
                        conf["when"] = t
                last_timestamp = t
        time.sleep(0.05)

def start():
    """Starts a thread which reads from RFM69Pi and publishes using MQTT."""    
    global logger
    logger = LoggerClient.open("OpenEnergyMonitor")
    logger.info("Opening connection")
    
    global client
    client = Utils.getpahoclient(logger)
    
    global iface
    iface = __try_open(logger)

    # config is a dictionary with:
    # devices : [ { id, desc, name  } ]
    # keys : [ { nodeId, key, desc, name } ]
    config    = Utils.getconfig("open_energy_monitor", logger)
    nodes     = config["nodes"]
    node2keys = config["node2keys"]
    for n in nodes:
        # We add data field to check relative difference between two consecutive
        # readings, if the difference is not enough the message is not published,
        # reducing this way the overhead and database size.
        for conf in node2keys[str(n["id"])]:
            conf["data"] = -10000.0
            conf["when"] = 0.0
    global is_running
    is_running = True
    thread = threading.Thread(target=__process,
                              args=(logger, client, iface, nodes, node2keys))
    thread.setDaemon(True)
    thread.start()

def stop():
    global is_running
    is_running = False
    time.sleep(0.1)
    client.disconnect()
    logger.close()
    iface.close()

if __name__ == "__main__":
    Utils.startup_wait()
    start()
    # Inifite loop.
    try:
        while True:
            time.sleep(60)
    except:
        stop()
