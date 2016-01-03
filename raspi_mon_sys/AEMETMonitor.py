#!/usr/bin/env python2.7
"""This module publishes current weather data from AEMET and future forecasts for
today and tomorrow.

This module is particularly different from other ones because its data is
published using two different topic roots. It publishes under
`BASETOPIC/aemet/NAME/ID` current weather status, and under
`forecast/RASPIMAC/aemet/HORIZON/NAME/ID` where `ID` is the location identifier,
`NAME` is the particular data identifier (wind,
rain, temperature, min_temperature, max_temperature, etc.) and `HORIZON` is the
forecast horizon (hourly, two_days, week, etc.). Messages for `raspimon` are a
usual with two data fields `timestamp` and `data`. For `forecast/aemet` they are
more complex with the following fields:

- `timestamp`: when the data has been captured (it can be a time mark given by
  AEMET or given by us when downloading the data).

- `values`: a list of forecast parameters.

- `periods_start`: a list of timestamps indicating period start times.

- `periods_end`: a list of timestamps indicating period last times. This
  can be None (null in JSON) when the data is not for a period.

Valencia current weather data::

    Ind. climatologico: 8416Y -  Altitud (m): 11
    Latitude: 39 28' 50'' N - Longitude: 0 21' 59'' O

http://www.aemet.es/es/eltiempo/observacion/ultimosdatos?k=val&l=8416Y&w=0&datos=det&x=h24&f=temperatura

http://www.aemet.es/es/eltiempo/observacion/ultimosdatos_8416Y_datos-horarios.csv?k=val&l=8416Y&datos=det&w=0&f=temperatura&x=h24

Valencia weather forecast data::

    Capital: Valencia (altitud: 16 m)
    Latitude: 39 28' 31'' N - Longitude: 0 22' 32' O
    Zona de avisos: Litoral norte de Valencia

http://www.aemet.es/es/eltiempo/prediccion/municipios/valencia-id46250

48 hours forecasts are not public in XML or CSV formats (or I'm unable to found
them). We need to rely in the web page:
http://www.aemet.es/es/eltiempo/prediccion/municipios/horas/tabla/valencia-id46250

Wind speeds is measured in km/h, rain in mm, probabilities and humidity in %,
snow level in m, snow in mm, rain_prob and snow_prob in %, pressure in hPa.

The table of sky description and other stuff is available here:
http://www.aemet.es/en/eltiempo/prediccion/municipios/zaragoza-id50297/ayuda

All descriptions and names are translated into English in order to normalize
their string representation in the database.

"""

# Copyright (C) 2015 Miguel Lorenzo, Francisco Zamora-Martinez
# Use of this source code is governed by the GPLv3 license found in the LICENSE file.

import csv
import json
import datetime
import pytz
import re
import requests
import time
import traceback
import unicodedata
import urllib2

from xml.etree.ElementTree import parse

import raspi_mon_sys.aemet as aemet
import raspi_mon_sys.LoggerClient as LoggerClient
import raspi_mon_sys.Utils as Utils

NUM_DAYS = 4

weather_topic  = Utils.gettopic("aemet/{0}/{1}")
forecast_topic = Utils.gettopic("aemet/{0}/{1}/{2}", "forecast")

# This variables are loaded from MongoDB server at start() function.
tz = None
logger = None
current_weather_url = None
location_id = None
config = None

daily_forecast_info = (
    # more than one value
    ( "get_precipitacion", "period", "rain_prob" ),
    ( "get_cota_nieve", "period", "snow_level" ),
    ( "get_estado_cielo", "period", "sky" ),
    ( "get_viento", "period", "wind_direction", "wind_speed" ),
    ( "get_racha", "period", "wind_gust" ),
    ( "get_temperatura_horas", "hour", "temperature" ),
    ( "get_sensacion_termica", "hour", "thermal_sens" ),
    ( "get_humedad", "hour", "humidity"),
    # only one value
    ( "get_temperatura_maxima", "max_temp" ),
    ( "get_temperatura_minima", "min_temp" ),
    ( "get_sensacion_termica_maxima", "max_thermal_sens" ),
    ( "get_sensacion_termica_minima", "min_thermal_sens" ),
    ( "get_humedad_maxima", "max_humidity" ),
    ( "get_humedad_minima", "min_humidity" ),
    ( "get_uv_max", "max_uv" )
)

translations = aemet.translations

def __normalize(x):
    """Remove non ASCII characters and left/right trailing whitespaces. All interior
    whitespaces, newlines, etc. by underscore characters. It transforms the
    sequence into lowercase. It also replaces / by _ and removing %.
    Additionally it removes any sequence enclosed between parentheses. And
    finally this function translates into English for normalization purposes.

    """
    if type(x) is list or type(x) is tuple: return [ __normalize(y) for y in x ]
    if type(x) != str and type(x) != unicode: return x
    # Be careful with this function, in the future it should be used to
    # translate Spanish or other language strings into English.
    if type(x) != unicode:
        try:
            x = unicode(x, "utf-8")
        except:
            try:
                x = unicode(x, "iso-8859-1")
            except:
                x = unicode(x, "utf-8", errors="ignore")
    x = re.sub(r'\([^)]*\)', '', x)
    x = x.strip()
    x = unicodedata.normalize("NFKD",x).encode("ascii","ignore")
    x = x.replace(" ","_").replace("\t","_").replace("\n","_").replace("\r","_")
    x = x.replace("/","_").replace("%","")
    x = x.lower()
    y = translations.get(x, x)
    if y == x: logger.debug(x)
    return y

def __try_number(x):
    if type(x) is list or type(x) is tuple:
        return [ __try_number(y) for y in x ]
    try:
        x_float = float(x)
        try:
            x_int = int(x)
        except:
            x_int = 0
        if x_float == x_int: return x_int
        return x_float
    except:
        return x

def __try_element(e, child, func):
    try:
        x = func( e.find(child) )
        return x
    except:
        return None

def __datetimestr2time(s, fmt="%Y-%m-%dT%H:%M:%S"):
    dt = tz.localize( datetime.datetime.strptime(s, fmt) )
    return time.mktime(dt.timetuple())

def __datestr2time(s): return __datetimestr2time(s, "%Y-%m-%d")

def __on_connect(client, userdata, rc):
    logger.info("Connected to MQTT broker")

def __configure(client):
    client.on_connect = __on_connect

def __process_daily_forecast_hour(result):
    for x in result: x[0] = [ x[0], int(x[0])+1 ] # one hour period
    return result

def __process_daily_forecast_period(result):
    def try_pop(x,n,v):
        y = x.pop(n)
        if y[0] != v: x.insert(n, y)
        
    if len(result) == 7:
        try_pop(result, 2, "12-24")
        try_pop(result, 1, "00-12")
        try_pop(result, 0, "00-24")

    elif len(result) == 3 or len(result) == 5: try_pop(result, 0, "00-24")

    for x in result:
        if x[0] is None:
            x[0] = 0
        else:
            dash_pos = x[0].find("-")
            x[0] = [ x[0][0:dash_pos], x[0][dash_pos+1:] ]

    return result

def __process_daily_forecast_singleton(result):
    return [ [ [0,24], result ] ]

def __process_daily_forecast_list(days_parsers, func, method_name, *args):
    all_days = [ __try_number(__normalize( func(getattr(day, method_name)()) )) for day in days_parsers ]
    all_days = [ [ [ z*3600 + __datestr2time(day.fecha) for z in x[0] ] ] + x[1:]
                 for i,day in enumerate(days_parsers) for x in all_days[i] ]
    all_datas = [ x for x in zip(*all_days) ]
    # print 3600,3600*6,3600*12,3600*24,[ x[1] - x[0] for x in all_datas[0] ]
    series = { name : all_datas[i] for i,name in enumerate(args) }
    return series

def __process_daily_forecast(days_parsers, *args):
    try:
        cls = args[1]
        if cls == "hour":
            x = args[2:]
            series = __process_daily_forecast_list(days_parsers, __process_daily_forecast_hour, args[0], "period", *x)
        elif cls == "period":
            x = args[2:]
            try:
                series = __process_daily_forecast_list(days_parsers, __process_daily_forecast_period, args[0], "period", *x)
            except TypeError:
                if len(x) == 1:
                    series = __process_daily_forecast_list(days_parsers, __process_daily_forecast_singleton, args[0], "period", *x)
                else:
                    raise
            except:
                raise
        else:
            assert len(args) == 2
            series = __process_daily_forecast_list(days_parsers, __process_daily_forecast_singleton, args[0], "period", args[1])
        period  = series.pop("period")
        periods = [ x for x in zip(*period) ]
        assert len(periods) == 2
        
        pre_messages = [
            {
                "content_key" : key,
                "periods_start" : periods[0],
                "periods_end" : periods[1],
                "values" : values
            }
            for key,values in series.iteritems()
        ]
        return pre_messages
    except:
        print "Unable to retrieve daily forecast for %s:"%(str(args)), traceback.format_exc()
        logger.error("Unable to retrieve daily forecast for %s: %s", str(args),
                     traceback.format_exc())        
        return []

def __publish_daily_forecast(client):
    try:
        aemet_parser = aemet.Localidad(location_id)
    
        # sanity check
        assert aemet_parser.get_localidad() == "Valencia"
    
        now = datetime.datetime.now()
        days = [ now + datetime.timedelta(i) for i in range(NUM_DAYS) ]
        days_parsers = [ aemet_parser.parse_datos_fecha(x) for x in days ]
        pre_messages = [ x for st in daily_forecast_info for x in __process_daily_forecast(days_parsers, *st) ]
        when = __datetimestr2time( aemet_parser.get_fecha_actualizacion() )
    
        for msg in pre_messages:
            key = msg.pop("content_key")
            msg["timestamp"] = when
            client.publish(forecast_topic.format("daily", key, location_id),
                           json.dumps(msg))
    except:
        print "Unable to retrieve daily forecast:", traceback.format_exc()
        logger.error("Unable to retrieve daily forecast: %s", traceback.format_exc())

def __process_hourly_forecast(result, name, dia, *args):
    t = __datetimestr2time(dia.get("fecha"), "%Y-%m-%d")
    for node in dia.findall(name):
        periodo = node.get(u"periodo")
        if periodo is not None:
            if len(periodo) == 2:
                h1 = t + int(periodo)*3600.0
                h2 = t + int(periodo)*3600.0 + 3600.0
            else:
                assert len(periodo) == 4
                h1 = t + int(periodo[0:2])*3600.0 - 3600.0
                h2 = t + int(periodo[2:4])*3600.0 - 3600.0
            for fn in args:
                k,v = fn(name,node)
                if v is not None:
                    l = result.setdefault(__normalize(k),
                                          { "periods_start":[], "periods_end":[], "values":[] })
                    l["periods_start"].append(h1)
                    l["periods_end"].append(h2)
                    l["values"].append(__try_number(__normalize(v)))

def __publish_hourly_forecast(client):
    try:
        url = 'http://www.aemet.es/xml/municipios_h/localidad_h_' + location_id + '.xml'
        doc = parse(urllib2.urlopen(url)).getroot()
        pred = doc.find("prediccion")
        result = {}
        for dia in pred.findall("dia"):
            for item_name in ["precipitacion","prob_precipitacion","prob_tormenta","nieve","prob_nieve","temperatura","sens_termica","humedad_relativa","racha_max"]:
                __process_hourly_forecast(result, item_name, dia, lambda name,x: (name,x.text))
            __process_hourly_forecast(result, "estado_cielo", dia, lambda name,x: (name,x.get('description')))
            __process_hourly_forecast(result, "viento", dia,
                                      lambda name,x: ("velocidad_del_viento",x.find('velocidad').text),
                                      lambda name,x: ("direccion_del_viento",x.find('direccion').text))
        when = time.time()
        for key,msg in result.iteritems():
            msg["timestamp"] = when
            client.publish(forecast_topic.format("hourly", key, location_id),
                           json.dumps(msg))
    except:
        print "Unable to retrieve hourly forecast:", traceback.format_exc()
        logger.error("Unable to retrieve hourly forecast: %s", traceback.format_exc())

def __publish_current_weather_status(client):
    response = urllib2.urlopen(current_weather_url)
    try:
        # First three lines are rubbish.
        for i in range(3): response.readline()
        reader = csv.reader(response)
        table = list(reader)
    
        names = [ __normalize(x) for x in table[0] ]
        values = [ __try_number(__normalize(x)) for x in table[1] ]

        names.pop(0)
        dt_str = values.pop(0)
        t = __datetimestr2time(dt_str, "%d_%m_%Y_%H:%M")

        for name,value in zip(names,values):
            if type(value) == str and len(value) == 0: value = None
            msg = { "timestamp" : t, "data" : value }
            client.publish(weather_topic.format(name,location_id), json.dumps(msg))

    except:
        print "Unable to retrieve current weather status:", traceback.format_exc()
        logger.error("Unable to retrieve current weather status: %s", traceback.format_exc())

def publish():
    global tz
    tz = pytz.timezone("Europe/Madrid")
    try:
        client = Utils.getpahoclient(logger)
        __publish_daily_forecast(client)
        __publish_hourly_forecast(client)
        __publish_current_weather_status(client)
        client.disconnect()
        
    except:
        print "Unexpected error:", traceback.format_exc()
        logger.error("Unexpected error: %s", traceback.format_exc())

def start():
    """Opens logger connection and loads its configuration from MongoDB and sends
    first message."""
    global logger
    global config
    global location_id
    global current_weather_url
    logger = LoggerClient.open("AEMETMonitor")
    config = Utils.getconfig("aemet", logger)
    location_id = config["location_id"]
    current_weather_url = config["current_weather_url"]
    publish()

def stop():
    """Closes connection with logger."""
    logger.close()

if __name__ == "__main__":
    import raspi_mon_sys.ScreenLoggerServer as ScreenLoggerServer
    transport = "ipc:///tmp/zmq_aemet_server.ipc"
    ScreenLoggerServer.start_thread(transport)
    
    class MQTTClientFake:
        def publish(self, *args):
            print args

    tz = pytz.timezone("Europe/Madrid")
    logger = LoggerClient.open("AEMETMonitor", transport)
    # logger.config(logger.levels.DEBUG, logger.schedules.INSTANTANEOUSLY)
    current_weather_url = "http://www.aemet.es/es/eltiempo/observacion/ultimosdatos_8416Y_datos-horarios.csv?k=val&l=8416Y&datos=det&w=0&f=temperatura&x=h24"
    location_id = "46250"
    client = MQTTClientFake()
    __publish_daily_forecast(client)
    __publish_hourly_forecast(client)
    __publish_current_weather_status(client)
