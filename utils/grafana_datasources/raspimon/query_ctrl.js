define([
    'angular',
],
       function (angular) {
           'use strict';

           var module = angular.module('grafana.controllers');
           
           module.controller('RaspimonQueryCtrl', function($scope, $http) {
               $scope.init = function() {
                   if (!$scope.target) { return; }
                   var target = $scope.target;
                   target.topics = [];
                   $scope.updateTopicsList(target);
               };

               $scope.updateTopicsList = function(target) {
                   $http({
                       method: 'GET',
                       url: target.datasource.url + "/raspimon/api/topics"
                   }).then(function successCallback(response) {
                       target.topics.push.apply(response.data);
                   }, function errorCallback(response) {
                   });
               };
               
           });
       });
