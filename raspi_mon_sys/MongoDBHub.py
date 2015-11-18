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
import raspi_mon_sys.Utils as Utils

PERIOD = 10 # every 3600 seconds (1 hour) we send data to hour server

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
    basetime = int(message.timestamp // PERIOD * PERIOD)
    lock.acquire()
    q = message_queues.setdefault( (topic,basetime), Queue.Queue() )
    lock.release()
    delta_time = message.timestamp - basetime
    q.put( (delta_time, message.data) )
    print(topic, message.timestamp, message.data)

def __configure_mqtt(client):
    client.on_connect = __on_mqtt_connect
    client.on_message = __on_mqtt_message

def __process(key, insert_batch):
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
    insert_batch.append(document)

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

def publish():
    t = time.time()
    lock.acquire()
    keys = message_queues.keys()
    lock.release()
    insert_batch = []
    for key in keys:
        topic,basetime = key
        if t - basetime > PERIOD: __process(key, insert_batch)
    if len(insert_batch) > 0: db.GVA2015_data.insert_many(insert_batch)

if __name__ == "__main__":
    start()
    while True:
        publish()
        time.sleep(PERIOD)
