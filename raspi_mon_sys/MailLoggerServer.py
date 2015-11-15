#!/usr/bin/env python2.7
"""The purpose of this module is to allow messaging via email with a standalone
system. It needs you to install enum module as `pip install enum`.
This module is executed as:

.. code-block:: bash

   $ python MailLoggerServer.py [mail_credentials [zmq_transport]]

By default it looks for `/etc/mail_credentials.json` if first argument is not
given and uses a default ZeroMQ transport if second one is given either.

Once it is executed, client module can connect using the appropiate ZMQ
transport. Messages would be shown at screen using stderr output and they would
be enqueued for delayed mail delivery, ignored from mail, or sended
instantaneously.

Alternatively, it is possible to import the module from another Python script
calling directly `start()` function:

>>> import raspi_mon_sys.MailLoggerServer as server
>>> server.start()
"""
import datetime
import json
import Queue
import Scheduler
import socket
import traceback
import sys
import zmq

import raspi_mon_sys.MailLoggerClient as MailLoggerClient
import raspi_mon_sys.Utils as Utils

__transport = MailLoggerClient.default_transport
__mail_credentials_path = "/etc/mail_credentials.json"
__mac_addr  = Utils.getmac()

# Queues of pending messages.
__hourly_queue = Queue.PriorityQueue()
__daily_queue  = Queue.PriorityQueue()
__weekly_queue = Queue.PriorityQueue()

# Enums.
__levels    = MailLoggerClient.levels
__schedules = MailLoggerClient.schedules

# Mapping between schedule options and python queues.
__schedule2queue = {
    str(__schedules.HOURLY) : __hourly_queue,
    str(__schedules.DAILY)  : __daily_queue,
    str(__schedules.WEEKLY) : __weekly_queue
}

def __generate_message_line(msg):
    """Given a message it generates a string to be shown at screen or mail."""
    time_str     = datetime.datetime.strftime(msg["datetime"], "%c")
    host_str     = socket.gethostname()
    name_str     = msg["name"]
    level_str    = msg["level"]
    schedule_str = msg["schedule"]
    text_str     = msg["text"].replace('\n', '\\n')
    line_str     = "%s %s %s %9s %17s: %s: %s"%(time_str, host_str, __mac_addr,
                                                level_str, schedule_str,
                                                name_str, text_str)
    return line_str

def __generate_subject(frequency, name="LIST"):
    """Generates a subject for the email."""
    return "MailLogger raspi %s - %s - %s"%(__mac_addr, name, str(frequency))

def __queue_handler(mail_credentials_path, frequency, queue):
    """Traverses the given queue and concatenates by lines all message texts."""
    subject = __generate_subject(frequency)
    if queue.empty():
        msg = "Empty queue"
    else:
        lines_list = []
        while not queue.empty(): lines_list.append( queue.get()[1] )
        msg = '\n'.join( lines_list )
    try:
        mail_credentials = json.loads( open(mail_credentials_path).read() )
        Utils.sendmail(mail_credentials, subject, msg)
        mail_credentials = None
    except:
        print "Unexpected error:", traceback.format_exc()
        if msg != "Empty queue":
            print("FATAL ERROR: irrecoverable information loss :(")

def __process_message(mail_credentials_path, msg):
    sched = msg["schedule"]
    txt   = __generate_message_line(msg)
    
    sys.stderr.write(txt + "\n")
    
    if sched == str(__schedules.INSTANTANEOUSLY):
        subject = __generate_subject(__schedules.INSTANTANEOUSLY,
                                     msg["name"])
        try:
            mail_credentials = json.loads( open(mail_credentials_path).read() )
            Utils.sendmail(mail_credentials, subject, txt)
            mail_credentials = None
        except:
            print "Unexpected error:", traceback.format_exc()
            
    elif sched != str(__schedules.SILENTLY):
        __schedule2queue[ sched ].put( (msg["datetime"],txt) )


def start(mail_credentials_path=__mail_credentials_path,
          transport_string=__transport):
    """Starts the execution of the server.
    
    The first argument is a path to `mail_credentials.json` file and the second
    argument is a ZeroMQ transport string for bind server socket.

    """
    if not Scheduler.is_running():
        __process_message(mail_credentials_path, {
            "name" : "MailLoggerServer",
            "level" : str(__levels.ALERT),
            "schedule" : str(__schedules.INSTANTANEOUSLY),
            "text" : "Logging service STARTED",
            "datetime" : datetime.datetime.now()
        })
        mail_credentials = json.loads( open(mail_credentials_path).read() )
        mail_credentials = None
        ctx = zmq.Context.instance()
        s   = ctx.socket(zmq.PULL)
        s.bind(transport_string)
        
        Scheduler.start()
        Scheduler.repeat_o_clock(3600*1000, __queue_handler,
                                 mail_credentials_path, "HOURLY", __hourly_queue)
        Scheduler.repeat_o_clock(3600*24*1000, __queue_handler,
                                 mail_credentials_path, "DAILY", __daily_queue)
        Scheduler.repeat_o_clock(3600*24*7*1000, __queue_handler,
                                 mail_credentials_path, "WEEKLY", __weekly_queue)
        
        print("Running server at ZMQ transport: " + transport_string)
        try:
            while True:
                msg   = s.recv_pyobj()
                __process_message(mail_credentials_path, msg)
        except:
            __queue_handler(mail_credentials_path, "HOURLY", __hourly_queue)
            __queue_handler(mail_credentials_path, "DAILY", __daily_queue)
            __queue_handler(mail_credentials_path, "WEEKLY", __weekly_queue)
            __process_message(mail_credentials_path, {
                "name" : "MailLoggerServer",
                "level" : "ALERT",
                "schedule" : "INSTANTANEOUSLY",
                "text" : "Logging service STOPPED",
                "datetime" : datetime.datetime.now()
            })
            print("Stopping server")
            Scheduler.stop()
            raise

##############################################################################

if __name__ == "__main__":
    credentials = sys.argv[1] if len(sys.argv) > 1 else __mail_credentials_path
    transport = sys.argv[2] if len(sys.argv) > 2 else __transport
    start(credentials, transport)
