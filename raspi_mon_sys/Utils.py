#!/usr/bin/env python2.7
"""Several utilities shared between different modules."""
from email.mime.text import MIMEText
from uuid import getnode
import paho.mqtt.client as paho
import smtplib

__PAHO_HOST      = "localhost"
__PAHO_PORT      = 1883
__PAHO_KEEPALIVE = 60
__PAHO_BIND_ADDRESS = "127.0.0.1"

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

def getmac(): return hex(getnode()).replace('0x','').replace('L','')

def __dummy_configure(client):
    pass
    
def getpahoclient(configure=__dummy_configure):
    # Configure logger.
    logger = MailLoggerClient.open("GetPahoClient")
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
