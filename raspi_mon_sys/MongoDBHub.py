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
raspimon_message_queues = {}
forecast_message_queues = {}

def __enqueue_raspimon_message(client, userdata, topic, message):
    timestamp = message["timestamp"]
    data = message["data"]
    basetime = int(timestamp // PERIOD * PERIOD)
    lock.acquire()
    q = raspimon_message_queues.setdefault( (topic,basetime), Queue.Queue() )
    lock.release()
    delta_time = timestamp - basetime
    q.put( (delta_time, data) )
    logger.debug("%s %f %f %f %s", topic, float(basetime), float(timestamp),
                 float(delta_time), str(data))

def __enqueue_forecast_message(client, userdata, topic, message):
    timestamp = message["timestamp"]
    basetime = int(timestamp // PERIOD * PERIOD)
    lock.acquire()
    q = forecast_message_queues.setdefault( (topic,basetime), Queue.Queue() )
    lock.release()
    q.put( message )
    logger.debug("%s %f %s", topic, float(timestamp), str(message))

def __on_mqtt_connect(client, userdata, rc):
    client.subscribe("raspimon/#")
    client.subscribe("forecast/#")

def __on_mqtt_message(client, userdata, msg):
    global raspimon_message_queues
    topic = msg.topic.replace("/",":")
    message = json.loads(msg.payload)
    if topic.startswith("raspimon/"):
        __enqueue_raspimon_message(client, userdata, topic, message)
    elif topic.startswith("forecast/"):
        __enqueue_forecast_message(client, userdata, topic, message)
    else:
        raise "Unknown MQTT topic :S"

def __configure_mqtt(client):
    client.on_connect = __on_mqtt_connect
    client.on_message = __on_mqtt_message

def __build_raspimon_documents(key):
    global raspimon_message_queues
    topic,basetime = key
    data_pairs = raspimon_message_queues.pop(key)
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
    return [ document ]

def __build_forecast_documents(key):
    global forecast_message_queues
    topic,basetime = key
    messages = raspimon_message_queues.pop(key)
    messages.sort(key=lambda x: x["timestamp"])
    for doc in messages:
        doc["house"] = house_data["name"]
        doc["topic"] = topic
    logger.info("New documents for topic= %s basetime= %d with n= %d",
                topic, int(basetime), len(messages))
    return messages

def __upload_all_data(db, build_documents, queues):
    insert_batch = [ y for x in queues.keys() for y in build_documents(x)]
    db.GVA2015_data.insert(insert_batch)
    logger.info("Inserted %d documents", len(insert_batch))

def __build_after_deadline_documents(build_docs, queues, t):
    lock.acquire()
    keys = queues.keys()
    lock.release()
    batch = [ (y for y in build_docs(queues) if t - x[1] > PERIOD) for x in keys ]
    return batch

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
    __upload_all_data(db, __build_raspimon_documents, raspimon_message_queues)
    __upload_all_data(db, __build_forecast_documents, forecast_message_queues)
    # close rest of pending connections
    mongo_client.close()
    logger.close()

def upload_data():
    try:
        mongo_client = Utils.getmongoclient(logger)
        db = mongo_client["raspimon"]
        t = time.time()

        raspimon_batch = __build_after_deadline_documents(__build_raspimon_documents,
                                                          raspimon_message_queues, t)
        forecast_batch = __build_after_deadline_documents(__build_forecast_documents,
                                                          forecast_message_queues, t)
        
        global pending_messages
        insert_batch = raspimon_batch + forecast_batch + pending_messages
        pending_messages = []
        
        try:
            if len(insert_batch) > 0: db.GVA2015_data.insert(insert_batch)
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
