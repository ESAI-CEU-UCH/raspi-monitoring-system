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

def __replace_vars(x, module):
    if not x.startswith("$this."): return x
    x.replace("$this.","")
    method = getattr(module,x)
    return method

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

    def try_start(module_info):
        module = __import__(module_info["import"])
        print module
        if __try_call(logger, module.start):
            started_modules.append(module)
            if "schedule_method" in module_info:
                method = getattr(Scheduler, module_info["schedule_method"])
                args = [ __replace_vars(x,module) for x in module_info["schedule_args"] ]
                method(args)
            return True
        return False

    config = Utils.getconfig("main", logger)
    for module_info in config["modules"]: try_start(module_info)
    
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
