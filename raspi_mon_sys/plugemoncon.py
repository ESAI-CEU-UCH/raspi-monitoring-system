#!/usr/bin/env python2.7

# Copyright (C) 2015 Miguel Lorenzo
# Use of this source code is governed by the MIT license found in the LICENSE file.

#Publica las lecturas de los diferentes Circles de plugwise mediante MQTT en un topic
#adecuado al emonhub para que se muestre en el emonCMS



import time
import paho.mqtt.client as mqtt
from plugwise import *
import plugwise.util


def on_connect(client, userdata, rc):
    #print("Connected with result code "+str(rc))
    client.subscribe("emonhub/#")

def on_message(client, userdata, msg):
	#print(msg.topic+" "+str(msg.payload))

#Configuracion de la conexion al broker MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("192.168.1.102", 1883, 60)

#Configuracion de la conexion con los plugwise
DEFAULT_SERIAL_PORT = "/dev/ttyUSB0" #Se define el puerto del usb
macs = [["000D6F00029C19F9",3],["000D6F0003562CBD",4]] #listado de macs de los circles que tenga que leer y su Id de nodo asiganda en el emon
device = DEFAULT_SERIAL_PORT
device = Stick(device)

client.loop_start()

while True:
    for mac in macs:
        c = Circle(mac[0], device)
        try:
            client.publish("emonhub/rx/{0}/values".format(mac[1]),"{0:.2f},{1}".format(c.get_power_usage(),c.get_info()['relay_state']))
            #time.sleep(1)
        except ValueError:
            client.publish("dev/errors/{0}".format(mac),"error")
    #client.loop(timeout=5)
    time.sleep(5)
