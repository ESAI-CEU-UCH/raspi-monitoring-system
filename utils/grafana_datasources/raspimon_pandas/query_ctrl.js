define([
    'angular',
],
       function (angular) {
           'use strict';

           var module = angular.module('grafana.controllers');
           
           module.controller('RaspimonPandasQueryCtrl', function($scope, $http) {
               $scope.init = function() {
                   if (!$scope.target) { return; }
                   var target = $scope.target;
                   target.mul = target.mul || 1.0;
                   target.add = target.add || 0.0;
                   $scope.datasource.getTopicsListFiltered().then(function(topics) {
                       $scope.topics = topics;
                   });
                   $scope.datasource.getAggregatorsList().then(function(aggregators) {
                       $scope.aggregators = aggregators;
                   });
                   $scope.consolidateby = target.consolidateby || "last";
                   $scope.function_names = [
                       "abs", "add", "clip", "clip_lower", "clip_upper",
                       "cumprod", "cumsum", "diff", "div", "dropna", "fillna",
                       "floordiv", "interpolate", "mod", "mul", "nlargest",
                       "nonzero", "nsmallest", "pow", "rank", "resample",
                       "rolling_count", "rolling_kurtosis", "rolling_max",
                       "rolling_mean", "rolling_median", "rolling_min",
                       "rolling_skew", "rolling_std", "rolling_sum",
                       "rolling_var", "rolling_window", "round", "shift", "sub",
                       "replace",
                   ];
                   target.functions = target.functions || [];
                   
                   $scope.addFunction = function() {
                       target.functions.push( { "name" : undefined,
                                                "arguments" : undefined } )
                   };
                   $scope.removeFunction = function(i) {
                       target.functions.splice(i, 1);
                   };
                   $scope.moveFunction = function(i,j) {
                       if (j >= 0 && j <= target.functions.length) {
                           var tmp = target.functions[i];
                           target.functions[i] = target.functions[j];
                           target.functions[j] = tmp;
                       }
                   };
               };
               $scope.targetBlur = function() {
                   // TODO: perform target validation here
               };
           });
       });
