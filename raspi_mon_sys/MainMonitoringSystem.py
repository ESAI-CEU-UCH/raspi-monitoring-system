#!/usr/bin/env python2.7
"""This module implements the main program for scheduling the monitoring system.

It should be executed from command line without arguments.
"""
import time
import traceback

import raspi_mon_sys.AEMETMonitor as AEMETMonitor
import raspi_mon_sys.CheckIP as CheckIP
import raspi_mon_sys.ElectricityPricesMonitor as ElectricityPrices
import raspi_mon_sys.InfluxDBHub as InfluxDBHub
import raspi_mon_sys.LoggerClient as LoggerClient
import raspi_mon_sys.MongoDBHub as MongoDBHub
import raspi_mon_sys.OpenEnergyMonitor as OpenEnergyMonitor
import raspi_mon_sys.PlugwiseMonitor as PlugwiseMonitor
import raspi_mon_sys.Scheduler as Scheduler
import raspi_mon_sys.Utils as Utils

def __try_call(logger, func, *args):
    try:
        func(*args)
        return True
    except:
        print "Unexpected error:",traceback.format_exc()
        logger.error("Unexpected error: %s", traceback.format_exc())
        return False

if __name__ == "__main__":
    Utils.startup_wait()
    
    T1_MILISECOND  = 1
    T1_CENTISECOND = 10
    T1_DECISECOND  = 100
    T1_SECOND      = 1000
    T1_MINUTE      = 60000
    T1_HOUR        = 3600000
    T1_DAY         = 24 * T1_HOUR

    # Configure logger.
    logger = LoggerClient.open("MainMonitoringSystem")

    logger.info("Initializing main monitoring system")

    # Configure Scheduler.
    Scheduler.start()
    
    logger.info("Scheduler started")
    
    # Start all modules.
    started_modules = []

    def try_start(module):
        if __try_call(logger, module.start):
            started_modules.append(module)
            return True
        return False

    if try_start(MongoDBHub):
        # repeat every hour with a 1/12th part as offset
        Scheduler.repeat_o_clock_with_offset(T1_HOUR, T1_HOUR/12, MongoDBHub.upload_data)

    if try_start(InfluxDBHub):
        # repeat every 10 seconds
        Scheduler.repeat_o_clock(10*T1_SECOND, InfluxDBHub.write_data)
    
    if try_start(AEMETMonitor):
        # publish last AEMET data
        __try_call(logger, AEMETMonitor.publish)
        # repeat every hour AEMET data capture
        Scheduler.repeat_o_clock(T1_HOUR, AEMETMonitor.publish)

    if try_start(CheckIP):
        # publish current IP
        __try_call(logger, CheckIP.publish)
        # repeat every time multiple of five minutes (at 00, 05, 10, 15, etc)
        Scheduler.repeat_o_clock(5 * T1_MINUTE, CheckIP.publish)

    if try_start(ElectricityPrices):
        # publish current electricity prices
        __try_call(logger, ElectricityPrices.publish, 0)
        if time.time()*1000 % T1_DAY > 21*T1_HOUR - 10*T1_SECOND:
            # publish next day electricity prices when starting the software at
            # night
            __try_call(logger, ElectricityPrices.publish, 1)
        # repeat every day at 21:00 UTC with prices for next day
        Scheduler.repeat_o_clock_with_offset(T1_DAY, 21 * T1_HOUR,
                                            ElectricityPrices.publish, 1)
    
    try_start(OpenEnergyMonitor)

    if try_start(PlugwiseMonitor):
        # repeat every second lectures from plugwise circles
        Scheduler.repeat_o_clock(10*T1_SECOND, PlugwiseMonitor.publish)
    
    logger.info("Scheduler configured")
    logger.info("Starting infinite loop")

    # Inifite loop.
    try:
        while True: time.sleep(60)
    except:
        logger.info("Stopping scheduler")
        Scheduler.stop()
        logger.info("Stopping modules")
        for m in started_modules: __try_call(logger, m.stop)
        logger.info("Bye!")
