"""This module is an adataption of `AEMET-Python <https://github.com/aariste/AEMET-Python>`_.

The main purpose of this module is to load and parse data from AEMET daily
forecasts retrieved in XML format. It should be use as following example:

>>> import raspi_mon_sys.aemet as aemet
>>> parser = aemet.Localidad("46250")
>>> tomorrow = datetime.datetime.now() + datetime.timedelta(1)
>>> date_forecast = parser.parse_datos_fecha(tomorrow)
>>> date_forecast.get_temperatura_maxima()

Class `DatosFecha` is described here for documentation purposes but it should
never being instantiated from outside the module. You should use
`Localidad.parse_datos_fecha()` method to instance `DatosFecha` class.

"""

from xml.etree.ElementTree import parse
from urllib import urlopen

import datetime
import time

translations = {
        "-" : "-",
        "avisos" : "alerts",
        "c" : "C",
        "calma" : "C",
        "cielo" : "sky",
        "cielo_despejado" : "clear",
        "cubierto" : "covered",
        "cubierto_con_lluvia" : "covered_with_rain",
        "cubierto_con_lluvia_escasa" : "covered_with_little_rain",
        "cubierto_con_lluvia_escasa_noche" : "covered_with_little_rain_night",
        "cubierto_con_lluvia_noche" : "covered_with_rain_night",
        "cubierto_con_nieve" : "covered_with_snow",
        "cubierto_con_nieve_escasa" : "covered_with_little_snow",
        "cubierto_con_nieve_escasa_noche" : "covered_with_little_snow_night",
        "cubierto_con_nieve_noche" : "covered_with_snow_night",
        "cubierto_con_tormenta" : "covered_with_storm",
        "cubierto_con_tormenta_noche" : "covered_with_storm_night",
        "cubierto_con_tormenta_y_lluvia_escasa" : "covered_with_storm_and_little_rain",
        "cubierto_con_tormenta_y_lluvia_escasa_noche" : "covered_with_storm_and_little_rain_night",
        "cubierto_noche" : "covered_night",
        "despejado" : "clear",
        "despejado_noche" : "clear_night",
        "direccion_de_racha" : "wind_gust_direction",
        "direccion_del_viento" : "wind_direction",
        "direccion_viento" : "wind_direction",
        "e" : "E",
        "en_calma" : "-",
        "este" : "E",
        "fecha" : "date",
        "fecha_y_hora_oficial" : "official_datetime",
        "humedad" : "humidity",
        "humedad_relativa" : "humidity",
        "intervalos_nubosos" : "cloudy_intervals",
        "intervalos_nubosos_con_lluvia" : "cloudy_intervals_with_rain",
        "intervalos_nubosos_con_lluvia_escasa" : "cloudy_intervals_with_little_rain",
        "intervalos_nubosos_con_lluvia_escasa_noche" : "cloudy_intervals_with_little_rain_night",
        "intervalos_nubosos_con_lluvia_noche" : "cloudy_intervals_with_rain_night",
        "intervalos_nubosos_con_nieve" : "cloudy_intervals_with_snow",
        "intervalos_nubosos_con_nieve_escasa" : "cloudy_intervals_with_little_snow",
        "intervalos_nubosos_con_nieve_escasa_noche" : "cloudy_intervals_with_little_snow_night",
        "intervalos_nubosos_con_nieve_noche" : "cloudy_intervals_with_snow_night",
        "intervalos_nubosos_con_tormenta" : "cloudy_intervals_with_storm",
        "intervalos_nubosos_con_tormenta_noche" : "cloudy_intervals_with_storm_night",
        "intervalos_nubosos_con_tormenta_y_lluvia_escasa" : "cloudy_intervals_with_storm_and_little_rain",
        "intervalos_nubosos_con_tormenta_y_lluvia_escasa_noche" : "cloudy_intervals_with_storm_and_little_rain_night",
        "intervalos_nubosos_noche" : "cloudy_intervals_night",
        "ip" : "Ip", # It means inappreciable precipitation.
        "muy_cubierto_con_lluvia" : "very_covered_with_rain",
        "muy_cubierto_con_lluvia_escasa" : "very_covered_with_little_rain",
        "muy_cubierto_con_lluvia_escasa_noche" : "very_covered_with_little_rain_night",
        "muy_cubierto_con_lluvia_noche" : "very_covered_with_rain_night",
        "muy_cubierto_con_nieve" : "very_covered_with_snow",
        "muy_cubierto_con_nieve_escasa" : "very_covered_with_little_snow",
        "muy_cubierto_con_nieve_escasa_noche" : "very_covered_with_little_snow_night",
        "muy_cubierto_con_nieve_noche" : "very_covered_with_snow_night",
        "muy_nuboso" : "very_cloudy",
        "muy_nuboso_con_lluvia" : "very_cloudy_with_rain",
        "muy_nuboso_con_lluvia_escasa" : "very_cloudy_with_little_rain",
        "muy_nuboso_con_lluvia_escasa_noche" : "very_cloudy_with_little_rain_night",
        "muy_nuboso_con_lluvia_noche" : "very_cloudy_with_rain_night",
        "muy_nuboso_con_nieve" : "very_cloudy_with_snow",
        "muy_nuboso_con_nieve_escasa" : "very_cloudy_with_little_snow",
        "muy_nuboso_con_nieve_escasa_noche" : "very_cloudy_with_little_snow_night",
        "muy_nuboso_con_nieve_noche" : "very_cloudy_with_snow_night",
        "muy_nuboso_con_tormenta" : "very_cloudy_with_storm",
        "muy_nuboso_con_tormenta_noche" : "very_cloudy_with_storm_night",
        "muy_nuboso_con_tormenta_y_lluvia_escasa" : "very_cloudy_with_storm_and_little_rain",
        "muy_nuboso_con_tormenta_y_lluvia_escasa_noche" : "very_cloudy_with_storm_and_little_rain_night",
        "n" : "N",
        "ne" : "NE",
        "nieve" : "snow_mm",
        "no" : "NO",
        "nordeste" : "NE",
        "noroeste" : "NO",
        "norte" : "N",
        "nubes_altas" : "high_clouds",
        "nubes_altas_noche" : "high_clouds_night",
        "nuboso" : "cloudy",
        "nuboso_con_lluvia" : "cloudy_with_rain",
        "nuboso_con_lluvia_escasa" : "cloudy_with_little_rain",
        "nuboso_con_lluvia_escasa_noche" : "cloudy_with_little_rain_night",
        "nuboso_con_lluvia_noche" : "cloudy_with_rain_night",
        "nuboso_con_nieve" : "cloudy_with_snow",
        "nuboso_con_nieve_escasa" : "cloudy_with_little_snow",
        "nuboso_con_nieve_escasa_noche" : "cloudy_with_little_snow_night",
        "nuboso_con_nieve_noche" : "cloudy_with_snow_night",
        "nuboso_con_tormenta" : "cloudy_with_storm",
        "nuboso_con_tormenta_noche" : "cloudy_with_storm_night",
        "nuboso_con_tormenta_y_lluvia_escasa" : "cloudy_with_storm_and_little_rain",
        "nuboso_con_tormenta_y_lluvia_escasa_noche" : "cloudy_with_storm_and_little_rain_night",
        "nuboso_noche" : "cloudy_night",
        "o" : "O",
        "oeste" : "O",
        "poco_nuboso" : "little_cloudy",
        "poco_nuboso_noche" : "little_cloudy_night",
        "precipitacion" : "rain_mm",
        "presion" : "pressure",
        "prob._de_nieve" : "snow_prob",
        "prob._de_tormenta" : "storm_prob",
        "prob._precip." : "rain_prob",
        "racha" : "wind_gust",
        "racha_max." : "wind_gust",
        "riesgo" : "alert",
        "riesgo_extremo" : "extreme_alert",
        "riesgo_importante" : "important_alert",
        "s" : "S",
        "se" : "SE",
        "sen._termica" : "thermal_sens",
        "sin_riesgo" : "no_alert",
        "so" : "SO",
        "sudeste" : "SE",
        "sudoeste" : "SO",
        "sur" : "S",
        "temp." : "temperature",
        "temperatura" : "temperature",
        "tendencia" : "pressure_trend",
        "velocidad_del_viento" : "wind_speed",
        "viento" : "wind_speed",
}


class DatosFecha:
        def __init__(self, url, rss, fecha):
                self.rss = rss
		self.fecha = fecha
		self.__url = url
		self.__fecha_de_actualizacion = ''
		self.__localidad = ''
		self.__provincia = ''
		self.precipitacion = []
		self.cota_nieve = []
		self.estado_cielo = []
		self.viento = []
		self.racha = []
		self.temperatura_maxima = 0
		self.temperatura_minima = 0
		self.temperatura_horas = []
		self.sensacion_termica_maxima = 0
		self.sensacion_termica_minima = 0
		self.sensacion_termica = []
		self.humedad_maxima = 0
		self.humedad_minima = 0
		self.humedad = []
		self.uv_max = 0
		self.__load_datos_base()
		self.__load_datos(self.fecha)

	def __load_datos_base(self):
		self.__fecha_de_actualizacion = self.rss.find('elaborado').text.encode('UTF-8')
		self.__localidad = self.rss.find('nombre').text.encode('UTF-8')
		self.__provincia = self.rss.find('provincia').text.encode('UTF-8')

	'''Carga de los datos del XML para el dia seleccionado'''
	def __load_datos(self, fecha):
                def try_periodo(elem):
                        p = elem.get('periodo')
                        if p is None: return "00-24"
                        return p
                
		nodo = self.rss.find("prediccion/dia[@fecha='" + fecha + "']")

		'''Probabilidad de precipitacion'''
		for elem in nodo.findall('prob_precipitacion'):
			self.precipitacion.append([try_periodo(elem), elem.text])

		'''Cota de nieve'''
		for elem in nodo.findall('cota_nieve_prov'):
			self.cota_nieve.append([try_periodo(elem), elem.text])
		
		'''Estado'''
		for elem in nodo.findall('estado_cielo'):
			self.estado_cielo.append([try_periodo(elem), elem.get('descripcion')])

		'''Viento'''
		for elem in nodo.findall('viento'):
			self.viento.append([try_periodo(elem), elem.find('direccion').text, elem.find('velocidad').text])

		'''Racha maxima'''
		for elem in nodo.findall('racha_max'):
			self.racha.append([try_periodo(elem), elem.text])

		'''Temperaturas'''
                try:
                        self.temperatura_maxima = nodo.find('temperatura/maxima').text
                except:
                        pass
                try:
                        self.temperatura_minima = nodo.find('temperatura/minima').text
                except:
                        pass

		for elem in nodo.findall('temperatura/dato'):
			self.temperatura_horas.append([elem.get('hora'), elem.text])

		'''Sensacion termica'''
                try:
                        self.sensacion_termica_maxima = nodo.find('sens_termica/maxima').text
                except:
                        pass
                try:
                        self.sensacion_termica_minima = nodo.find('sens_termica/minima').text
                except:
                        pass

		for elem in nodo.findall('sens_termica/dato'):
			self.sensacion_termica.append([elem.get('hora'), elem.text])

		'''Humedad'''
                try:
                        self.humedad_maxima = nodo.find('humedad_relativa/maxima').text
                except:
                        pass
                try:
                        self.humedad_minima = nodo.find('humedad_relativa/minima').text
                except:
                        pass
                
		for elem in nodo.findall('humedad_relativa/dato'):
			self.humedad.append([elem.get('hora'), elem.text])

		'''U.V. Maximo'''
                try:
                        self.uv_max = nodo.find('uv_max').text
                except:
                        pass

	'''Interfaz publica'''
	def get_fecha_actualizacion(self):
		return self.__fecha_de_actualizacion

	def get_localidad(self):
		return self.__localidad

	def get_provincia(self):
		return self.__provincia

	def get_precipitacion(self):
		return self.precipitacion

	def get_cota_nieve(self):
		return self.cota_nieve

	def get_estado_cielo(self):
		return self.estado_cielo

	def get_viento(self):
		return self.viento

	def get_racha(self):
		return self.racha

	def get_temperatura_maxima(self):
		return self.temperatura_maxima

	def get_temperatura_minima(self):
		return self.temperatura_minima
		
	def get_temperatura_horas(self):
		return self.temperatura_horas

	def get_sensacion_termica_maxima(self):
		return self.sensacion_termica_maxima

	def get_sensacion_termica_minima(self):
		return self.sensacion_termica_minima

	def get_sensacion_termica(self):
		return self.sensacion_termica

	def get_humedad_maxima(self):
		return self.humedad_maxima

	def get_humedad_minima(self):
		return self.humedad_minima

	def get_humedad(self):
		return self.humedad

	def get_uv_max(self):
		return self.uv_max

class Localidad:

	'''Fecha en formato dd/mm/AAAA'''
	def __init__(self, codigo):
		self.__url = 'http://www.aemet.es/xml/municipios/localidad_' + codigo + '.xml'
		self.rss = parse(urlopen(self.__url)).getroot()
                self.__load_datos_base()

	def __load_datos_base(self):
		self.__fecha_de_actualizacion = self.rss.find('elaborado').text.encode('UTF-8')
		self.__localidad = self.rss.find('nombre').text.encode('UTF-8')
		self.__provincia = self.rss.find('provincia').text.encode('UTF-8')

	'''Interfaz publica'''

        def parse_datos_fecha(self, fecha):
                __fecha = time.strftime("%Y-%m-%d", fecha.timetuple())
                return DatosFecha(self.__url, self.rss, __fecha)

	def get_fecha_actualizacion(self):
		return self.__fecha_de_actualizacion

	def get_localidad(self):
		return self.__localidad

	def get_provincia(self):
		return self.__provincia

