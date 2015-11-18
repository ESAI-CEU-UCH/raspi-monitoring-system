#!/usr/bin/env python2.7
"""MongoDB hub for insertion of data into our servers.

This module inserts into GVA2015_data collection documents with the following
structure::

    {
        "_id": ObjectID(...),
        "basetime": Timestamp(1447343677, 0),
        "topic": MQTT TOPIC,
        "delta_times": AN ARRAY,
        "values": ANOTHER ARRAY
    } 
"""

import bson
import json
import Queue
import time
import threading

import raspi_mon_sys.LoggerClient as LoggerClient
import raspi_mon_sys.Scheduler as Scheduler
import raspi_mon_sys.Utils as Utils

PERIOD = 3600 # every 3600 seconds (1 hour) we send data to hour server

raspi_mac = Utils.getmac()
logger = None
mongo_client = None
mqtt_client = None
house_data = None
db = None
lock = threading.RLock()

message_queues = {}

def __on_mqtt_connect(client, userdata, rc):
    client.subscribe("raspimon/#")

def __on_mqtt_message(client, userdata, msg):
    global message_queues
    topic = msg.topic
    message = json.loads(msg.payload)
    timestamp = message["timestamp"]
    data = message["data"]
    basetime = int(timestamp // PERIOD * PERIOD)
    lock.acquire()
    q = message_queues.setdefault( (topic,basetime), Queue.Queue() )
    lock.release()
    delta_time = timestamp - basetime
    q.put( (delta_time, data) )
    logger.debug("%s %f %f %f %s", topic, float(basetime), float(timestamp),
                 float(delta_time), str(data))

def __configure_mqtt(client):
    client.on_connect = __on_mqtt_connect
    client.on_message = __on_mqtt_message

def __process(key):
    global message_queues
    topic,basetime = key
    data_pairs = message_queues.pop(key)
    data_pairs.put('STOP')
    data_pairs = [ x for x in iter(data_pairs.get, 'STOP') ]
    data_pairs.sort(key=lambda x: x[0])
    delta_times,values = zip(*data_pairs)
    document = {
        "basetime" : bson.timestamp.Timestamp(basetime,0),
        "topic" : topic,
        "delta_times" : delta_times,
        "values" : values
    }
    logger.info("New document for topic= %s basetime= %d with n= %d",
                topic, int(basetime), len(delta_times))
    return document

def start():
    """Opens connections with logger, MongoDB and MQTT broker."""
    global logger
    global mqtt_client
    global mongo_client
    global house_data
    global db
    logger = LoggerClient.open("MongoDBHub")
    mqtt_client = Utils.getpahoclient(logger, __configure_mqtt)
    mongo_client = Utils.getmongoclient(logger)
    db = mongo_client["raspimon"]
    col = db["GVA2015_houses"]
    house_data = col.find_one({ "raspi":raspi_mac })
    assert house_data is not None

def stop():
    # close MQTT broker connection
    mqtt_client.disconnect()
    # force sending data to MongoDB
    insert_batch = [ __process(x) for x in message_queues.keys() ]
    db.GVA2015_data.insert(insert_batch)
    logger.info("Inserted %d documents", len(insert_batch))
    # close rest of pending connections
    mongo_client.close()
    logger.close()

def publish():
    t = time.time()
    lock.acquire()
    keys = message_queues.keys()
    lock.release()
    insert_batch = [ __process(x) for x in keys if t - key[1] > PERIOD ]
    db.GVA2015_data.insert(insert_batch)
    logger.info("Inserted %d documents", len(insert_batch))
    
if __name__ == "__main__":
    Scheduler.start()
    start()
    Scheduler.repeat_o_clock_with_offset(PERIOD*1000, PERIOD/12*1000, publish)
    try:
        while True: time.sleep(60)
    except:
        stop()
        raise
