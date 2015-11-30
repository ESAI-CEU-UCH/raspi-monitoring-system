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

INFLUX_HOST='localhost'
INFLUX_PORT=8086
INFLUX_USER='root'
INFLUX_PASSWORD='root'
INFLUX_DATABASE='raspimon'

logger = None
mqtt_client = None
influx_client = None
lock = threading.RLock()

pending_points = []

def __enqueue_raspimon_point(client, userdata, topic, message, tz):
    timestamp = message["timestamp"]
    data = message["data"]
    doc = {
        "measurement": topic,
        "time": datetime.datetime.fromtimestamp(timestamp, tz).isoformat(),
        "fields": { "value": data }
    }
    lock.acquire()
    pending_points.append( doc )
    lock.release()

def __enqueue_forecast_point(client, userdata, topic, message, tz):
    timestamp = message["timestamp"]
    lock.acquire()
    for s,e,v in zip(message["periods_start"],message["periods_end"],message["values"]):
        doc = {
            "measurement": topic,
            "time": datetime.datetime.fromtimestamp(0.5*(s+e), tz).isoformat(),
            "fields": { "value": v }
        }
        pending_points.append( doc )
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
    influx_client = InfluxDBClient(INFLUX_HOST, INFLUX_PORT,
                                   INFLUX_USER, INFLUX_PASSWORD,
                                   INFLUX_DATABASE)
    try:
        influx_client.create_database(INFLUX_DATABASE)
    except:
        pass

def stop():
    mqtt_client.disconnect()
    logger.close()

def write_data():        
    try:
        global pending_points
        lock.acquire()
        influx_client.write_points(pending_points)
        pending_points = []
        lock.release()
    except:
        print "Unexpected error:", traceback.format_exc()
        logger.error("Unexpected error: %s", traceback.format_exc())
