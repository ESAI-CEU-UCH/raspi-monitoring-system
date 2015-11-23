define([
    'angular',
    'lodash',
    'app/core/utils/datemath',
    'moment',
    './directives',
    './query_ctrl'
],
       function (angular, _, dateMath) {
           'use strict';

           var module = angular.module('grafana.services');

           module.factory('RaspimonDatasource', function($q, backendSrv) {

               // the datasource object passed to constructor
               // is the same defined in config.js
               function RaspimonDatasource(datasource) {
                   this.name = datasource.name;
                   this.type = "raspimon";
                   this.url  = datasource.url;
                   this.supportMetrics = true;
               }
               
               RaspimonDatasource.prototype._get = function(relativeUrl, params) {
                   return backendSrv.datasourceRequest({
                       method: 'GET',
                       url: this.url + relativeUrl,
                       params: params,
                   });
               };

               var transformToTimeSeries = function(query, data) {
                   var dps = [];
                   _.each(data, function(v, k) {
                       console.log(v, k);
                       dps.push([v, Math.round(k * 1000)]);
                   })
                   return {
                       target: query.alias || query.topic,
                       datapoints: dps,
                   };
               };
               
               RaspimonDatasource.prototype.query = function(options) {
                   console.log('options: ' + JSON.stringify(options));
                   // get from & to in seconds
                   var from = Math.floor(dateMath.parse(options.range.from) / 1000);
                   var to = Math.ceil(dateMath.parse(options.range.to) / 1000);
                   var maxDataPoints = options.maxDataPoints
                   var qs = [];

                   _.each(options.targets, function(target) {
                       if (!target.topic || target.hide) { return; }
                       qs.push({ topic: target.topic, alias: target.alias });
                   });

                   if (_.isEmpty(qs)) {
                       var d = $q.defer();
                       d.resolve({ data: [] });
                       return d.promise;
                   }

                   var buildQuery = function(topic) {
                       return "/raspimon/api/query/" + topic + "/" + from + "/" + to + "/" + maxDataPoints;
                   };

                   // chain all promises, one per each element at qs (targets)
                   var self = this;
                   var promises = []
                   _.each(qs, function(q) {
                       promises.push( self._get(buildQuery(q.topic))
                                      .then(function(response) {
                                          return transformToTimeSeries(q, response.data);
                                      }) );
                   });
                   
                   return $q.all(promises).then(function(result) {
                       console.log(result);
                       return { data: result };
                   });
               };

               RaspimonDatasource.prototype.testDatasource = function () {
                   return this._get('/raspimon/api/topics').then(function(topics) {
                       if (!topics) return { status: "error", message: "Unable to connect to data source" };
                       return { status: "success", message: "Data source is working", title: "Success" };
                   });
               };

               RaspimonDatasource.prototype.getTopicsList = function() {
                   return this._get('/raspimon/api/topics').then(function(result) {
                       if (result.data && _.isArray(result.data)) {
                           return result.data.sort();
                       }
                       return [];
                   });
               };
               
               return RaspimonDatasource;
           });
       });
