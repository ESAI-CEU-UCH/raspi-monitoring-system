#!env python2.7
"""
The purpose of this module is to allow messaging via email with a standalone
system. It needs you to install schedule module:

$ pip install enum

Example:

import MailLoggerClient
logger = MailLoggerClient.open() # it can receive a transport string
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

import zmq
from enum import Enum

default_transport = "ipc:///tmp/zmq_mail_logger_server.ipc"
levels = Enum('DEBUG', 'INFO', 'ALERT', 'WARNING', 'ERROR')
schedules = Enum('SILENTLY', 'INSTANTANEOUSLY', 'HOURLY', 'DAILY', 'WEEKLY')

class LoggerClient:

    def __init__(self, transport):
        self.__level2schedule = {
            str(levels.DEBUG)   : schedules.SILENTLY,
            str(levels.INFO)    : schedules.DAILY,
            str(levels.ALERT)   : schedules.INSTANTANEOUSLY,
            str(levels.WARNING) : schedules.INSTANTANEOUSLY,
            str(levels.ERROR)   : schedules.INSTANTANEOUSLY
        }
        self.ctx = zmq.Context.instance()
        self.s = self.ctx.socket(zmq.PUSH)
        self.s.connect(transport)
        self.levels = levels
        self.schedules = schedules

    def __del__(self):
        self.close()

    def __generate_message(self, level, schedule, text):
        return { "level" : str(level), "schedule" : str(schedule), "text" : text }

    def config(self, level, schedule):
        if not level in levels or not schedule in schedules:
            raise Exception("Needs a level and a schedule as arguments")
        self.__level2schedule[str(level)] = schedule

    def write(self, level, strfmt, *args):
        text = strfmt % args
        schedule = self.__level2schedule[str(level)]
        msg = self.__generate_message(level, schedule, text)
        self.s.send_pyobj(msg)

    def debug(self, strfmt, *args):
        self.write(levels.DEBUG, strfmt, *args)

    def info(self, strfmt, *args):
        self.write(levels.INFO, strfmt, *args)

    def alert(self, strfmt, *args):
        self.write(levels.ALERT, strfmt, *args)

    def warning(self, strfmt, *args):
        self.write(levels.WARNING, strfmt, *args)

    def error(self, strfmt, *args):
        self.write(levels.error, strfmt, *args)

    def close(self):
        if self.s is not None:
            self.s.close()
            self.s = None

def open(transport=default_transport):
    return LoggerClient(transport)
