#!env python2.7
"""
The purpose of this module is to allow messaging via email with a standalone
system. It needs you to install schedule module:

$ pip install enum

And is executed as:

$ python MailLoggerServer.py mail_credentials [zmq_transport]
"""
from uuid import getnode as get_mac

import datetime
import json
import Queue
import Scheduler
import socket
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

__mac_addr = hex(get_mac()).replace('0x','')

# Queues of pending messages.
__hourly_queue = Queue.Queue()
__daily_queue  = Queue.Queue()
__weekly_queue = Queue.Queue()

# Enums.
__levels    = MailLoggerClient.levels
__schedules = MailLoggerClient.schedules

__schedule2queue = {
    str(__schedules.HOURLY) : __hourly_queue,
    str(__schedules.DAILY)  : __daily_queue,
    str(__schedules.WEEKLY) : __weekly_queue
}

def __generate_message_line(msg):
    time_str     = datetime.datetime.strftime(datetime.datetime.now(), "%c")
    host_str     = socket.gethostname()
    level_str    = msg["level"]
    schedule_str = msg["schedule"]
    text_str     = msg["text"].replace('\n', '\\n')
    line_str     = "%s %s %s %9s %17s: %s"%(time_str, host_str, __mac_addr,
                                            level_str, schedule_str, text_str)
    return line_str

def __generate_subject(frequency):
    return "MailLogger raspi %s -- %s"%(__mac_addr, str(frequency))

def __queue_handler(frequency, queue):
    subject = __generate_subject(frequency)
    if queue.empty():
        msg = "Empty queue"
    else:
        lines_list = []
        while not queue.empty(): lines_list.append( queue.get() )
        msg = '\n'.join( lines_list )
    Utils.sendmail(__mail_credentials, subject, msg)

def start():
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
                    subject = __generate_subject(__schedules.INSTANTANEOUSLY)
                    Utils.sendmail(__mail_credentials, subject, txt)

                elif sched != __schedules.SILENTLY:
                    __schedule2queue[ sched ].put( txt )
        except:
            print("Stopping server")
            Scheduler.stop()
            raise

##############################################################################

if __name__ == "__main__": start()
