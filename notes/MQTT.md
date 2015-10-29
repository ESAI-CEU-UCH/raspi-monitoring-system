# MQTT

Miguel, investiga un poco sobre el protocolo, y describelo aquí. Me
gustaría poder muestrear de la predicción del tiempo y de la
temperatura actual a través de servicios web oficiales de España. Esos
servicios no estarían dentro del protocolo, pero necesitaríamos un
wrapper para emitir los mensajes de la manera adecuada. Cuando te
hayas mirado esto, escribe aquí una descripción, con referencias, del
protocolo, de manera que luego puedas usar ese texto para ponerlo en
la memoria del proyecto.

El protocolo MQTT es un estandar abierto que permite la comunicacion entre diferentes clientes sobre TCP/IP utilizando muy pocos recursos, tanto de red como de procesamiento. 
Esta diseñado para su utilizacion en IoT y comunicaciones M2M.
Diseñado en 1999, es una evolucion de protocolso de comunicacion SCADA & MQIsdp
Los puertos reservados IANA son 1883 para conexiones estandar y 8883 para la utilizacion de MQTT sobre SSL
Permite conexiones de 10000 clientes o mas en algunos casos.
Es un protocolo que utiliza una topologia en estrella en el que un servidor central (BROKER) es el encargado de recibir los mensajes y distribuirlos a sus destinatarios.
El sistema se basa en publicaciones y subscripciones a canales con un formato jerarquico "canal/tema/subtema/..." por lo tanto un nodo publica su mensaje en el tema oportuno y los nodos subscriptores de ese canal lo recibiran.

La subscripcion a un canal permite el uso de wildcards (comodines) 
El uso de # ("canal/tema/#) subscribira al cliente a todos los mensajes que se emitan para "canal/tema/...."
El uso de + permite sustituir solo un directorio "/canal/+/subtema1" permtira al cliente suscribirse a /canal/tema1/subtema1  y canal/tema2/subtema1 etc..

Utilizando este sistema de publicacion y subscripcion se permite la cominicacion 1 a 1 , 1 a muchos y muchos a 1.

Permite definir 3 niveles de QoS 
- 0 At most once delivery El mensaje llega al receptor 1 o ninguna veces
- 1 At least once delivery Asegura que el mensaje llega al receptor al menos una vez 
- 2 Exactly once delivery

Permite definir un mensaje especial "Last Will and Testament" que se emitira en caso de desconexion irregular del cliente
Persistencia, MQTT permite que el Broker almacene solamente el ultimo mensaje bueno recibidoy que al suscribirse un cliente este lo reciba al conectarse.

MQTT permite solicitar usuario y contraseña para realizar la conexion al broker
para realizar la conexion segura los mensajes deben ser cifrados usando TLS o algun otro metodo
SHOULD use TCP port 8883 (IANA service name: secure-mqtt).

Al realizar el cliente la conexion hacia el broker y mantenerla abierta a lo largo de las sesion mediente PINGREQ y PINGRESP facilita su funcionamiento a traves de Firewalls
solo el broker tiene que estar accesible desde el exterior.

Referencias:
http://mqtt.org/
http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html

 

