define([
    'angular',
    'lodash',
    'app/core/utils/datemath',
    'moment',
    './directives',
    './autogrow'
    './query_ctrl',
],
       function (angular, _, dateMath) {
           'use strict';

           var module = angular.module('grafana.services');

           module.factory('RaspimonPandasDatasource', function($q, backendSrv) {

               // the datasource object passed to constructor is the same
               // defined in config.js named `current`
               function RaspimonPandasDatasource(datasource) {
                   this.name = datasource.name;
                   this.type = "raspimon_pandas";
                   this.url  = datasource.url;
                   // jsonData is a dictionary created by the controller and
                   // resued by raspimon_pandas to track new configuration items
                   if (datasource.jsonData) {
                       this.topic_filters = datasource.jsonData.topic_filters;
                   }
                   else {
                       this.topic_filters = [];
                   }
                   this.supportMetrics = true;
               }
               
               // performs an HTTP GET request to datasource using the
               // backendSrv
               RaspimonPandasDatasource.prototype._get = function(relativeUrl) {
                   return backendSrv.datasourceRequest({
                       method: 'GET',
                       url: this.url + relativeUrl,
                   });
               };

               // performs an HTTP POST request to datasource using the
               // backendSrv
               RaspimonPandasDatasource.prototype._post = function(relativeUrl, data) {
                   return backendSrv.datasourceRequest({
                       method: 'POST',
                       url: this.url + relativeUrl,
                       data: data,
                   });
               };
               
               // Receives a query configuration (as defined in query editor),
               // an array of data as returned by datasource request, and
               // returns it as a time-series object expected by Grafana.
               var transformToTimeSeries = function(query, data) {
                   var dps = [];
                   _.each(data, function(v) {
                       var mul = query.mul || 1.0;
                       var add = query.add || 0.0;
                       // multiply timestamp by 1000 to transform from float
                       // seconds to integer miliseconds
                       dps.push([v[0]*mul + add, Math.round(v[1] * 1000)]);
                   });
                   // a time-series has 'target' string and 'datapoints' array
                   return {
                       target: query.alias || query.topic,
                       datapoints: dps,
                   };
               };
               
               // a facility which allow to cache call to functions which return
               // a promise
               var buildCachedPromiseMethod = function(func) {
                   var promise;
                   return function() {
                       if (!promise) promise = func(this);
                       return promise;
                   }
               };
               
               // This function processes all queries in array `options.target`
               // using the configuration of `options` object. It requests every
               // query to datasource server and transforms its response into a
               // time-series expected by Grafana.
               RaspimonPandasDatasource.prototype.query = function(options) {
                   console.log('options: ' + JSON.stringify(options));
                   var self = this; // forward declaration
                   // get from & to in seconds
                   var from = Math.floor(dateMath.parse(options.range.from) / 1000);
                   var to = Math.ceil(dateMath.parse(options.range.to) / 1000);
                   var maxDataPoints = options.maxDataPoints
                   var qs = [];
                   
                   // take only not hidden `targets` and with a proper topic
                   _.each(options.targets, function(target) {
                       if (target.topic && !target.hide) qs.push(target);
                   });
                   
                   if (_.isEmpty(qs)) {
                       var d = $q.defer();
                       d.resolve({ data: [] });
                       return d.promise;
                   }
                   
                   var buildQueryUrl = function(topic, aggregator) {
                       return "/raspimon_pandas/api/aggregate/" + aggregator + "/" + topic + "/" + from + "/" + to + "/" + maxDataPoints;
                   };
                   
                   // chain all promises, one per each element at qs (targets)
                   var promises = []
                   _.each(qs, function(q) {
                       promises.push( self._get(buildQueryUrl(q.topic, q.consolidateby || "last"))
                                      .then(function(response) {
                                          return transformToTimeSeries(q, response.data);
                                      }) );
                   });
                   
                   return $q.all(promises).then(function(result) {
                       // this is the object expected by Grafana
                       return { data: result };
                   });
               };
               
               // test connectivity requesting the list of topics (all topics)
               RaspimonPandasDatasource.prototype.testDatasource = function () {
                   return this._get('/raspimon_pandas/api/topics').then(function(topics) {
                       if (!topics) return { status: "error", message: "Unable to connect to data source" };
                       return { status: "success", message: "Data source is working", title: "Success" };
                   });
               };
               
               // facility to process array responses given by datasource
               var array_promise_callback = function(result) {
                   if (result.data && _.isArray(result.data)) {
                       return result.data.sort();
                   }
                   return [];
               };
               
               var contains_any = function(filters) {
                   return function(x) {
                       var any = false;
                       for (var i=0; i<filters.length && !any; ++i) {
                           any = (x.indexOf(filters[i]) > -1);
                       }
                       return any;
                   };
               };
               
               // Facility to request topics list from query editor.
               RaspimonPandasDatasource.prototype.getTopicsList = buildCachedPromiseMethod(function(self) {
                   return self._get('/raspimon_pandas/api/topics').then(array_promise_callback)
               })
               
               // Returns the list of topics filtered by using topic_filters
               // property as declared at datasource configuration.
               RaspimonPandasDatasource.prototype.getTopicsListFiltered = function() {
                   var self = this;
                   return this.getTopicsList().then(function(result) {
                       if (self.topic_filters && self.topic_filters.length > 0) {
                           return result.filter(contains_any(self.topic_filters));
                       }
                       else {
                           return result;
                       }
                   });
               };
               
               // facility to request aggregators list from query editor
               RaspimonPandasDatasource.prototype.getAggregatorsList = buildCachedPromiseMethod(function(self) {
                   return self._get('/raspimon_pandas/api/aggregators').then(array_promise_callback);
               });
               
               return RaspimonPandasDatasource;
           });
       });
