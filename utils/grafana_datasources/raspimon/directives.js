define([
    'angular',
],
       function (angular) {
           'use strict';

           var module = angular.module('grafana.directives');

           module.directive('metricQueryEditorRaspimon', function() {
               return {controller: 'RaspimonQueryCtrl', templateUrl: 'app/plugins/datasource/raspimon/partials/query.editor.html'};
           });
       });
