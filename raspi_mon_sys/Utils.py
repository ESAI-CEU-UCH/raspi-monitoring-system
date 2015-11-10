#!/usr/bin/env python2.7
"""Several utilities shared between different modules."""
from email.mime.text import MIMEText
from uuid import getnode as get_mac
import smtplib

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

def getmac(): return hex(get_mac()).replace('0x','')
