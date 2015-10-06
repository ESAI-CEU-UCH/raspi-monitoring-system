#!/usr/bin/env python

# Copyright (C) 2015 Miguel Lorenzo
# Use of this source code is governed by the MIT license found in the LICENSE file.

#Publica las lecturas de temperatura del DHT11 y de AEMET mediante MQTT en un topic
#adecuado al emonhub para que se muestre en el emonCMS



import time
import paho.mqtt.client as mqtt
import Adafruit_DHT
import csv
import urllib2

def on_connect(client, userdata, rc):
    #print("Connected with result code "+str(rc))
    client.subscribe("emonhub/tx")

def on_message(client, userdata, msg):
	print(msg.topic+" "+str(msg.payload))

#Configuracion de la conexion al broker MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("127.0.0.1", 1883, 60)

#Configuracion de la conexion al sensor de temperatura DHT11
sensor = Adafruit_DHT.DHT11
pin = 4
humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

#configuracion del canal mqtt
canalmqtt = 19

url = 'http://www.aemet.es/es/eltiempo/observacion/ultimosdatos_8414A_datos-horarios.csv?k=val&l=8414A&datos=det&w=0&f=temperatura&x='


client.loop_start()
last_min = time.time()
temp_ext = None
while True:
    
    now = time.time()   # Current time as timestamp based on local time from the Pi. updated once per minute.
    dif = now - last_min
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    
    
    if dif>3600 or temp_ext is None:  # only check programs once an hour or first time
        last_min = now
        response = urllib2.urlopen(url)
        try:
            reader = csv.reader(response)
            listado = list(reader)
            #print(listado[4][1])
            temp_ext = listado[4][1]
        except ValueError:
            print "Oops!  That was no valid number.  Try again..."
    if humidity is not None and temperature is not None:
        client.publish("emonhub/rx/{0}/values".format(canalmqtt),"{0:.2f},{1},{2},1.5".format(temperature,temp_ext,humidity))
    
    time.sleep(60)
