import numpy
import sys
import time
sys.path.append("../../")

import raspi_mon_sys.emonhub.emonhub_interfacer as emonhub_interfacer
import raspi_mon_sys.LoggerClient as LoggerClient
import raspi_mon_sys.ScreenLoggerServer as ScreenLoggerServer

DEFAULT_CTs = [ 2, 3, 4, 5 ]
DEFAULT_CALIBRATION_TIME = 300 # in seconds
DEFAULT_COM_BAUD = 38400
DEFAULT_COM_PORT = "/dev/ttyAMA0"
nodeId_reference = 10
DEFAULT_TIMEOUT = 0

def try_input(msg, n):
    x = raw_input(msg + " (%s): "%str(n))
    if len(x) == 0: x = n
    print msg + "= %s"%str(x)
    return n

def configure_logger():
    transport = "ipc:///tmp/zmq_calibrate_util_server.ipc"
    ScreenLoggerServer.start_thread(transport)
    logger = LoggerClient.open("calibrate", transport)
    logger.config(logger.levels.DEBUG, logger.schedules.INSTANTANEOUSLY)
    logger.info("Opening connection")
    return logger

def configure_rfm69():
    iface = emonhub_interfacer.EmonHubJeeInterfacer("calibration", logger,
                                                    DEFAULT_COM_PORT,
                                                    DEFAULT_COM_BAUD)
    return iface

def do_monitoring(logger, iface):
    measures = []
    t0 = time.time()
    while time.time() - t0 < DEFAULT_CALIBRATION_TIME:
        iface.run()
        # Read socket
        values = iface.read()
        if values is not None:
            logger.debug("Elapsed time %6.1f (%3.0f%%)", time.time() - t0,
                         (time.time() - t0) / DEFAULT_CALIBRATION_TIME * 100)
            logger.debug(str(values))
            t      = values[0]
            nodeId = values[1]
            if nodeId == nodeId_reference:
                current = [ values[i] for i in DEFAULT_CTs if values[i] > 0 ]
                measures.append( current )
        time.sleep(0.05)
    m = numpy.array(measures)
    return m

if __name__ == "__main__":
    logger = configure_logger()
    iface = configure_rfm69()
    m = do_monitoring(logger, iface)
    means = m.mean(axis=0)
    stds = m.std(axis=0)
    mins = m.min(axis=0)
    maxs = m.max(axis=0)
    result = numpy.concatenate( means, stds, mins, maxs )
    print "# Mean   Stdanrd-deviations   Minimum   Maximum"
    print result
