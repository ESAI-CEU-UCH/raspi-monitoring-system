#!/usr/bin/env python2.7
"""Several utilities shared between different modules."""
from email.mime.text import MIMEText
from uuid import getnode
import paho.mqtt.client as paho
import pymongo
import smtplib

__PAHO_HOST      = "localhost"
__PAHO_PORT      = 1883
__PAHO_KEEPALIVE = 60
__PAHO_BIND_ADDRESS = "127.0.0.1"

__MONGO_HOST = "localhost"
__MONGO_PORT = 27018

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
        logger.alert("Unable to connect with Paho server")
        raise
    logger.info("Paho initialized at %s:%d with timeout=%d",
                __PAHO_HOST, __PAHO_PORT, __PAHO_KEEPALIVE)
    return client

def gettopic(name):
    """Returns a MQTT topic as `raspimon/MACADDRESS/name/value` where name is given
    as argument to this function."""
    return "raspimon/" + getmac() + "/" + name + "/value"

def getmongoclient(logger):
    """Returns a client connected to Mongo DB."""
    try:
        client = pymongo.MongoClient(__MONGO_HOST, __MONGO_PORT)
    except:
        if logger is not None: logger.alert("Unable to connect with MongoDB server")
        raise
    if logger is not None: logger.info("MongoDB initialized at %s:%d", __MONGO_HOST, __MONGO_PORT)
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
