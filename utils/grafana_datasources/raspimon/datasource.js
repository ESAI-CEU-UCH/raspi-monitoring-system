define([
    'angular',
    'lodash',
    'app/core/utils/datemath',
    'moment',
    './query_ctrl.js'
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

               RaspimonDatasource.prototype.query = function(options) {
                   console.log(options);
                   // get from & to in seconds
                   var from = Math.ceil(dateMath.parse(options.range.from) / 1000);
                   var to = Math.ceil(dateMath.parse(options.range.to) / 1000);
                   var maxDataPoints = options.maxDataPoints
                   var topic = "raspimon:b827eb7c62d8:aemet:46250:humidity:value"; //options.target;
                   var query = this.url + "/raspimon/api/query/" + topic + "/" + from + "/" + to + "/" + maxDataPoints;
                   var options = {
                       method: 'GET',
                       url: query
                   };
                   return backendSrv.datasourceRequest(options).then(function (result) {
                       return result;
                   }).then(function (response) {
                       // this callback will be called asynchronously
                       // when the response is available
                       var data = [ [topic,response.data] ];
                       var series = [];
                       for (var i=0; i<data.length; ++i) {
                           var timeSeries = {
                               target: data[i][0],
                               datapoints: data[i][1],
                           }
                           series.push(timeSeries);
                       }
                       console.log(series);
                       return { data: series };
                   });
               };

               RaspimonDatasource.prototype.testDatasource = function () {
                   var options = {
                       method: 'GET',
                       url: this.url + '/raspimon/api/topics',
                   };
                   return backendSrv.datasourceRequest(options).then(function () {
                       return { status: "success", message: "Data source is working", title: "Success" };
                   });
               };

               return RaspimonDatasource;
           });
       });
