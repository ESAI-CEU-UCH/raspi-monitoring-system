var db = db.getSiblingDB('raspimon');

var house = "D361";
var raspi_mac = "b827eb7c62d8";
var plugwise_stick = "000D6F000452459C";

print("Populating 'raspimon' database for house " + house + " and raspi " + raspi_mac);

var cursor = db.GVA2015_houses.find({ "name":house });
if (cursor.count() == 0) {
    print("Inserting at GVA2015_houses collection")
    db.GVA2015_houses.insert({
        "start_date": Timestamp(1447343054, 0),
        "name": house,
        "location": "Despacho 361 for debug purposes",
        "mac": raspi_mac,
        "older_macs": [],
        "description": "None",
        "stop_date": null
    });
}

cusor = db.GVA2015_config.find({ "source":"open_energy_monitor", "house":house });
if (cursor.count() == 0) {
    print("Inserting at GVA2015_config collection open_energy_monitor document")
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
                    "unit": "W"
                },
                {
                    "key": 6,
                    "desc": "VRMS EmonTXV3 1",
                    "name": "vrms1",
                    "mul": 0.01,
                    "add": 0,
                    "unit": "V"
                }
            ],
            "19": [
                {
                    "key": 2,
                    "desc": "DHT22 Temperature 1",
                    "name": "in_temperature1",
                    "unit": "ºC",
                    "mul": 0.1
                },
                {
                    "key": 4,
                    "desc": "DHT22 Humidity 1",
                    "name": "in_humidity1",
                    "mul": 0.1,
                    "unit": "%"
                },
                {
                    "key": 5,
                    "desc": "Battery voltage EmonTH 1",
                    "name": "emonth1_battery_voltage",
                    "mul": 0.1,
                    "unit": "V"
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
                "unit": "W"
            },
            {
                "mac": "000D6F00004BFA7C",
                "desc": "Raspberry pi " + raspi_mac,
                "name": "raspi",
                "unit": "W"
            }
        ]
    });
}

print("Ok")
