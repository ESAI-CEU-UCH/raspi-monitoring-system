define([
    'angular',
    './gfunc'
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
                   $scope.consolidateby = "last";
               };
               $scope.targetBlur = function() {
                   // TODO: perform target validation here
               };
           });
       });
