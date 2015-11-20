1#!/usr/bin/env python2.7
"""MongoDB hub for insertion of data into our servers.

This module inserts into GVA2015_data collection documents with the following
structure::

    {
        "_id": ObjectID(...),
        "house": HOUSE_NAME,
        "basetime": DATE VALUE IN TIMESTAMP,
        "topic": MQTT TOPIC WITH / REPLACED BY :,
        "delta_times": AN ARRAY,
        "values": ANOTHER ARRAY
    }
"""

import bson
import datetime
import json
import Queue
import time
import threading
import traceback

import raspi_mon_sys.LoggerClient as LoggerClient
import raspi_mon_sys.Scheduler as Scheduler
import raspi_mon_sys.Utils as Utils

PENDING_MESSAGES_LENGTH_WARNING = 10000 # expected 40MB of messages for warning
PENDING_MESSAGES_LENGTH_ERROR = 30000 # expected 120MB of messages for data loss
PERIOD = 3600 # every 3600 seconds (1 hour) we send data to hour server

assert PENDING_MESSAGES_LENGTH_ERROR > PENDING_MESSAGES_LENGTH_WARNING

raspi_mac = Utils.getmac()
logger = None
mqtt_client = None
house_data = None
lock = threading.RLock()

pending_messages = []
message_queues = {}

def __on_mqtt_connect(client, userdata, rc):
    client.subscribe("raspimon/#")

def __on_mqtt_message(client, userdata, msg):
    global message_queues
    topic = msg.topic.replace("/",":")
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
        "house" : house_data["name"],
        "basetime" : datetime.datetime.utcfromtimestamp(basetime),
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
    global house_data
    logger = LoggerClient.open("MongoDBHub")
    mqtt_client = Utils.getpahoclient(logger, __configure_mqtt)
    mongo_client = Utils.getmongoclient(logger)
    db = mongo_client["raspimon"]
    col = db["GVA2015_houses"]
    house_data = col.find_one({ "raspi":raspi_mac })
    assert house_data is not None
    mongo_client.close()

def stop():
    mongo_client = Utils.getmongoclient(logger)
    db = mongo_client["raspimon"]
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
    try:
        mongo_client = Utils.getmongoclient(logger)
        db = mongo_client["raspimon"]
        lock.acquire()
        t = time.time()
        keys = message_queues.keys()
        lock.release()
        insert_batch = [ __process(x) for x in keys if t - x[1] > PERIOD ]
        global pending_messages
        insert_batch.extend(pending_messages)
        pending_messages = []
        try:
            db.GVA2015_data.insert(insert_batch)
        except:
            pending_messages = insert_batch
            if len(pending_messages) > PENDING_MESSAGES_LENGTH_ERROR:
                logger.error("Pending %s messages is above data loss threshold %d, sadly pending list set to zero :S",
                             len(pending_messages),
                             PENDING_MESSAGES_LENGTH_ERROR)
                pending_messages = [] # data loss here :'(
            elif len(pending_messages) > PENDING_MESSAGES_LENGTH_WARNING:
                logger.alert("Pending %s messages is above warning threshold %d, data loss will occur at %d",
                             len(pending_messages),
                             PENDING_MESSAGES_LENGTH_WARNING,
                             PENDING_MESSAGES_LENGTH_ERROR)
            else:
                logger.warning("Connection with database is failing")
            raise
        logger.info("Inserted %d documents", len(insert_batch))
        mongo_client.close()
    except:
        print "Unexpected error:", traceback.format_exc()
        logger.error("Unexpected error: %s", traceback.format_exc())

if __name__ == "__main__":
    Scheduler.start()
    start()
    Scheduler.repeat_o_clock_with_offset(PERIOD*1000, PERIOD/12*1000, publish)
    try:
        while True: time.sleep(60)
    except:
        stop()
        raise
