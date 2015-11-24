define([
    'angular',
],
       function (angular) {
           'use strict';

           var module = angular.module('grafana.controllers');
           
           module.controller('RaspimonQueryCtrl', function($scope, $http) {
               $scope.init = function() {
                   console.log($scope);
                   if (!$scope.target) { return; }
                   var target = $scope.target;
                   target.mul = target.mul || 1.0;
                   target.add = target.add || 0.0;
                   $scope.datasource.getTopicsList().then(function(topics) {
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
