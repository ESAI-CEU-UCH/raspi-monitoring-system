#!/usr/bin/env python2.7
"""Several utilities shared between different modules.

This module uses /etc/default/raspimon_auth to get a MongoDB connection URI:

    mongodb://[username:password@]host1[:port1][,host2[:port2],...[,hostN[:portN]]][/[database][?options]]

"""
from email.mime.text import MIMEText
from uuid import getnode

import datetime
import ntplib
import os
import paho.mqtt.client as paho
import pymongo
import smtplib
import time

__PAHO_HOST      = "localhost"
__PAHO_PORT      = 1883
__PAHO_KEEPALIVE = 60
__PAHO_BIND_ADDRESS = "127.0.0.1"

__RASPIMON_AUTH = "/etc/default/raspimon_auth"

def __get_mongodb_uri():
    with open(__RASPIMON_AUTH) as f: x = f.readline().strip()
    return x

def sendmail(credentials, subject, msg):
    """Sends an email using the given credentials dictionary, subject and message
    strings.

    The credentials dictionary should contain the following keys:

    - server: a sever hostname string.
    - port: a port number.
    - user: a string with user name.
    - password: a password string.
    - from: string with From header content.
    - to: string with To header content.

    """
    smtpserver = smtplib.SMTP_SSL(credentials["server"], credentials["port"])
    smtpserver.ehlo()
    #smtpserver.starttls()
    smtpserver.login(credentials["user"], credentials["password"])
    msg = MIMEText( msg )
    msg['Subject'] = subject
    msg['From'] = credentials["from"]
    msg['To'] = credentials["to"]
    smtpserver.sendmail(credentials["from"], credentials["to"], msg.as_string())
    smtpserver.quit()

def getmac():
    """Returns MAC address of eth0 in a hexadecimal string."""
    return hex(getnode()).replace('0x','').replace('L','')

def __dummy_configure(client):
    pass
    
def getpahoclient(logger,configure=__dummy_configure):
    """Connects to MQTT broker using python paho client.
    
    This function receives a logger instance for info and alert messages, and an
    optional configure function. The client is instantiated and configure
    function is called as `configure(client)`. Next, `client.connect()` is
    called. Usually configure function is used to initialize `on_connect` and
    `on_message` fields.

    """
    try:
        # Configure Paho.
        client = paho.Client()
        configure(client)
        client.connect(__PAHO_HOST, __PAHO_PORT, __PAHO_KEEPALIVE,
                       __PAHO_BIND_ADDRESS)
        client.loop_start()
    except:
        logger.alert("Unable to connect with MQTT broker")
        raise
    logger.info("MQTT client connected to %s:%d with keepalive=%d",
                __PAHO_HOST, __PAHO_PORT, __PAHO_KEEPALIVE)
    return client

def gettopic(name):
    """Returns a MQTT topic as `raspimon/MACADDRESS/name/value` where name is given
    as argument to this function."""
    return "raspimon/" + getmac() + "/" + name + "/value"

def getmongoclient(logger):
    """Returns a client connected to Mongo DB."""
    try:
        client = pymongo.MongoClient( __get_mongodb_uri() )
    except:
        if logger is not None: logger.alert("Unable to connect with MongoDB server")
        raise
    if logger is not None: logger.info("MongoDB client connected")
    return client

def getconfig(source, logger):
    """Returns the configuration for `source` as stored at Mongo DB in our
    servers."""
    client = getmongoclient(logger)
    collection = client["raspimon"]["GVA2015_config"]
    config = collection.find_one({ "raspi":getmac(), "source":source })
    client.close()
    assert config is not None
    if logger is not None: logger.debug("Configuration retrieved properly for source %s", source)
    return config

def ntpcheck(logger=None):
    c = ntplib.NTPClient()
    response = c.request('europe.pool.ntp.org', version=3)
    ntp_time = datetime.datetime.fromtimestamp(response.tx_time)
    today = datetime.datetime.today()
    if abs(ntp_time - today) > datetime.timedelta(0,2,0): # 2 seconds
        if logger is not None: logger.error("NTP sync error")
        raise Exception("NTP sync error")

def startup_wait():
    if os.getenv("STARTED_AT_BOOT") == "yes":
        try:
            wait = float(os.getenv("STARTUP_SLEEP"))
        except:
            wait = 30.0
            # wait for device configuration during startup
        print "Waiting %f seconds for device configuration..."%(wait)
        time.sleep(wait)
        print "Starting"

def compute_relative_difference(a, b): return abs(b - a) / (max(abs(a),abs(b)) + 1e-20)
