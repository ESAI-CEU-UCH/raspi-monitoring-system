var db = db.getSiblingDB('raspimon');

var mapfn = function() {
    b = this.basetime;
    for(i=0; i<this.values.length; ++i) {
        emit(new Date(b.getTime()+this.delta_times[i]*1000.0), this.values[i]);
    }
};

var reducefn = function(key,values) {
    return values[0];
};

db.GVA2015_data.mapReduce(mapfn, reducefn,
                          {
                              "query" : { "topic" : /.*plugwise.*tel.*/ },
                              "out" : { "inline":1}
                          })
