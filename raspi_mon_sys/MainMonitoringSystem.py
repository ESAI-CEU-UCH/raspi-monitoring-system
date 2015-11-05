#!/usr/bin/env python2.7
"""This module implements the main program for scheduling the monitoring system.

It should be executed from command line without arguments.
"""
import paho.mqtt.client as paho

import time
import traceback

import raspi_mon_sys.CheckIP as CheckIP
import raspi_mon_sys.MailLoggerClient as MailLoggerClient
import raspi_mon_sys.Scheduler as Scheduler

if __name__ == "__main__":
    T1_MILISECOND  = 0.001
    T1_CENTISECOND = 0.01
    T1_DECISECOND  = 0.1
    T1_SECOND      = 1
    T1_MINUTE      = 60
    T1_HOUR        = 3600

    PAHO_HOST     = "localhost"
    PAHO_PORT     = 1883
    PAHO_TIMEOUT  = 60

    # Configure logger.
    logger = MailLoggerClient.open("MainMonitoringSystem")

    logger.info("Initializing main monitoring system")

    try:
        # Configure Paho.
        client = paho.Client()
        client.connect(PAHO_HOST, PAHO_PORT, PAHO_TIMEOUT)
        client.loop_start()
    except:
        logger.alert("Unable to connect with Paho server")
        raise

    logger.info("Paho initialized at %s:%d with timeout=%d",
                PAHO_HOST, PAHO_PORT, PAHO_TIMEOUT)

    # Configure Scheduler.
    Scheduler.start()

    logger.info("Scheduler started")

    Scheduler.repeat_o_clock(5 * T1_MINUTE, CheckIP.publish)

    logger.info("Scheduler configured")
    logger.info("Starting infinite loop")

    # Inifite loop.
    try:
        while True: time.sleep(60)
    except:
        logger.info("Stopping scheduler")
        Scheduler.stop()
        logger.info("Bye!")
