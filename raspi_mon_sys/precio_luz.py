#!/usr/bin/env python

# Copyright (C) 2015 Miguel Lorenzo
# Use of this source code is governed by the MIT license found in the LICENSE file.

#Recoje el precio de la luz en para el dia siguiente y lo publica mediante MQTT


from datetime import date, timedelta
import time
import datetime
import paho.mqtt.client as mqtt
import json
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
client.connect("192.168.2.103", 1883, 60)

#configuracion del canal mqtt
canalmqtt = 23   

client.loop_start()
last_min = time.time() #hora de la ultima lectura

while True:
    
    #defino la URL del origen de datos para el dia actual
    dt=datetime.date.today()
    url = 'http://www.esios.ree.es/Solicitar?fileName=PVPC_CURV_DD_{0}&fileType=txt&idioma=es'.format(dt.strftime("%Y%m%d"))
    
    #calculo cuanto hace que se ejecuto el script
    now = time.time()   #Hora actual de ejecucuion (actualiza cada minuto)
    dif = now - last_min #diferencia
    dia = None
    #creo el dictionary dia donde se almacenaran los datos
    
    if dif>3600 or dia is None:  # Solo actualiza una vez cada hora o al arrancar cuando no exite 'dia'
        last_min = now #actualizo la ultima hora de ejecucion
        response = urllib2.urlopen(url) #cargo los datos de la url
        dia = {}
        try:
            json_load = json.load(response) #cargo el JSON de la respuesta
            for res in json_load['PVPC']:
                precio = res[u'GEN'].replace(',','.') #convierto el precio a decimales con punto, no con coma como hace REE
                dia[res['Hora']] = float(precio) #genero los pares clave - valor y lso guardo en el diccionario
            
            #obtengo el minimo y el maximo para el dia
            h_mini = min(dia, key=dia.get) #hora minimia
            mini = dia[h_mini] #valor minimo
            h_maxi = max(dia, key=dia.get) #hora maxima
            maxi = dia[h_maxi] #valor maximo
            
            hora = datetime.datetime.now() #hora actual
            hora_sig = datetime.datetime.now() + timedelta(hours=1) #hora siguiente
            inter_actual = "{:02d}-{:02d}".format(hora.hour,hora_sig.hour) #intervalo horario actual formateado
            coste_actual = dia[inter_actual] #valor de la electricidad en la hora actual
            #envio los mensajes mqtt correspondientes a la hora actual
            #formato del mqtt: precio_actual,min,hora_min,max,hora_max
            
            client.publish("emonhub/rx/{0}/values".format(canalmqtt),"{0},{1},{2},{3},{4}".format(coste_actual/1000,mini/1000,h_mini,maxi/1000,h_maxi))
        except ValueError:
            print "Oops! fial"
        
    time.sleep(1800)
