#!/usr/bin/env python2.7
"""This module implements the main program for scheduling the monitoring system.

It should be executed from command line without arguments.
"""
import time
import traceback

import raspi_mon_sys.CheckIP as CheckIP
import raspi_mon_sys.ElectricityPricesMonitor as ElectricityPrices
import raspi_mon_sys.MailLoggerClient as MailLoggerClient
import raspi_mon_sys.PlugwiseMonitor as PlugwiseMonitor
import raspi_mon_sys.Scheduler as Scheduler

if __name__ == "__main__":
    T1_MILISECOND  = 1
    T1_CENTISECOND = 10
    T1_DECISECOND  = 100
    T1_SECOND      = 1000
    T1_MINUTE      = 60000
    T1_HOUR        = 3600000
    T1_DAY         = 24 * T1_HOUR

    # Configure logger.
    logger = MailLoggerClient.open("MainMonitoringSystem")

    logger.info("Initializing main monitoring system")

    # Configure Scheduler.
    Scheduler.start()

    logger.info("Scheduler started")

    # Start all modules.
    CheckIP.start()
    ElectricityPrices.start()
    PlugwiseMonitor.start()
    
    # publish current electricity prices
    ElectricityPrices.publish(0)

    # repeat every time multiple of five minutes (at 00, 05, 10, 15, etc)
    Scheduler.repeat_o_clock(5 * T1_MINUTE, CheckIP.publish)
    # repeat every day at 21:00 UTC with prices for next day
    Scheduler.repeat_o_clock_with_offset(T1_DAY, 21 * T1_HOUR,
                                         ElectricityPrices.publish, 1)
    # repeat every second lectures from plugwise circles
    Scheduler.repeat_o_clock(T1_SECOND, PlugwiseMonitor.publish)

    logger.info("Scheduler configured")
    logger.info("Starting infinite loop")

    # Inifite loop.
    try:
        while True: time.sleep(60)
    except:
        logger.info("Stopping scheduler")
        Scheduler.stop()
        logger.info("Bye!")
