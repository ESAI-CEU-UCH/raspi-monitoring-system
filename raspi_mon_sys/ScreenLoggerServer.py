#!/usr/bin/env python2.7
"""The purpose of this module is to allow messaging via screen. It needs you to
install enum module as `pip install enum`.  This module is executed as:

.. code-block:: bash

   $ python ScreenLoggerServer.py [zmq_transport]

It uses a default ZeroMQ transport if the argument is not given.

Once it is executed, client module can connect using the appropiate ZMQ
transport. Messages would be shown at screen using stderr output or ignored.

Alternatively, it is possible to import the module from another Python script
calling directly `start_thread()` function:

>>> import raspi_mon_sys.MailLoggerServer as server
>>> server.start_thread()

"""
import datetime
import json
import Queue
import socket
import threading
import traceback
import sys
import zmq

import raspi_mon_sys.LoggerClient as LoggerClient
import raspi_mon_sys.Utils as Utils

__transport = LoggerClient.default_transport
__mac_addr  = Utils.getmac()

# Queues of pending messages.
__hourly_queue = Queue.PriorityQueue()
__daily_queue  = Queue.PriorityQueue()
__weekly_queue = Queue.PriorityQueue()

# Enums.
__levels    = LoggerClient.levels
__schedules = LoggerClient.schedules

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

def __process_message(msg):
    sched = msg["schedule"]
    txt   = __generate_message_line(msg)

    if sched != str(__schedules.SILENTLY):
        sys.stderr.write(txt + "\n")
    
def start(transport_string=__transport):
    """Starts the execution of the server.
    
    The argument is a ZeroMQ transport string for bind server socket.

    """
    ctx = zmq.Context.instance()
    s   = ctx.socket(zmq.PULL)
    s.bind(transport_string)
        
    print("Running server at ZMQ transport: " + transport_string)
    try:
        while True:
            msg   = s.recv_pyobj()
            __process_message(msg)
    except:
        __process_message({
            "name" : "MailLoggerServer",
            "level" : "ALERT",
            "schedule" : "INSTANTANEOUSLY",
            "text" : "Logging service STOPPED",
            "datetime" : datetime.datetime.now()
        })
        print("Stopping server")
        raise

def start_thread(transport_string=__transport):
    """Starts the sever in a python thread."""
    thread = threading.Thread(target=start, args=(mail_credentials_path,
                                                  transport_string))
    thread.setDaemon()
    thread.start()

##############################################################################

if __name__ == "__main__":
    credentials = sys.argv[1] if len(sys.argv) > 1 else __mail_credentials_path
    transport = sys.argv[2] if len(sys.argv) > 2 else __transport
    start(credentials, transport)
