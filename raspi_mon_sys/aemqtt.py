#!/usr/bin/env python2.7
# Copyright (C) 2015 Miguel Lorenzo
# Use of this source code is governed by the MIT license found in the LICENSE file.

#recoge la prediccion de temperatura de AEMET para los proximos 7 dias y la publica mediante MQTT


import Aemet
import time
import paho.mqtt.client as paho

def on_connect(pahoClient, obj, rc):
# Once connected, publish message
        print "Connected Code = %d"%(rc)
        client.publish("casa/prediccion/{0}/temperatura/max".format(tiempo.get_localidad()), tiempo.get_temperatura_maxima(), 0)
        client.publish("casa/prediccion/{0}/temperatura/min".format(tiempo.get_localidad()), tiempo.get_temperatura_minima(), 0)
        




host="192.168.1.104"
port=1883

dia = time.strftime("%d/%m/%Y")
localidad = "46190"
tiempo = Aemet.Localidad(localidad, dia)

#print 'Localidad: ', tiempo.get_localidad()
#print 'Temp. max:', tiempo.get_temperatura_maxima()
#print 'Temp. min:', tiempo.get_temperatura_minima()

client=paho.Client()
client.connect(host, port, 60)
client.loop_start()

while True:
    try:
        client.publish("casa/prediccion/{0}/{1}/temperatura/max".format(tiempo.get_localidad(),time.strftime("%d-%m-%Y")), tiempo.get_temperatura_maxima(), 0)
        client.publish("casa/prediccion/{0}/{1}/temperatura/min".format(tiempo.get_localidad(),time.strftime("%d-%m-%Y")), tiempo.get_temperatura_minima(), 0)
        for datohora in tiempo.get_temperatura_horas():
            client.publish("casa/prediccion/{0}/{1}/temperatura/hora/{2}".format(tiempo.get_localidad(),time.strftime("%d-%m-%Y"),datohora[0]),datohora[1], 0)

    except ValueError:
        client.publish("casa/{0}".format(mac),"error")
    time.sleep(3600)
