#!/usr/bin/env python2.7
"""This module publishes current weather data from AEMET and future forecasts for
today and tomorrow.

This module is particularly different from other ones because its data is
published using two different topic roots. It publishes under
`raspimon/aemet/ID/NAME/#` current weather status, and under
`aemet/forecast/ID/HORIZON/NAME/#` where `ID` is the location identifier,
`NAME` is the particular data identifier (wind,
rain, temperature, min_temperature, max_temperature, etc.) and `HORIZON` is the
forecast horizon (hourly, two_days, week, etc.). Messages for `raspimon` are a
usual with two data fields `timestamp` and `data`. For `aemet/forecast` they are
more complex with the following fields:

- `timestamp`: when the data has been captured (it can be a time mark given by
  AEMET or given by us when downloading the data).

- `values`: a list of forecast parameters.

- `period_first_times`: a list of timestamps indicating period start times.

- `period_last_times`: a list of timestamps indicating period last times. This
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
http://www.aemet.es/es/eltiempo/prediccion/municipios/tabla/valencia-id46250

Wind is measured in km/h, rain in mm, probabilities and humidity in %, snow
level in m.

"""

# Copyright (C) 2015 Miguel Lorenzo, Francisco Zamora-Martinez
# Use of this source code is governed by the GPLv3 license found in the LICENSE file.

import csv
import json
import datetime
import pytz
import requests
import time
import traceback
import unicodedata
import urllib2

from lxml import html

import raspi_mon_sys.aemet as aemet
import raspi_mon_sys.LoggerClient as LoggerClient
import raspi_mon_sys.Utils as Utils

NUM_DAYS = 4

weather_topic  = Utils.gettopic("aemet/{0}/{1}")
forecast_topic = "aemet/forecast/{0}/{1}/{2}"

# This variables are loaded from MongoDB server at start() function.
tz = None
logger = None
current_weather_url = None
hourly_forecast_url = None
location_id = None

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

def __normalize(x):
    """Remove non ASCII characters and left/right trailing whitespaces. All
    interior whitespaces, newlines, etc. by underscore characters. It
    transforms the sequence into lowercase. It also replaces / by _ and % by p.
    Finally it removes any sequence enclosed between parentheses.

    In the future this function should translate into English for normalization
    purposes.

    """
    if type(x) is list or type(x) is tuple: return [ __normalize(y) for y in x ]
    if type(x) != str and type(x) != unicode: return x
    # Be careful with this function, in the future it should be used to
    # translate Spanish or other language strings into English.
    if type(x) != unicode: x = unicode(x, errors="ignore")
    x = x.strip()
    x = unicodedata.normalize("NFKD",x).encode("ascii","ignore")
    x = x.replace(" ","_").replace("\t","_").replace("\n","_").replace("\r","_")
    x = x.replace("/","_").replace("%","p")
    x = x.lower()
    return x

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
    return time.mktime(dt.utctimetuple())

def __datestr2time(s): return __datetimestr2time(s, "%Y-%m-%d")

def __on_connect(client, userdata, rc):
    logger.info("Connected to MQTT broker")

def __configure(client):
    client.on_connect = __on_connect

def __process_daily_forecast_hour(result):
    for x in result: x[0] = [ x[0] ]
    return result

def __process_daily_forecast_period(result):
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
    all_days = [ [ [ z + __datestr2time(day.fecha) for z in x[0] ] ] + x[1:]
                 for i,day in enumerate(days_parsers) for x in all_days[i] ]
    all_datas = [ x for x in zip(*all_days) ]
    series = { name : all_datas[i] for i,name in enumerate(args) }
    return series

def __process_daily_forecast(days_parsers, *args):
    cls = args[1]
    if cls == "hour":
        x = args[2:]
        series = __process_daily_forecast_list(days_parsers, __process_daily_forecast_hour, args[0], "period", *x)
    elif cls == "period":
        x = args[2:]
        series = __process_daily_forecast_list(days_parsers, __process_daily_forecast_period, args[0], "period", *x)
    else:
        assert len(args) == 2
        series = __process_daily_forecast_list(days_parsers, __process_daily_forecast_singleton, args[0], "period", args[1])
    period = series.pop("period")
    aux = [ x for x in zip(*period) ]
    if len(aux) == 1: aux.append(None)
    pre_messages = [
        {
            "content_key" : key,
            "period_first_times" : aux[0],
            "period_last_times" : aux[1],
            "values" : values
        }
        for key,values in series.iteritems()
    ]
    return pre_messages

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
            client.publish(forecast_topic.format(location_id, "daily", key),
                           json.dumps(msg))
    except:
        print "Unable to retrieve daily forecast:", traceback.format_exc()
        logger.error("Unable to retrieve daily forecast: %s", traceback.format_exc())

def __publish_hourly_forecast(client):
    """Traverses the HTML web page of AEMET and transforms it into forecast
    MQTT messages as described above in this module documentation.
    
    All input strings are normalized to be in lower case, using underscores in
    any whitespace character, replacing accents and other non ASCII characters
    by its closest ASCII character.

    """
    try:
        d = datetime.date.today()
        t = tz.localize( datetime.datetime(d.year, d.month, d.day) )
        doc = html.fromstring(requests.get(hourly_forecast_url).content)
        pred = doc.get_element_by_id("tabla_prediccion")
        head = pred.find("thead").find("tr")
        body = pred.find("tbody")
        series_names = [ elem.get("title") for elem in head.findall("th") ]
        series_names.append("Direccion viento")
        series_data = [ [] for i in range(len(series_names)) ]
        delta = int( body.find("tr").find("td").text )
        t = t + datetime.timedelta(0, delta * 3600)
        for row in body.findall("tr"):
            series_data[0].append(time.mktime(t.utctimetuple()))
            t = t + datetime.timedelta(0, 3600)
            j = 0
            for i,elem in enumerate(row.findall("td")):
                j += 1
                try:
                    # in order to process properly rowspan property we need to
                    # skip as many columns as they have more than content than
                    # the expected
                    while len(series_data[j]) >= len(series_data[0]): j += 1
                    x = elem.text
                    if x is not None: x = x.strip()
                    if x is None or len(x) == 0:
                        x = __try_element(elem, "img", lambda x: x.get("alt"))
                    if x is None:
                        x = __try_element(elem, "a", lambda x: x.text)
                    if x is None:
                        divs = elem.findall("div")
                        assert len(divs) == 2
                        x = divs[0].find("img").get("alt")
                        x = __try_number(__normalize(x))
                        series_data[-1].append(x)
                        x = divs[1].text
                    # normalize x and copy it as many times as rowspan indicates
                    x = __try_number(__normalize(x))
                    span = elem.get("rowspan", 1)
                    for k in range(int(span)): series_data[j].append(x)
                except:
                    print "Unable to parse dom element:", traceback.format_exc()
                    logger.error("Unable to parse dom element: %s", traceback.format_exc())

        # Position 1 contains hour information, not needed, we use timestamps
        # located at position 0.
        series_names.pop(1)
        series_data.pop(1)
        series_names = [ __normalize(x) for x in series_names ]
        
        for i in range(1,len(series_names)):
            name = series_names[i]
            msg = {
                "timestamp" : time.time(),
                "values" : series_data[i],
                "period_first_times" : series_data[0],
                "period_last_times" : None
            }
            client.publish(forecast_topic.format(location_id, "hourly", name),
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
            if type(value) != str or len(value) > 0:
                msg = { "timestamp" : t, "data" : value }
                client.publish(weather_topic.format(location_id,name), json.dumps(msg))

    except:
        print "Unable to retrieve current weather status:", traceback.format_exc()
        logger.error("Unable to retrieve current weather status: %s", traceback.format_exc())

def start():
    """Opens logger connection and loads its configuration from MongoDB."""
    global logger
    logger = LoggerClient.open("AEMETMonitor")
    config = Utils.getconfig("aemet", logger)
    global location_id
    location_id = config["location_id"]
    global hourly_forecast_url
    hourly_forecast_url = config["hourly_forecast_url"]
    global current_weather_url
    current_weather_url = config["current_weather_url"]
    global tz
    tz = pytz.timezone(config["timezone"])

def stop():
    """Closes connection with logger."""
    logger.close()

def publish():
    try:
        client = Utils.getpahoclient(logger)
        __publish_daily_forecast(client)
        __publish_hourly_forecast(client)
        __publish_current_weather_status(client)
        client.disconnect()
        
    except:
        print "Unexpected error:", traceback.format_exc()
        logger.error("Unexpected error: %s", traceback.format_exc())

start()
publish()
