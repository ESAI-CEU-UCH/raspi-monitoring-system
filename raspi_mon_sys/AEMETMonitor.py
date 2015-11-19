#!/usr/bin/env python2.7
"""This module publishes current weather data from AEMET and future forecasts for
today and tomorrow.

This module is particularly different from other ones because its data is
published using two different topic roots. It publishes under
`raspimon/aemet/ID/NAME/#` current weather status, and under
`aemet/forecast/ID/HORIZON/NAME` where `ID` is the location identifier,
`NAME` is the particular data identifier (wind,
rain, temperature, min_temperature, max_temperature, etc.) and `HORIZON` is the
forecast horizon (hourly, two_days, week, etc.). Messages for `raspimon` are a
usual with two data fields `timestamp` and `data`. For `aemet/forecast` they are
more complex with the following fields:

- `timestamp`: when the data has been captured (it can be a time mark given by
  AEMET or given by us when downloading the data).

- `values`: a list of forecast parameters.

- `period_first_times`: a list of timestamps indicating period start times.

- `period_last_times`: a list of timestamps indicating period last times.

Valencia current weather data::

    Ind. climatologico: 8416Y -  Altitud (m): 11
    Latitude: 39 28' 50'' N - Longitude: 0 21' 59'' O

http://www.aemet.es/es/eltiempo/observacion/ultimosdatos?k=val&l=8416Y&w=0&datos=det&x=h24&f=temperatura

Valencia weather forecast data::

    Capital: Valencia (altitud: 16 m)
    Latitude: 39 28' 31'' N - Longitude: 0 22' 32' O
    Zona de avisos: Litoral norte de Valencia

http://www.aemet.es/es/eltiempo/prediccion/municipios/valencia-id46250

48 hours forecasts are not public in XML or CSV formats (or I'm unable to found
them). We need to rely in the web page: http://www.aemet.es/es/eltiempo/prediccion/municipios/horas/valencia-id46250
"""

# Copyright (C) 2015 Miguel Lorenzo, Francisco Zamora-Martinez
# Use of this source code is governed by the GPLv3 license found in the LICENSE file.

import csv
import json
import datetime
import time
import traceback
import urllib2

import raspi_mon_sys.aemet as aemet
import raspi_mon_sys.LoggerClient as LoggerClient
import raspi_mon_sys.Utils as Utils

logger = None
weather_topic  = Utils.gettopic("aemet/{0}")
forecast_topic = "aemet/forecast/{0}/{1}/{2}"
valencia_url = "http://www.aemet.es/es/eltiempo/observacion/ultimosdatos_8416Y_datos-horarios.csv?k=val&l=8416Y&datos=det&w=0&f=temperatura&x=h24"
#airport_url  = "http://www.aemet.es/es/eltiempo/observacion/ultimosdatos_8414A_datos-horarios.csv?k=val&l=8414A&datos=det&w=0&f=temperatura&x=h24"
valencia_forecast_id = "46250"
NUM_DAYS = 4

week_forecast_info = (
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

def __try_number(x):
    if type(x) is list:
        return [ __try_number(y) for y in x ]
    try:
        x_float = float(x)
        x_int = int(x)
        if x_float == x_int: return x_int
        return x_float
    except:
        return x

def __datestr2time(s):
    return time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d").timetuple())

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
    all_days = [ __try_number( func(getattr(day, method_name)()) ) for day in days_parsers ]
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
    aemet_parser = aemet.Localidad(valencia_forecast_id)
    
    # sanity check
    assert aemet_parser.get_localidad() == "Valencia"
    
    now = datetime.datetime.now()
    days = [ now + datetime.timedelta(i) for i in range(NUM_DAYS) ]
    days_parsers = [ aemet_parser.parse_datos_fecha(x) for x in days ]
    pre_messages = [ x for st in week_forecast_info for x in __process_daily_forecast(days_parsers, *st) ]
    when = __datestr2time( aemet_parser.get_fecha_actualizacion() )
        
    for msg in pre_messages:
        key = msg.pop("content_key")
        msg["timestamp"] = when
        client.publish(forecast_topic.format(valencia_forecast_id, "daily", key),
                       json.dumps(message))

def start():
    """Opens logger connection."""
    global logger
    logger = LoggerClient.open("ElectricityPricesMonitor")

def publish():
    try:
        client = Utils.getpahoclient(logger)
        __publish_daily_forecast(client)
        client.disconnect()
        
    except:
        print "Unexpected error:", traceback.format_exc()
        logger.error("Unexpected error: %s", traceback.format_exc())

start()
publish()


# client.on_connect = on_connect
# client.on_message = on_message
# client.connect("127.0.0.1", 1883, 60)

# #Configuracion de la conexion al sensor de temperatura DHT11
# sensor = Adafruit_DHT.DHT11
# pin = 4
# humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

# #configuracion del canal mqtt
# canalmqtt = 19

# url = 


# client.loop_start()
# last_min = time.time()
# temp_ext = None
# while True:
    
#     now = time.time()   # Current time as timestamp based on local time from the Pi. updated once per minute.
#     dif = now - last_min
#     humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    
    
#     if dif>3600 or temp_ext is None:  # only check programs once an hour or first time
#         last_min = now
#         response = urllib2.urlopen(url)
#         try:
#             reader = csv.reader(response)
#             listado = list(reader)
#             #print(listado[4][1])
#             temp_ext = listado[4][1]
#         except ValueError:
#             print "Oops!  That was no valid number.  Try again..."
#     if humidity is not None and temperature is not None:
#         client.publish("emonhub/rx/{0}/values".format(canalmqtt),"{0:.2f},{1},{2},1.5".format(temperature,temp_ext,humidity))
    
#     time.sleep(60)
