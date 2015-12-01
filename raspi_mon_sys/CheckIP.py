#!/usr/bin/env python2.7
"""This module publishes the IP address using LoggerClient.
"""

import socket
import sys
import traceback

from urllib2 import urlopen

import raspi_mon_sys.LoggerClient as LoggerClient

logger = None
last_private_ip = None
last_public_ip  = None
failure = False

# This function SHOULD BE implemented always.
def publish():
    """Publishes the IP using an ALERT message."""
    global failure
    global last_public_ip
    global last_private_ip
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80))
        private_ip= s.getsockname()[0]
        s.close()
        f = urlopen('http://ip.42.pl/raw')
        public_ip = f.read()
        f.close()
        if private_ip != last_private_ip or public_ip != last_public_ip:
            logger.alert("My private IP address is %s", private_ip)
            logger.alert("My public IP address is %s", public_ip)
            last_private_ip = private_ip
            last_public_ip  = public_ip
        failure = False
    except:
        print "Unexpected error:", traceback.format_exc()
        if not failure:
            logger.alert("Unable to retrieve IP addresses: %s",
                         traceback.format_exc())
            failure = True
            last_private_ip = None
            last_public_ip  = None
        raise

def start():
    """Connects with logging server and sends first message."""
    global logger
    logger = LoggerClient.open("CheckIP")
    publish()

def stop():
    logger.close()
