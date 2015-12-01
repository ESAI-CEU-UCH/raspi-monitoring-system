#!/usr/bin/env python2.7
"""InfluxDB hub for insertion of points into raspberry pi InfluxDB server.
"""

import bson
import datetime
import json
import pytz
import Queue
import time
import threading
import traceback

from influxdb import InfluxDBClient

import raspi_mon_sys.LoggerClient as LoggerClient
import raspi_mon_sys.Scheduler as Scheduler
import raspi_mon_sys.Utils as Utils

logger = None
mqtt_client = None
influx_client = None
lock = threading.RLock()

pending_points = []

def __build_fields_dict(v):
    fields = {}
    if v is None or v == '': fields["null"] = "true"
    if v is None: fields["null"] = "true"
    elif type(v) == str or type(v) == unicode: fields["svalue"] = unicode(v)
    else: fields["value"] = v
    return fields

def __enqueue_raspimon_point(client, userdata, topic, message, tz):
    timestamp = message["timestamp"]
    fields = __build_fields_dict( message["data"] )
    doc = {
        "measurement": topic,
        "time": datetime.datetime.fromtimestamp(timestamp, tz).isoformat(),
        "fields": fields
    }
    lock.acquire()
    try:
        pending_points.append( doc )
    except:
        print "Unexpected error:", traceback.format_exc()
        logger.error("Unexpected error: %s", traceback.format_exc())        
    lock.release()

def __enqueue_forecast_point(client, userdata, topic, message, tz):
    timestamp = message["timestamp"]
    lock.acquire()
    try:
        for s,e,v in zip(message["periods_start"],message["periods_end"],message["values"]):
            fields = __build_fields_dict(v)
            doc = {
                "measurement": topic,
                "time": datetime.datetime.fromtimestamp(0.5*(s+e), tz).isoformat(),
                "fields": fields
            }
            pending_points.append( doc )
    except:
        print "Unexpected error:", traceback.format_exc()
        logger.error("Unexpected error: %s", traceback.format_exc())
    lock.release()

def __on_mqtt_connect(client, userdata, rc):
    client.subscribe("raspimon/#")
    client.subscribe("forecast/#")

def __on_mqtt_message(client, userdata, msg):
    tz = pytz.timezone("Europe/Madrid")
    topic = msg.topic.replace("/",":")
    message = json.loads(msg.payload)
    if topic.startswith("raspimon:"):
        __enqueue_raspimon_point(client, userdata, topic, message, tz)
    elif topic.startswith("forecast:"):
        __enqueue_forecast_point(client, userdata, topic, message, tz)
    else:
        raise ValueError("Unknown MQTT topic " + topic)

def __configure_mqtt(client):
    client.on_connect = __on_mqtt_connect
    client.on_message = __on_mqtt_message

def start():
    """Opens connections with logger, InfluxDB and MQTT broker."""
    global logger
    global mqtt_client
    global house_data
    global influx_client
    logger = LoggerClient.open("InfluxDBHub")
    mqtt_client = Utils.getpahoclient(logger, __configure_mqtt)
    config = Utils.getconfig("influxdb", logger)
    influx_client = InfluxDBClient(config["host"], config["port"],
                                   config["user"], config["password"],
                                   config["database"])
    try:
        influx_client.create_database(config["database"])
    except:
        pass
    influx_client.create_retention_policy('raspimon_policy',
                                          config["retention_policy"],
                                          1, default=True)

def stop():
    mqtt_client.disconnect()
    logger.close()

def write_data():
    global pending_points
    lock.acquire()
    if len(pending_points) > 0:
        try:
            influx_client.write_points(pending_points)
            pending_points = []
        except:
            print "Unexpected error:", traceback.format_exc()
            logger.error("Unexpected error: %s", traceback.format_exc())
    lock.release()
