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
                   $scope.datasource.getTopicsList().then(function(topics) {
                       $scope.topics = topics;
                   });
                   $scope.datasource.getAggergatorsList().then(function(topics) {
                       $scope.aggregators = aggregators;
                   });
               };
               $scope.targetBlur = function() {
                   // TODO: perform target validation here
               };
           });
       });
