var db = db.getSiblingDB('raspimon');

var mapfn = function() {
    var b = this.basetime;
    var t = this.topic;
    for(i=0; i<this.values.length; ++i) {
        emit(new Date(b.getTime()+this.delta_times[i]*1000.0), this.values[i]);
    }
};

var reducefn = function(key,values) {
    return values[0];
};

db.result.drop();

db.GVA2015_data.mapReduce(mapfn, reducefn,
                          {
                              "query" : { "topic" : /.*rfemon.*grid.*real.*/ },
                              "out" : "result"
                          });
