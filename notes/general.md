# Ideas sobre servidor y raspberry pi

Estoy pensando la posibilidad de que el servidor identifique a la raspberry pi
utilizando la MAC de su tarjeta de red. Si tiene un wifi y una ethernet, me
decantaría por usar la MAC de la ethernet que sabemos que **siempre** va a estar
presente. De esta forma, el servidor tendría una base de datos en MongoDB
direccionada con el nombre `raspimon_MACSTRING` donde si la MAC del dispositivo
es `bc:ae:c5:71:22:fc`, entonces `MACSTRING=bcaec57122fc`, es decir, la
secuencia hexdecimal sin los dos puntos de separación que ponen muchas
aplicaciones a la hora de mostrar la MAC. El dispositivo debería mostrar un
error y enviar un correo electrónico informando de que ha habido un problema.

## Mensajes de error y avisos de la raspberry pi

Al hilo de lo anterior, se me ocurre que podemos implementar un módulo Python
que permita comunicarnos con nuestra cuenta de correo `esaiceuuch@gmail.com`.
Dicho servicio debería ser cargado y utilizado así:

```Python
import MailLogger
# El servicio abre un archivo con los credenciales de la cuenta de correo
# (en este caso credenciales para conectarse a GMail).
logger = MailLogger.open("/etc/mail_credentials")

# Deberiamos poder configurarlo para que nos envie mensajes instantaneos o bien
# resumenes diarios, semanales, mensuales, ... La configuracion aqui indicada
# seria la esperada por defecto?
logger.config(logger.levels.DEBUG, logger.schedule.SILENTLY)
logger.config(logger.levels.INFO, logger.schedule.DAILY)
logger.config(logger.levels.ALERT, logger.schedule.INSTANTANEOUSLY)
logger.config(logger.levels.WARNING, logger.schedule.INSTANTANEOUSLY)
logger.config(logger.levels.ERROR, logger.schedule.INSTANTANEOUSLY)

# Mensajes de aviso.
logger.debug("Un mensaje con trazas y demas.")
logger.info("Informacion de cualquier tipo.")
logger.warning("Cuidadin.")
logger.alert("Algo muy malo ha pasado.")
logger.error("Algo malo pero recuperable.")
```

# Descripción general

La idea es tener un sistema de monitorización que nos permita guardar en una
base de datos información más o menos heterogénea. La tabla principal de la BBDD
tendrá estos campos:

**Tabla readings**

- id: identificador del dispositivo (numérico entero).
- keyId: identificador del tipo de dato (numérico entero).
- value: identificador del valor asociado a ese dato (numérico entero).

Habrá una dos tablas auxiliares:

**Tabla devices**

- id: identificador del dispositivo.
- name: un nombre dado por nosotros, para localizarlo rápidamente.
- description: una descripción que nos permita introducir información sobre el
  dispositivo.
- vendor ID (tal cual sale en dmesg en Linux)
- product ID (tal cual sale en dmesg en Linux)
- *pyClass*: nos indicará que clase permite interactura con el dispositivo.
- *pyConf*: nos permitirá pasarle al constructor de la clase la información
  necesaria para construir un objeto que permita sincronizarnos con el
  dispositivo real. Puede ser un string Python que pueda cargarse mediante un
  `eval()`.

**Tabla keys**

- keyId: identificador del tipo de dato (numérico entero).
- unit: unidad de medida (string).
- description: una descripción textual.

En principio, la tabla **readings** puede llegar a ser enorme, debido a la
cantidad de datos que podemos muestrear en un día. Esto nos puede llevar usar
BBDD tipo [MongoDB](https://www.mongodb.org/). Habría relaciones entre las
tablas, cuya integridad no es verificable por MongoDB, pero a priori parece que
no son relaciones complicadas, con lo que esperamos poder meter lógica en el
servidor para verificar la integridad de las relaciones.

## Sistema de monitorización

Dicho sistema se configurará a través de la BBDD. Recibirá como parámetro un
espacio de nombres en mongo (namespace) y buscará allí las tablas indicadas.  La
aplicación permitirá recibir señales como *SIGHUP* para informar de que se ha
actualizado la base de datos. Esto nos permitirá añadir nuevos elementos *en
caliente*, simplemente actualizando la BBDD e informando al sistema de
monitorización. En cualquier caso, el sistema de monitorización verificará
cada **X** segundos el estado de la BBDD, y si hubieran cambiado las tablas,
volverá a cargar la descripción de los dispositivos en memoria.
