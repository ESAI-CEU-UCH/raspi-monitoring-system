#!/usr/bin/env python2.7
"""This is a bit more complicated module, similar to raspimon.py but allowing to
incorporate complex statistics using numpy and pandas.
"""
import datetime
import json
import logging
import numpy as np
import pandas as pd
import pymongo
import time

from pandas import Series

from flask import Flask, request
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

IN_DEBUG=True
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
    values.sort(function(a,b) {{ return a.secs - b.secs; }});
    return {{ secs:values[{0}].secs, value: values[{0}].value }};
}}"""

avg_reducefn = """function(key,values) {{
    values.sort(function(a,b) {{ return a.secs - b.secs; }});
    sum = 0.0;
    t = 0.0;
    for(i=1; i<values.length; ++i) {{
        dt = values[i].secs - values[i-1].secs;
        if (dt > 0.0) {{
            value = 0.5*values[i].value + 0.5*values[i-1].value;
            sum  += value * dt;
            t    += dt;
        }}
    }}
    if (t < 1.0) t = 1.0;
    if (sum == 0.0) sum = values[0].value;
    return {{ secs: 0.5*values[0].secs + 0.5*values[values.length-1].secs, value: sum/t }};
}}"""

sum_reducefn = """function(key,values) {{
    values.sort(function(a,b) {{ return a.secs - b.secs; }});
    sum = 0.0;
    t = 0.0;
    for(i=1; i<values.length; ++i) {{
        dt = values[i].secs - values[i-1].secs;
        if (dt > 0.0) {{
            value = 0.5*values[i].value + 0.5*values[i-1].value;
            sum  += value * dt;
            t    += dt;
        }}
    }}
    if (t < 1.0) t = 1.0;
    if (sum == 0.0) sum = values[0].value;
    return {{ secs: values[values.length-1].secs, value: sum }};
}}"""

generic_math_reducefn = """function(key,values) {{
    values.sort(function(a,b) {{ return a.secs - b.secs; }});
    result = values[0].value;
    t = 0.0;
    for(i=1; i<values.length; ++i) {{
        secs   = values[i].secs;
        value  = values[i].value;
        dt     = secs - values[i-1].secs;
        result = Math.{0}(result, value);
        t     += dt;
    }}
    if (t < 1.0) t = 1.0;
    return {{ secs: values[0].secs + t*0.5, value: result }};
}}"""

reduce_operators = {
    "first" : [ take_one_reducefn, 0 ],
    "last" : [ take_one_reducefn, "values.length-1" ],
    #"sum" : [ sum_reducefn ],
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
    if len(data) == 0: return Series(np.array([]))
    if len(data) == 1:
        idx = np.array([ data[0]["value"]["secs"] ])
        ts = np.array([ [data[0]["value"]["value"]] ])
        return Series(ts, index=idx)
    idx = []
    ts = []
    for pair in data:
        p = pair["value"]
        idx.append( p["secs"] )
        ts.append( p["value"] )
    return Series(np.array(ts), index=np.array(idx))

def get_topics(filters=None):
    client,col = connect()
    if False:
        # This code is not working, pymongo Collection.distinct don't accepts a
        # query as argument :'(
        if filters is None or type(filters) is not list or len(filters) == 0:
            topics = col.distinct("topic")
        else:
            query  = { "$or" : [ {"topic":{"$regex":".*"+x+".*"}} for x in filters ] }
            topics = col.distinct("topic", query)
    else:
        # so we perform selection of topics using a Python filter
        topics = col.distinct("topic")
        if filters is not None and type(filters) is list and len(filters) > 0:
            topics = [ x for x in topics if any([x.find(y)!=-1 for y in filters]) ]
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
    if step < 1.0: step = 1.0;
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

def series(start, stop, max_data_points, topics_agg):
    series = [ mapreduce_query(top, start, stop, max_data_points, agg) for top,agg in topics_agg ]
    return pd.concat(series, axis=1)

def to_grafana_time_series(s):
    values = s.values
    if len(values.shape) == 1: values = list( values )
    else: values = list( values[:,0] )
    time = list( s.index )
    result = [ [v,k] for v,k in zip(values,time) ]
    return result

@app.route("/raspimon/api/topics")
def http_get_topics():
    return json.dumps( get_topics() )

@app.route("/raspimon/api/topics/filtered", methods=["POST"])
def http_post_topics_filtered():
    filters = request.get_json(force=True)
    return json.dumps( get_topics(filters) )

@app.route("/raspimon/api/aggregators")
def http_get_aggregators():
    return json.dumps( reduce_operators.keys() );

# http://localhost:5000/raspimon/api/aggregate/last/raspimon:b827eb7c62d8:rfemon:10:6:vrms1:value/0/1448193433/100

@app.route('/raspimon/api/aggregate/<string:agg>/<string:topic>/<int:start>/<int:stop>/<int:max_data_points>')
def http_get_aggregation_query(agg, topic, start, stop, max_data_points):
    return json.dumps( to_grafana_time_series( mapreduce_query(topic, start, stop, max_data_points, agg) ) )

@app.route('/raspimon/api/pandas/<int:start>/<int:stop>/<int:max_data_points>', methods=["POST"])
def http_get_pandas_query(start, stop, max_data_points):
    params = request.get_json(force=True)
    topics_aggs = params["topics_aggs"]
    funcs = params["funcs"]
    eval_list = [ "series({0},{1},{2},{3})".format(str(start),str(stop),
                                                   str(max_data_points),
                                                   str(topics_aggs)) ]
    for func in params: eval_list.append( ".%s"%func )
    return json.dumps( to_grafana_time_series( eval( ''.join(eval_list) ) ) )

# if __name__ == "__main__":
#     app.debug = IN_DEBUG
#     if not IN_DEBUG:
#         try:
#             handler = RotatingFileHandler('/var/log/raspimon/raspimon.log', maxBytes=10000, backupCount=1)
#             formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#             handler.setLevel(logging.INFO)
#             handler.setFormatter(formatter)
#             app.logger.addHandler(handler)
#         except IOError:
#             pass
#         except:
#             raise
#     app.run()

import math
import numpy as np
import pandas as pd

y = series(0, 1448193433, 100000,
           [ ["raspimon:b827eb7c62d8:rfemon:10:6:vrms1:value","last"],
             ["raspimon:b827eb7c62d8:rfemon:10:2:telephone:value","last"] ]).interpolate().dropna().diff().dropna().sum(axis=1)
print to_grafana_time_series(y)
