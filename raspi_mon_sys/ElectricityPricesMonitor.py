#!/usr/bin/env python2.7
"""Recovers electricity prices and publish them using MQTT.

Following this [press notice](http://www.ree.es/es/sala-de-prensa/notas-de-prensa/2014/03/red-electrica-empieza-publicar-los-nuevos-precios-horarios-de-la-electricidad)
the prices for next day will be available every day at 20:15, so we can check
the price at 21:00 UTC in order to be sure they are available. This module
publishes a sequence of messages as:

```
BASETOPIC/electricity_prices/GEN  {"timestamp":REF+0,"data":10}
BASETOPIC/electricity_prices/NOC  {"timestamp":REF+0,"data":66}
BASETOPIC/electricity_prices/VHC  {"timestamp":REF+0,"data":70}
BASETOPIC/electricity_prices/GEN  {"timestamp":REF+3600,"data":12}
BASETOPIC/electricity_prices/NOC  {"timestamp":REF+3600,"data":69}
BASETOPIC/electricity_prices/VHC  {"timestamp":REF+3600,"data":80}
...
```

This sequence can be interpreted as a time series of electricity prices for a
given day offset (current if `offset=0`, next if `offset=1`).
"""

# Copyright (C) 2015 Miguel Lorenzo, Francisco Zamora-Martinez
# Use of this source code is governed by the GPLv3 license found in the LICENSE file.

import datetime
import json
import paho.mqtt.client as mqtt
import time
import traceback
import urllib2

import raspi_mon_sys.MailLoggerClient as MailLogger
import raspi_mon_sys.Utils as Utils

logger = MailLogger.open("ElectricityPricesMonitor")
topic = Utils.gettopic("electricity_prices/{0}")
url = 'http://www.esios.ree.es/Solicitar?fileName=PVPC_CURV_DD_{0}&fileType=txt&idioma=es'

def __on_connect(client, userdata, rc):
    logger.info("Connected to MQTT broker")

def __configure(client):
    client.on_connect = __on_connect

def publish(day_offset):
    """Publishes the electricity prices for a given day offset.
    
    If `offset=0` prices will be for current day, if `offset=1` prices will be
    for next day, and so on.
    """
    try:
        client = Utils.getpahoclient(logger, __configure)
    except:
        logger.error("Error when connecting with MQTT broker")
        raise
    try:
        # take the date for tomorrow
        dt=datetime.date.today() + datetime.timedelta(days=day_offset)
        ref_time = time.mktime(dt.timetuple())
        tomorrow_url = url.format(dt.strftime("%Y%m%d"))
        # http request
        response_string = urllib2.urlopen(tomorrow_url)
    except:
        logger.error("Unable to retrieve electricity prices")
        client.disconnect()
        raise
    try:
        response = json.load(response_string)
        pvpc = response['PVPC']
        # PVPC is an array of dictionaries where every dictionary is:
        # {"Dia":"13/11/2015","Hora":"00-01",
        # "GEN":"126,08","NOC":"75,81","VHC":"79,94",
        # "COFGEN":"0,000075326953000000","COFNOC":"0,000158674625000000",
        # "COFVHC":"0,000134974129000000","PMHGEN":"66,35","PMHNOC":"63,98",
        # "PMHVHC":"66,63","SAHGEN":"6,14","SAHNOC":"5,92","SAHVHC":"6,17",
        # "FOMGEN":"0,03","FOMNOC":"0,03","FOMVHC":"0,03","FOSGEN":"0,13",
        # "FOSNOC":"0,12","FOSVHC":"0,13","INTGEN":"2,46","INTNOC":"2,37",
        # "INTVHC":"2,47","PCAPGEN":"6,94","PCAPNOC":"1,16","PCAPVHC":"1,64",
        # "TEUGEN":"44,03","TEUNOC":"2,22","TEUVHC":"2,88"}
        
        # Looking here: http://tarifaluzhora.es/ it seems that GEN is the main
        # electricity price, and it comes in thousandth of an euro.
        
        # It will send 25 hours at CEST to CET transition day.
        
        keys = [ 'GEN', 'NOC', 'VHC' ]
        # for every hour data in pvpc
        for res in pvpc:
            # TODO: check day value
            hour_offset = int( res['Hora'].split('-')[0] ) * 3600
            for k in keys:
                v = float( res[k].replace(',','.') ) # replace commas by dots
                message = { 'timestamp' : ref_time + hour_offset, 'data' : v }
                client.publish(topic.format(k), json.dumps(message))
        logger.info("Electricity price published")
    except:
        logger.info("Unable to publish electricity prices")
        client.disconnect()
        raise
