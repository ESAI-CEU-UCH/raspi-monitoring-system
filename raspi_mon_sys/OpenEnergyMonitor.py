#!/usr/bin/env python2.7
"""This module publishes the data related with Open Energy Monitor devices.

This code is an adaptation of [emonhub](https://github.com/emonhub/emonhub).
"""

import serial

import raspi_mon_sys.emonhub.emonhub_interfacer as emonhub_interfacer
import raspi_mon_sys.MailLoggerClient as MailLogger

com_port = "/dev/ttyAMA0"
com_baud = 38400
timeout = 0

logger = MailLogger.open("OpenEnergyMonitor")
logger.info("Opening connection")

iface = emonhub_interfacer.EmonHubJeeInterfacer("raspimon", logger,
                                                com_port, com_baud)


# Execute run method
I.run()
# Read socket
values = I.read()
# If complete and valid data was received
if values is not None:
    # Place a copy of the values in a queue for each reporter
    for name in self._reporters:
        # discard if reporter 'pause' set to 'all' or 'in'
        if 'pause' in self._reporters[name]._settings \
           and str(self._reporters[name]._settings['pause']).lower() in \
           ['all', 'in']:
            continue
        print(values)
