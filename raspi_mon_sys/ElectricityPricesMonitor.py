#!/usr/bin/env python2.7
"""Recovers electricity prices and publish them using MQTT.

Following this [press notice](http://www.ree.es/es/sala-de-prensa/notas-de-prensa/2014/03/red-electrica-empieza-publicar-los-nuevos-precios-horarios-de-la-electricidad)
the prices for next day will be available every day at 20:15, so we can check
the price at 21:00 UTC in order to be sure they are available.
"""

# Copyright (C) 2015 Miguel Lorenzo
# Use of this source code is governed by the MIT license found in the LICENSE file.

from datetime import date, timedelta
import time
import datetime
import paho.mqtt.client as mqtt
import json
import urllib2
import traceback

import raspi_mon_sys.MailLoggerClient as MailLogger
import raspi_mon_sys.Utils as Utils

logger = MailLogger.open("ElectricityPricesMonitor")
topic = Utils.gettopic("electricity_prices")
url = 'http://www.esios.ree.es/Solicitar?fileName=PVPC_CURV_DD_{0}&fileType=txt&idioma=es'

def __on_connect(client, userdata, rc):
    logger.info("Connected to MQTT broker")

def __configure(client):
    client.on_connect = __on_connect

def publish(day_offset):
    """Publishes the electricity prices for next day."""
    try:
        client = Utils.getpahoclient(__configure)
    except:
        print "Unexpected error:", traceback.format_exc()
        logger.error("Error when connecting with MQTT broker")
        return
    try:
        # take the date for tomorrow
        dt=datetime.date.today() + datetime.timedelta(days=day_offset)
        tomorrow_url = url.format(dt.strftime("%Y%m%d"))
        # http request
        response_string = urllib2.urlopen(tomrrow_url)
        response = json.load(response_string)
        pvpc = response.PVPC
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
        
        # 25 hours because of CEST to CET transition day.
        prices = { 'GEN' : [0]*25, 'NOC' : [0]*25, 'VHC' : [0]*25 }
        n = 0
        # for every hour data in pvpc
        for res in pvpc:
            # TODO: check day value
            h = int( res['Hora'].split('-')[0] )
            for k in prices.keys():
                prices[k][h] = float( res[k].replace(',','.') ) # replace commas by dots
            n = n + 1
        # shrink prices to n length in case it is necessary
        if n < len(prices):
            for k,v in prices.iteritems(): prices[k] = v[0:n]
        message = { 'timestamp' : time.time(), 'data' : prices }
        client.publish(topic, json.dumps(message))
        logger.info("Electricity price published")
    except:
        print "Unexpected error:", traceback.format_exc()
        logger.error("Unable to retrieve electricity prices")
