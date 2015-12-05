var db = db.getSiblingDB('raspimon');

var house = "MALVA";
var raspi_mac = "74da38545ebd";
var plugwise_stick = "000D6F000452459C";

print("Populating 'raspimon' database for house " + house + " and raspi " + raspi_mac);

var cursor = db.GVA2015_houses.find({ "name":house });
if (cursor.count() == 0) {
    print("Inserting at GVA2015_houses collection");
    db.GVA2015_houses.insert({
        "start_date": ISODate("2015-12-05T00:00:00.000Z"),
        "name": house,
        "location": "Malvarrosa house, C/ San Rafael, 1",
        "raspi": raspi_mac,
        "older_raspis": ["b827eb7c62d8"],
        "description": "None",
        "stop_date": null
    });
}

cursor = db.GVA2015_config.find({ "source":"open_energy_monitor", "house":house });
if (cursor.count() == 0) {
    print("Inserting at GVA2015_config collection open_energy_monitor document");
    db.GVA2015_config.insert({
        "source": "open_energy_monitor",
        "house": house,
        "raspi": raspi_mac,
        "nodes": [
            {
                "id": 10,
                "desc": "EmonTXV3 1",
                "name": "emontx1"
            },
            {
                "id": 19,
                "desc": "EmonTH 1",
                "name": "emonth1"
            }
        ],
        "node2keys": {
            "10": [
                {
                    "key": 2,
                    "desc": "CT Clip 1, EmonTXV3 1, telephone power consumption",
                    "name": "telephone",
                    "unit": "W",
                    "tolerance" : 0.0005
                },
                {
                    "key": 6,
                    "desc": "VRMS EmonTXV3 1",
                    "name": "vrms1",
                    "mul": 0.01,
                    "add": 0,
                    "unit": "V",
                    "tolerance" : 0.0005
                }
            ],
            "19": [
                {
                    "key": 2,
                    "desc": "DHT22 Temperature 1",
                    "name": "in_temperature1",
                    "unit": "ºC",
                    "mul": 0.1,
                    "tolerance" : 0.01
                },
                {
                    "key": 4,
                    "desc": "DHT22 Humidity 1",
                    "name": "in_humidity1",
                    "mul": 0.1,
                    "unit": "%",
                    "tolerance" : 0.01
                },
                {
                    "key": 5,
                    "desc": "Battery voltage EmonTH 1",
                    "name": "emonth1_battery_voltage",
                    "mul": 0.1,
                    "unit": "V",
                    "tolerance" : 0.01,
                    "alert_below_threshold" : 1.5
                }
            ]
        }
    });
}

cursor = db.GVA2015_config.find({ "house":house, "source":"plugwise" });
if (cursor.count() == 0) {
    print("Inserting at GVA2015_config collection plugwise document")
    db.GVA2015_config.insert({
        "source": "plugwise",
        "house": house,
        "stick": plugwise_stick,
        "raspi": raspi_mac,
        "pairing": {
            "000D6F0005671DC3": [
                "000D6F00004BFA7C"
            ]
        },
        "circles": [
            {
                "mac": "000D6F0005671DC3",
                "desc": "Telephone D361 IMF",
                "name": "telephone",
                "unit": "W",
                "tolerance" : 0.005
            },
            {
                "mac": "000D6F00004BFA7C",
                "desc": "Raspberry pi " + raspi_mac,
                "name": "raspi",
                "unit": "W",
                "tolerance" : 0.005
            }
        ]
    });
}

cursor = db.GVA2015_config.find({ "source":"aemet", "house":house });
if (cursor.count() == 0) {
    print("Inserting at GVA2015_config collection aemet document");
    db.GVA2015_config.insert({
        "source": "aemet",
        "house": house,
        "raspi": raspi_mac,
        "current_weather_url" : "http://www.aemet.es/es/eltiempo/observacion/ultimosdatos_8416Y_datos-horarios.csv?k=val&l=8416Y&datos=det&w=0&f=temperatura&x=h24",
        "hourly_forecast_url" : "http://www.aemet.es/es/eltiempo/prediccion/municipios/horas/tabla/valencia-id46250",
        "location_id" : "46250",
        "timezone" : "Europe/Madrid"
    });
}

cursor = db.GVA2015_config.find({ "source":"influxdb", "house":house });
if (cursor.count() == 0) {
    print("Inserting at GVA2015_config collection influxdb document");
    db.GVA2015_config.insert({
        "source": "influxdb",
        "house": house,
        "raspi": raspi_mac,
        "host": "localhost",
        "port": 8086,
        "user": "root",
        "password": "root",
        "database": "raspimon",
        "retention_policy" : "7d"
    });
}

cursor = db.GVA2015_config.find({ "source":"main", "house":house });
if (cursor.count() == 0) {
    print("Inserting at GVA2015_config collection main document");
    db.GVA2015_config.insert({
        "_id": ObjectID("565d7524a5aad3ec293e2d07"),
        "source": "main",
        "house": house,
        "raspi": raspi_mac,
        "modules": [
            {
                "import": "raspi_mon_sys.MongoDBHub",
                "schedules": [
                    {
                        "method": "repeat_o_clock_with_offset",
                        "args": [ "1h", "0.08h", "$this.upload_data" ]
                    }
                ]
            },
            {
                "import": "raspi_mon_sys.InfluxDBHub",
                "schedules": [
                    {
                        "method": "repeat_o_clock",
                        "args": [ "10s", "$this.write_data" ]
                    }
                ]
            },
            {
                "import": "raspi_mon_sys.AEMETMonitor",
                "schedules": [
                    {
                        "method": "repeat_o_clock",
                        "args": [ "1h", "$this.publish" ]
                    }
                ]
            },
            {
                "import": "raspi_mon_sys.CheckIP",
                "schedules": [
                    {
                        "method": "repeat_o_clock",
                        "args": [ "5m", "$this.publish" ]
                    }
                ]
            },
            {
                "import": "raspi_mon_sys.ElectricityPricesMonitor",
                "schedules": [
                    {
                        "method": "repeat_o_clock_with_offset",
                        "args": [ "1d", "21h", "$this.publish", 1 ]
                    }
                ]
            },
            {
                "import": "raspi_mon_sys.OpenEnergyMonitor"
            },
            {
                "import": "raspi_mon_sys.PlugwiseMonitor",
                "schedules": [
                    {
                        "method": "repeat_o_clock",
                        "args": [ "10s", "$this.publish" ]
                    }
                ]
            }
        ]
    });
}
print("Ok")
