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
                    "desc": "CT Clip 1, EmonTXV3 num 1. Grid loads. Real power.",
                    "name": "ground_floor/circuits/grid_real_power",
                    "unit": "W",
                    "tolerance": 0.0005
                },
                {
                    "key": 3,
                    "desc": "CT Clip 1, EmonTXV3 num 1. Grid loads. Apparent power.",
                    "name": "ground_floor/circuits/grid_app_power",
                    "unit": "W",
                    "tolerance": 0.0005
                },
                {
                    "key": 4,
                    "desc": "CT Clip 2, EmonTXV3 num 1. Circuit 1 loads, 20A. Real power.",
                    "name": "ground_floor/circuits/circuit1_real_power",
                    "unit": "W",
                    "tolerance": 0.0005
                },
                {
                    "key": 5,
                    "desc": "CT Clip 2, EmonTXV3 num 1. Circuit 1 loads 20A. Apparent power.",
                    "name": "ground_floor/circuits/circuit1_app_power",
                    "unit": "W",
                    "tolerance": 0.0005
                },
                {
                    "key": 6,
                    "desc": "CT Clip 3, EmonTXV3 num 1. Circuit 2 loads 16A. Real power.",
                    "name": "ground_floor/circuits/circuit2_real_power",
                    "unit": "W",
                    "tolerance": 0.0005
                },
                {
                    "key": 7,
                    "desc": "CT Clip 3, EmonTXV3 num 1. Circuit 2 loads 16A. Apparent power.",
                    "name": "ground_floor/circuits/circuit2_app_power",
                    "unit": "W",
                    "tolerance": 0.0005
                },
                {
                    "key": 8,
                    "desc": "CT Clip 4, EmonTXV3 num 1. Circuit 3 loads 15A. Real power.",
                    "name": "ground_floor/circuits/circuit3_real_power",
                    "unit": "W",
                    "tolerance": 0.0005
                },
                {
                    "key": 9,
                    "desc": "CT Clip 4, EmonTXV3 num 1. Circuit 3 loads 15A. Apparent power.",
                    "name": "ground_floor/circuits/circuit3_app_power",
                    "unit": "W",
                    "tolerance": 0.0005
                },
                {
                    "key": 10,
                    "desc": "VRMS EmonTXV3 1",
                    "name": "ground_floor/circuits/vrms1",
                    "mul": 0.01,
                    "add": 0,
                    "unit": "V",
                    "tolerance": 0.0005
                }
            ],
            "19": [
                {
                    "key": 2,
                    "desc": "Temperature dining room measured with DHT22",
                    "name": "ground_floor/dining_room/temperature",
                    "unit": "ºC",
                    "mul": 0.1,
                    "tolerance": 0.01
                },
                {
                    "key": 4,
                    "desc": "Humidity dining room measured with DHT22",
                    "name": "ground_floor/dining_room/humidity",
                    "mul": 0.1,
                    "unit": "%",
                    "tolerance": 0.01
                },
                {
                    "key": 5,
                    "desc": "EmonTH battery level",
                    "name": "ground_floor/dining_room/emonth_battery_level",
                    "mul": 0.1,
                    "unit": "V",
                    "tolerance": 0.01,
                    "alert_below_threshold": 1.5
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
                "000D6F00004BFA7C",
                "000D6F00004BA14E",
                "000D6F00004BE7CD",
                "000D6F00004BF57F",
                "000D6F00004ECE05",
                "000D6F000043B5FB",
                "000D6F00004BE94C",
                "000D6F00004BE7CD",
                "000D6F00004698D2",
                "000D6F00004BFAD3",
                "000D6F0004B1EF92",
                "000D6F0004B1E853",
                "000D6F0004B1F028",
                "000D6F000043B9AA",
                "000D6F000043BA5B"
            ]
        },
        "circles": [
            {
                "mac": "000D6F0005671DC3",
                "desc": "Raspberry pi + router",
                "name": "ground_floor/dining_room/rpi",
                "unit": "W",
                "tolerance": 0.005
            },
            {
                "mac": "000D6F00004BFA7C",
                "desc": "Reverse osmosis water source",
                "name": "ground_floor/kitchen/water_source",
                "unit": "W",
                "tolerance": 0.005
            },
            {
                "mac": "000D6F00004BA14E",
                "desc": "Washing machine",
                "name": "ground_floor/kitchen/washer",
                "unit": "W",
                "tolerance": 0.005
            },
            {
                "mac": "000D6F00004BE7CD",
                "desc": "Heater (oil version) + vacuum cleaner (few times) at dining room",
                "name": "ground_floor/dining_room/heater",
                "unit": "W",
                "tolerance": 0.005
            },
            {
                "mac": "000D6F00004BF57F",
                "desc": "Dressing room: heater (air version) + vacuum cleaner (few times)",
                "name": "second_floor/dressing_room/heater",
                "unit": "W",
                "tolerance": 0.005
            },
            {
                "mac": "000D6F00004ECE05",
                "desc": "Two computers: iMac + PC + screen + speakers. Reading lamp. Sometimes iPad charger, Mac Book Air charger, mobile phone charger. At largest room 3.",
                "name": "second_floor/room3/electronics",
                "unit": "W",
                "tolerance": 0.005
            },
            {
                "mac": "000D6F000043B5FB",
                "desc": "Heater (oil version) at largest room 3.",
                "name": "second_floor/room3/heater",
                "unit": "W",
                "tolerance": 0.005
            },
            {
                "mac": "000D6F00004BE94C",
                "desc": "Microwave oven",
                "name": "ground_floor/kitchen/microwave",
                "unit": "W",
                "tolerance": 0.005
            },
            {
                "mac": "000D6F000043B9AA",
                "desc": "Instruments room, small room 1: electronic piano + fan (few times in summer) + heater (few times in winter) + amplified speakers + mixing table",
                "name": "first_floor/room1/electronics",
                "unit": "W",
                "tolerance": 0.005
            },
            {
                "mac": "000D6F00004698D2",
                "desc": "Fridge 1 (larger one)",
                "name": "ground_floor/kitchen/fridge1",
                "unit": "W",
                "tolerance": 0.005
            },
            {
                "mac": "000D6F00004BFAD3",
                "desc": "Fridge 2 (smaller one)",
                "name": "ground_floor/kitchen/fridge2",
                "unit": "W",
                "tolerance": 0.005
            },
            {
                "mac": "000D6F0004B1EF92",
                "desc": "Electric oven",
                "name": "ground_floor/kitchen/oven",
                "unit": "W",
                "tolerance": 0.005
            },
            {
                "mac": "000D6F0004B1E853",
                "desc": "Water heater + toaster + juice maker + vacuum cleaner (few times)",
                "name": "ground_floor/kitchen/outlets",
                "unit": "W",
                "tolerance": 0.005
            },
            {
                "mac": "000D6F0004B1F028",
                "desc": "TV + multimedia computer + amplifier",
                "name": "ground_floor/dining_room/multimedia",
                "unit": "W",
                "tolerance": 0.005
            },
            {
                "mac": "000D6F000043BA5B",
                "desc": "alarm clock + iPad charger + Mac Book Air charger + other outlets",
                "name": "second_floor/room3/outlets",
                "unit": "W",
                "tolerance": 0.005
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
        "location_id" : "46250"
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
        "retention_policy" : "7d",
        "timezone" : "Europe/Madrid"
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
                        "args": [ "60s", "$this.write_data" ]
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
                        "args": [ "8s", "$this.publish" ]
                    }
                ]
            }
        ]
    });
}
print("Ok")
