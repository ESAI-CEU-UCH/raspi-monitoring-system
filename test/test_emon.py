import numpy
import sys
import time
sys.path.append("../")

import raspi_mon_sys.emonhub.emonhub_interfacer as emonhub_interfacer
import raspi_mon_sys.LoggerClient as LoggerClient
import raspi_mon_sys.ScreenLoggerServer as ScreenLoggerServer

DEFAULT_COM_BAUD = 38400
DEFAULT_COM_PORT = "/dev/ttyAMA0"
DEFAULT_TIMEOUT = 0

def try_input(msg, n):
    x = raw_input(msg + " (%s): "%str(n))
    if len(x) == 0: x = n
    print msg + "= %s"%str(x)
    return n

def configure_logger():
    transport = "ipc:///tmp/zmq_calibrate_util_server.ipc"
    ScreenLoggerServer.start_thread(transport)
    logger = LoggerClient.open("test_emon", transport)
    logger.config(logger.levels.DEBUG, logger.schedules.INSTANTANEOUSLY)
    logger.info("Opening connection")
    return logger

def configure_rfm69():
    iface = emonhub_interfacer.EmonHubJeeInterfacer("test_emon", logger,
                                                    DEFAULT_COM_PORT,
                                                    DEFAULT_COM_BAUD)
    return iface

def do_monitoring(logger, iface):
    while True:
        iface.run()
        # Read socket
        values = iface.read()
        if values is not None:
            print str(values)
        time.sleep(0.05)

if __name__ == "__main__":
    logger = configure_logger()
    iface = configure_rfm69()
    do_monitoring(logger, iface)
