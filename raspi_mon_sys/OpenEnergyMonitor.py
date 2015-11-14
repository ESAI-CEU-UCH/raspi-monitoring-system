#!/usr/bin/env python2.7
"""This module publishes the data related with Open Energy Monitor devices.

This code is an adaptation of [emonhub](https://github.com/emonhub/emonhub).
"""

import serial
import time

import raspi_mon_sys.emonhub.emonhub_interfacer as emonhub_interfacer
import raspi_mon_sys.MailLoggerClient as MailLogger

com_port = "/dev/ttyAMA0"
com_baud = 38400
timeout = 0

logger = MailLogger.open("OpenEnergyMonitor")
logger.info("Opening connection")

iface = emonhub_interfacer.EmonHubJeeInterfacer("raspimon", logger,
                                                com_port, com_baud)


while True:
    # Execute run method
    iface.run()
    # Read socket
    values = iface.read()
    # If complete and valid data was received
    if values is not None:
        print(values)
    time.sleep(0.1)
    print("EO")
