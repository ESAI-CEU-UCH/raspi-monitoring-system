import numpy
import sys
import time
sys.path.append("../../")

import raspi_mon_sys.emonhub.emonhub_interfacer as emonhub_interfacer
import raspi_mon_sys.LoggerClient as LoggerClient
import raspi_mon_sys.ScreenLoggerServer as ScreenLoggerServer

DEFAULT_CTs = [ 2, 3, 4, 5 ]
DEFAULT_CALIBRATION_TIME = 60 # in seconds
DEFAULT_COM_BAUD = 38400
DEFAULT_COM_PORT = "/dev/ttyAMA0"
nodeId_reference = 10
DEFAULT_NUMBER_OF_LOOPS = 8
DEFAULT_POWER_REFERENCE = 40 # in Watts
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

def configure_user_options():
    time.sleep(1)
    nloops = int(try_input("Indicate number of loops", DEFAULT_NUMBER_OF_LOOPS))
    power = int(try_input("Indicate power reference", DEFAULT_POWER_REFERENCE))
    return nloops,power

def configure_rfm69():
    iface = emonhub_interfacer.EmonHubJeeInterfacer("calibration", logger,
                                                    DEFAULT_COM_PORT,
                                                    DEFAULT_COM_BAUD)
    return iface

def do_monitoring(logger, number_of_loops, power_reference, iface):
    measures = []
    t0 = time.time()
    while time.time() - t0 < calibration_time:
        iface.run()
        # Read socket
        values = iface.read()
        print values
        if values is not None:
            logger.debug(str(values))
            t      = values[0]
            nodeId = values[1]
            if nodeId == nodeId_reference:
                current = [ values[i]/number_of_loops for i in DEFAULT_CTs ]
                measures.append( current )
        time.sleep(0.05)
    m = numpy.array(measures)
    return m

if __name__ == "__main__":
    logger = configure_logger()
    number_of_loops,power_reference = configure_user_options()
    iface = configure_rfm69()
    m = do_monitoring(logger, number_of_loops, power_reference, iface)
    print "Mean values=    " + str( m.mean(axis=1) )
    print "Std-dev values= " + str( m.std(axis=1) )
