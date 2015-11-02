#!env python2.7
"""The purpose of this module is to allow messaging via email with a standalone
system. It needs you to install enum module:

$ pip install enum

The module exports the following levels and schedules:

  - levels: DEBUG, INFO, ALERT, WARNING, ERROR
  - schedules: SILENTLY, INSTANTANEOUSLY, HOURLY, DAILY, WEEKLY

Schedules are based on UTC timestamps, so don't expect to be correlated with
local time zone.

Example:

import raspi_mon_sys.MailLoggerClient as MailLoggerClient
logger = MailLoggerClient.open("name") # it can receive a transport string
logger.debug("Program traces and related stuff.")
logger.info("Any useful information.")
logger.warning("Be careful, error incoming.")
logger.error("Something bad happened but the system still working.")
logger.alert("Something really bad happened.")
logger.write(MailLoggerClient.levels.DEBUG, "Another debug info.")


The default configuration is as follows:

logger.config(logger.levels.DEBUG, logger.schedules.SILENTLY)
logger.config(logger.levels.INFO, logger.schedules.DAILY)
logger.config(logger.levels.ALERT, logger.schedules.INSTANTANEOUSLY)
logger.config(logger.levels.WARNING, logger.schedules.INSTANTANEOUSLY)
logger.config(logger.levels.ERROR, logger.schedules.INSTANTANEOUSLY)

"""
from enum import Enum

import datetime
import threading
import zmq

default_transport = "ipc:///tmp/zmq_mail_logger_server.ipc"
levels = Enum('DEBUG', 'INFO', 'ALERT', 'WARNING', 'ERROR')
schedules = Enum('SILENTLY', 'INSTANTANEOUSLY', 'HOURLY', 'DAILY', 'WEEKLY')

class LoggerClient:
    """This class implements the interface to communicate with MailLoggerServer."""

    def __init__(self, name, transport):
        """Initializes connection with server using the given transport and
        builds a default mapping between levels and schedules."""
        self.__level2schedule = {
            str(levels.DEBUG)   : schedules.SILENTLY,
            str(levels.INFO)    : schedules.DAILY,
            str(levels.ALERT)   : schedules.INSTANTANEOUSLY,
            str(levels.WARNING) : schedules.INSTANTANEOUSLY,
            str(levels.ERROR)   : schedules.INSTANTANEOUSLY
        }
        ctx = zmq.Context.instance()
        self.__s = ctx.socket(zmq.PUSH)
        self.__s.connect(transport)
        self.__transport = transport
        self.__lock = threading.RLock()
        self.__name = name
        self.levels = levels
        self.schedules = schedules

    def __del__(self):
        self.close()

    def __generate_message(self, name, level, schedule, text):
        return {
            "name"     : name,
            "level"    : str(level),
            "schedule" : str(schedule),
            "text"     : text,
            "datetime" : datetime.datetime.now()
        }
        
    def clone(self):
        other = LoggerClient(self.__name, self.__transport)
        self.__lock.acquire()
        for k,v in self.__level2schedule.iteritems():
            other.__level2schedule[k] = v
        self.__lock.release()

    def config(self, level, schedule):
        """Associates the given level with the given schedule."""
        if not level in levels or not schedule in schedules:
            raise Exception("Needs a level and a schedule as arguments")
        self.__lock.acquire()
        self.__level2schedule[str(level)] = schedule
        self.__lock.release()

    def write(self, level, strfmt, *args):
        """Writes a text string using the given level.
        
        This function implements kind of printf(), so it receives a string
        format and a variadic list of values.
        """
        text = strfmt % args
        self.__lock.acquire()
        schedule = self.__level2schedule[str(level)]
        msg = self.__generate_message(self.__name, level, schedule, text)
        self.__s.send_pyobj(msg)
        self.__lock.release()

    def debug(self, strfmt, *args):
        """Writes a text string at DEBUG level.
        
        This function implements kind of printf(), so it receives a string
        format and a variadic list of values.
        """
        self.write(levels.DEBUG, strfmt, *args)

    def info(self, strfmt, *args):
        """Writes a text string at INFO level.
        
        This function implements kind of printf(), so it receives a string
        format and a variadic list of values.
        """
        self.write(levels.INFO, strfmt, *args)

    def alert(self, strfmt, *args):
        """Writes a text string at ALERT level.
        
        This function implements kind of printf(), so it receives a string
        format and a variadic list of values.
        """
        self.write(levels.ALERT, strfmt, *args)

    def warning(self, strfmt, *args):
        """Writes a text string at WARNING level.

        This function implements kind of printf(), so it receives a string
        format and a variadic list of values.
        """
        self.write(levels.WARNING, strfmt, *args)

    def error(self, strfmt, *args):
        """Writes a text string at ERROR level.

        This function implements kind of printf(), so it receives a string
        format and a variadic list of values.
        """
        self.write(levels.error, strfmt, *args)

    def close(self):
        """Terminates connection with MailLoggerServer.."""
        self.__lock.acquire()
        if self.__s is not None:
            self.__s.close()
            self.__s = None
        self.__lock.release()

def open(name,transport=default_transport):
    """Returns a new LoggerClient() instance."""
    return LoggerClient(name,transport)
