#!/usr/bin/env python2.7
"""The purpose of this module is to offer a basic API for MongoDB server. It
should be executed at same host as MongoDB server. This module communicates with
MongoDB using pymongo and implements facilities to obtain time-series from data
storage. Currently it offers a basic API with following commands:

- `/raspimon/topics` returns a JSON array with all available topics.
- `/raspimon/query/<topic>/<from>/<to>/<max>` returns a JSON array with the
  time-series for given `<topic>` name in the time interval `<from>-<to>` given
  as timestamps. The size of the returned array will be at most `<max>`.

"""
import datetime
import json
import pymongo
import time

from flask import Flask

app = Flask("Raspimon Grafana Datasource API")

MONGO_HOST = "localhost"
MONGO_PORT = 27018

mapfn = """function() {
    b = this.basetime;
    for(i=0; i<this.values.length; ++i) {
        emit(new Date(b.getTime()+this.delta_times[i]*1000.0), this.values[i]);
    }
}"""

reducefn = """function(key,values) {
    return values[0];
}"""

def connect():
    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    db = client["raspimon"]
    collection = db["GVA2015_data"]
    return (client,collection)

def take_n_points_and_convert_to_series(data, max_data_points):
    # take at most max_data_points, so we take one data point for each time step
    # as computed below
    step = (data[-1]["_id"] - data[0]["_id"]) / max_data_points
    next_time = data[0]["_id"]
    result = []
    for pair in data:
        dt,y = pair["_id"],pair["value"]
        if dt >= next_time:
            x = time.mktime(dt.utctimetuple())
            result.append([y,x])
            next_time += step
    return result

@app.route("/raspimon/api/topics")
def topics():
    client,col = connect()
    topics = col.distinct("topic")
    client.close()
    return json.dumps(topics)

# http://localhost:5000/raspimon/api/query/raspimon:b827eb7c62d8:rfemon:10:6:vrms1:value/0/1448193433/100

@app.route('/raspimon/api/query/<string:topic>/<int:start>/<int:stop>/<int:max_data_points>')
def query(topic, start, stop, max_data_points):
    client,col = connect()
    query = {
        "topic" : topic,
        "basetime" : { "$gte" : datetime.datetime.utcfromtimestamp(start),
                       "$lte" : datetime.datetime.utcfromtimestamp(stop) }
    }
    data = col.inline_map_reduce(mapfn, reducefn,
                                 full_response=False, query=query)
    data.sort()
    result = take_n_points_and_convert_to_series(data, max_data_points)
    return json.dumps(result)

if __name__ == "__main__":
    app.debug = True
    app.run()
