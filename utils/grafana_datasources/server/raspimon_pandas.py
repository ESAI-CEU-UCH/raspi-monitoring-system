#!/usr/bin/env python2.7
"""This is a bit more complicated module, similar to raspimon.py but allowing to
incorporate complex statistics using numpy and pandas.
"""
import datetime
import json
import logging
import math
import numpy as np
import pandas as pd
import pymongo
import pytz
import re
import time

from pandas import Series

from flask import Flask, request
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

IN_DEBUG=True
MONGO_HOST = "localhost"
MONGO_PORT = 27018
tz = pytz.timezone("Europe/Madrid")

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

class MySeries:
    def __init__(self, *args, **kwargs):
        self.x = Series(*args, **kwargs)
        self.values = self.x.values
        self.index = self.x.index
    
    def rolling_mean(self, *args, **kwargs):
        return MySeries(pd.rolling_mean(self.x, *args, **kwargs))

    def rolling_count(self, *args, **kwargs):
        return MySeries(pd.rolling_count(self.x, *args, **kwargs))

    def rolling_sum(self, *args, **kwargs):
        return MySeries(pd.rolling_sum(self.x, *args, **kwargs))

    def rolling_median(self, *args, **kwargs):
        return MySeries(pd.rolling_median(self.x, *args, **kwargs))
        
    def rolling_min(self, *args, **kwargs):
        return MySeries(pd.rolling_min(self.x, *args, **kwargs))

    def rolling_max(self, *args, **kwargs):
        return MySeries(pd.rolling_max(self.x, *args, **kwargs))

    def rolling_std(self, *args, **kwargs):
        return MySeries(pd.rolling_std(self.x, *args, **kwargs))

    def rolling_var(self, *args, **kwargs):
        return MySeries(pd.rolling_var(self.x, *args, **kwargs))

    def rolling_skew(self, *args, **kwargs):
        return MySeries(pd.rolling_skew(self.x, *args, **kwargs))

    def rolling_kurtosis(self, *args, **kwargs):
        return MySeries(pd.rolling_kurtosis(self.x, *args, **kwargs))

    def rolling_window(self, *args, **kwargs):
        return MySeries(pd.rolling_window(self.x, *args, **kwargs))

    def cumprod(self, *args, **kwargs):
        return MySeries(self.x.cumprod(*args, **kwargs))

    def cumsum(self, *args, **kwargs):
        return MySeries(self.x.cumsum(*args, **kwargs))

    def diff(self, *args, **kwargs):
        return MySeries(self.x.diff(*args, **kwargs))

    def div(self, *args, **kwargs):
        return MySeries(self.x.div(*args, **kwargs))

    def mul(self, *args, **kwargs):
        return MySeries(self.x.mul(*args, **kwargs))

    def add(self, *args, **kwargs):
        return MySeries(self.x.add(*args, **kwargs))

    def dropna(self, *args, **kwargs):
        return MySeries(self.x.dropna(*args, **kwargs))
    
    def fillna(self, *args, **kwargs):
        return MySeries(self.x.fillna(*args, **kwargs))

    def floordiv(self, *args, **kwargs):
        return MySeries(self.x.floordiv(*args, **kwargs))

    def mod(self, *args, **kwargs):
        return MySeries(self.x.mod(*args, **kwargs))

    def nlargest(self, *args, **kwargs):
        return MySeries(self.x.nlargest(*args, **kwargs))

    def nonzero(self, *args, **kwargs):
        return MySeries(self.x.nonzero(*args, **kwargs))

    def nsmallest(self, *args, **kwargs):
        return MySeries(self.x.nsmallest(*args, **kwargs))

    def pow(self, *args, **kwargs):
        return MySeries(self.x.pow(*args, **kwargs))

    def rank(self, *args, **kwargs):
        return MySeries(self.x.rank(*args, **kwargs))

    def round(self, *args, **kwargs):
        return MySeries(self.x.round(*args, **kwargs))

    def shift(self, *args, **kwargs):
        return MySeries(self.x.shift(*args, **kwargs))

    def sub(self, *args, **kwargs):
        return MySeries(self.x.sub(*args, **kwargs))

    def abs(self, *args, **kwargs):
        return MySeries(self.x.abs(*args, **kwargs))

    def clip(self, *args, **kwargs):
        return MySeries(self.x.clip(*args, **kwargs))

    def clip_lower(self, *args, **kwargs):
        return MySeries(self.x.clip_lower(*args, **kwargs))

    def clip_upper(self, *args, **kwargs):
        return MySeries(self.x.clip_upper(*args, **kwargs))
    
    def interpolate(self, *args, **kwargs):
        return MySeries(self.x.interpolate(*args, **kwargs))

    def resample(self, *args, **kwargs):
        return MySeries(self.x.resample(*args, **kwargs))
    
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
    if len(data) == 0: return MySeries(np.array([]))
    if len(data) == 1:
        idx = np.array([ data[0]["value"]["secs"] ])
        ts = np.array([ [data[0]["value"]["value"]] ])
        return MySeries(ts, index=idx)
    idx = []
    ts = []
    for pair in data:
        p = pair["value"]
        idx.append( datetime.datetime.fromtimestamp(p["secs"], tzinfo=tz) )
        ts.append( p["value"] )
    return MySeries(np.array(ts), index=np.array(idx))

def get_topics(filters=None):
    client,col = connect()
    if False:
        # This code is not working, pymongo Collection.distinct don't accepts a
        # query as argument :'( (we need to wait for next version update in
        # Ubuntu)
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
    topics = filter(lambda x: not x.startswith("forecast"), topics)
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

#def series(topic, start, stop, max_data_points, agg):
#    return mapreduce_query(topic, start, stop, max_data_points, agg)

def to_grafana_time_series(s):
    def filt(x):
        try:
            if math.isnan(x): return None
            else: return x
        except:
            return x

    values = s.values
    if len(values.shape) == 1: values = list( values )
    else: values = list( values[:,0] )
    dates = list( s.index )
    result = [ [filt(v),time.mktime(k.timetuple())] for v,k in zip(values,dates) ]
    return result

def process_series(ts, funcs):
    g = { "__builtins__" : None } # only allow time-series object
    for f in funcs:
        ts = eval("ts.{0}".format(f), g, { "ts" : ts })
    return ts

@app.route("/raspimon_pandas/api/topics")
def http_get_topics():
    return json.dumps( get_topics() )

@app.route("/raspimon_pandas/api/topics/filtered", methods=["POST"])
def http_post_topics_filtered():
    filters = request.get_json(force=True)
    return json.dumps( get_topics(filters) )

@app.route("/raspimon_pandas/api/aggregators")
def http_get_aggregators():
    return json.dumps( reduce_operators.keys() );

# http://localhost:5000/raspimon_pandas/api/aggregate/last/raspimon:b827eb7c62d8:rfemon:10:6:vrms1:value/0/1448193433/100

@app.route('/raspimon_pandas/api/aggregate/<string:agg>/<string:topic>/<int:start>/<int:stop>/<int:max_data_points>')
def http_get_aggregation_query(agg, topic, start, stop, max_data_points):
    return json.dumps( to_grafana_time_series( mapreduce_query(topic, start, stop, max_data_points, agg) ) )

@app.route('/raspimon_pandas/api/pandas/<string:agg>/<string:topic>/<int:start>/<int:stop>/<int:max_data_points>', methods=["POST"])
def http_get_pandas_query(agg, topic, start, stop, max_data_points):
    funcs = request.get_json(force=True)
    ts = mapreduce_query(topic, start, stop, max_data_points, agg)
    return json.dumps( to_grafana_time_series( process_series(ts, funcs) ) )

if __name__ == "__main__":
    app.debug = IN_DEBUG
    if not IN_DEBUG:
        try:
            handler = RotatingFileHandler('/var/log/raspimon_pandas/raspimon_pandas.log', maxBytes=10000, backupCount=1)
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setLevel(logging.INFO)
            handler.setFormatter(formatter)
            app.logger.addHandler(handler)
        except IOError:
            pass
        except:
            raise
    app.run(port=5050)

# import math
# import numpy as np
# import pandas as pd

# y = mapreduce_query("raspimon:b827eb7c62d8:rfemon:10:6:vrms1:value", 1448183433, 1448193433, 100, "last")

# z = process_series(y, [
#     [ "diff" ],
#     [ "fillna", None, "backfill" ],
#     [ "mul", 4 ],
#     [ "add", 4 ],
#     [ "diff" ],
#     [ "rolling_mean",  20 ],
#     [ "dropna" ],
# ])

# print to_grafana_time_series(y)
# print to_grafana_time_series(z)
