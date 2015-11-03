#!env python2.7
"""The purpose of this module is to allow messaging via email with a standalone
system. It needs you to install enum module:

$ pip install enum

And is executed as:

$ python MailLoggerServer.py mail_credentials [zmq_transport]

Once it is executed, client module can connect using the appropiate ZMQ
transport. Messages would be shown at screen using stderr output and they would
be enqueued for delayed mail delivery, ignored from mail, or sended
instantaneously.
"""
from uuid import getnode as get_mac

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

# Command line arguments.
__nargs = len(sys.argv)
__transport = MailLoggerClient.default_transport
if __nargs < 2: raise Exception("Sever needs mail credentials as argument")
if __nargs > 3: raise Exception("Sever needs one or two arguments")
if len(sys.argv) == 3: __transport = sys.argv[2]
__mail_credentials = json.loads( open(sys.argv[1]).read() )

__mac_addr  = hex(get_mac()).replace('0x','')

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

def __queue_handler(frequency, queue):
    """Traverses the given queue and concatenates by lines all message texts."""
    subject = __generate_subject(frequency)
    if queue.empty():
        msg = "Empty queue"
    else:
        lines_list = []
        while not queue.empty(): lines_list.append( queue.get()[1] )
        msg = '\n'.join( lines_list )
    try:
        Utils.sendmail(__mail_credentials, subject, msg)
    except:
        print "Unexpected error:", traceback.format_exc()
        if msg != "Empty queue":
            print("FATAL ERROR: irrecoverable information loss :(")

def start():
    """Starts the execution of the server."""
    if not Scheduler.is_running():
        ctx = zmq.Context.instance()
        s   = ctx.socket(zmq.PULL)
        s.bind(__transport)
        
        Scheduler.start()
        Scheduler.repeat_o_clock(3600, __queue_handler, "HOURLY", __hourly_queue)
        Scheduler.repeat_o_clock(3600*24, __queue_handler, "DAILY", __daily_queue)
        Scheduler.repeat_o_clock(3600*24*7, __queue_handler, "WEEKLY", __weekly_queue)
        
        print("Running server at ZMQ transport: " + __transport)
        try:
            while True:
                msg   = s.recv_pyobj()
                sched = msg["schedule"]
                txt   = __generate_message_line(msg)

                sys.stderr.write(txt + "\n")

                if sched == str(__schedules.INSTANTANEOUSLY):
                    subject = __generate_subject(__schedules.INSTANTANEOUSLY,
                                                 msg["name"])
                    try:
                        Utils.sendmail(__mail_credentials, subject, txt)
                    except:
                        print "Unexpected error:", traceback.format_exc()

                elif sched != __schedules.SILENTLY:
                    __schedule2queue[ sched ].put( (msg["datetime"],txt) )
        except:
            print("Stopping server")
            Scheduler.stop()
            raise

##############################################################################

if __name__ == "__main__": start()
