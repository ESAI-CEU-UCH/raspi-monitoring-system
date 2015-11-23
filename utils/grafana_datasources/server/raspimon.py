#!/usr/bin/env python2.7
"""The purpose of this module is to offer a basic API for MongoDB server using
the schema defined in the project. It should be executed at same host as MongoDB
server. This module communicates with MongoDB using pymongo and implements
facilities to obtain time-series from data storage. Currently it offers a basic
API with following commands:

- `/raspimon/api/topics` returns a JSON array with all available topics.
- `/raspimon/api/aggregators` returns a JSON array with all available aggregators.
- `/raspimon/api/aggregate/<agg>/<topic>/<from>/<to>/<max>` returns a JSON array
  with the time-series aggregation for given `<topic>` name in the time interval
  `<from>-<to>` given as timestamps. The size of the returned array will be at
  most `<max>`.

"""
import datetime
import json
import pymongo
import time

from flask import Flask

app = Flask(__name__)

MONGO_HOST = "localhost"
MONGO_PORT = 27018

mapfn = """function() {{
    period = {0};
    b = this.basetime;
    for(i=0; i<this.values.length; ++i) {{
        secs = b.getTime()/1000.0 + this.delta_times[i];
        key  = Math.floor( secs / period ) * period;
        emit(key, {{ secs: secs, value: this.values[i] }});
    }}
}}"""

take_one_reducefn = """function(key,values) {{
    values.sort(function(a,b) {{ return a.secs < b.secs; }});
    return {{ secs:values[{0}].secs, value: values[{0}].value }};
}}"""

avg_reducefn = """function(key,values) {{
    values.sort(function(a,b) {{ return a.secs < b.secs; }});
    sum = values[0].value;
    t = 0.0;
    for(i=1; i<values.length; ++i) {{
        dt    = values[i].secs - values[i-1].secs;
        value = 0.5*values[i].value + 0.5*values[i-1].value;
        sum  += value * dt;
        t    += dt;
    }}
    return {{ secs: values[0].secs + t*0.5, value: sum/t }};
}}"""

sum_reducefn = """function(key,values) {{
    values.sort(function(a,b) {{ return a.secs < b.secs; }});
    sum = values[0].value;
    t = 0.0;
    for(i=1; i<values.length; ++i) {{
        dt    = values[i].secs - values[i-1].secs;
        value = 0.5*values[i].value + 0.5*values[i-1].value;
        sum  += value * dt;
        t    += dt;
    }}
    return {{ secs: values[0].secs + t*0.5, value: sum }};
}}"""

generic_math_reducefn = """function(key,values) {{
    values.sort(function(a,b) {{ return a.secs < b.secs; }});
    result = values[0].value;
    t = 0.0;
    for(i=1; i<values.length; ++i) {{
        secs   = values[i].secs;
        value  = values[i].value;
        dt     = secs - values[i-1].secs;
        result = Math.{0}(result, value);
        t     += dt;
    }}
    return {{ secs: values[0].secs + t*0.5, value: result }};
}}"""

reduce_operators = {
    "first" : [ take_one_reducefn, 0 ],
    "last" : [ take_one_reducefn, "values.length-1" ],
    "sum" : [ sum_reducefn ],
    "avg" : [ avg_reducefn ],
    "min" : [ generic_math_reducefn, "min" ],
    "max" : [ generic_math_reducefn, "max" ]
}

def build_mapfn(step): return mapfn.format(step)

def build_reducefn(agg):
    func = reduce_operators[agg][0]
    params = reduce_operators[agg][1:]
    return func.format(*params)

def connect():
    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    db = client["raspimon"]
    collection = db["GVA2015_data"]
    return (client,collection)

def transform_to_time_series(data):
    if len(data) == 0: return []
    if len(data) == 1: return [ [data[0]["value"]["value"],data[0]["value"]["secs"]] ]
    result = []
    for pair in data:
        p   = pair["value"]
        k,v = p["secs"],p["value"]
        result.append([v,k])
    return result

def get_topics():
    client,col = connect()
    topics = col.distinct("topic")
    client.close()
    return topics

def mapreduce_query(topic, start, stop, max_data_points, agg):
    client,col = connect()
    query = {
        "topic" : topic,
        "basetime" : { "$gte" : datetime.datetime.utcfromtimestamp(start),
                       "$lte" : datetime.datetime.utcfromtimestamp(stop) }
    }
    step = (stop - start) / max_data_points;
    query_mapfn = build_mapfn(step)
    query_reducefn = build_reducefn(agg)
    data = col.inline_map_reduce(query_mapfn,
                                 query_reducefn,
                                 full_response=False,
                                 query=query,
                                 sort={"topic":1,"basetime":1})
    client.close()
    #data.sort(key=lambda x: x["_id"])
    result = transform_to_time_series(data)
    return result

@app.route("/raspimon/api/topics")
def http_get_topics():
    return json.dumps( get_topics() )

@app.route("/raspimon/api/aggregators")
def http_get_aggregators():
    return json.dumps( reduce_operators.keys() );

# http://localhost:5000/raspimon/api/aggregate/last/raspimon:b827eb7c62d8:rfemon:10:6:vrms1:value/0/1448193433/100

@app.route('/raspimon/api/aggregate/<string:agg>/<string:topic>/<int:start>/<int:stop>/<int:max_data_points>')
def http_get_aggregation_query(agg, topic, start, stop, max_data_points):
    return json.dumps( mapreduce_query(topic, start, stop, max_data_points, agg) )

if __name__ == "__main__":
    app.debug = True
    app.run()
