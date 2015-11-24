define([
    'angular',
],
       function (angular) {
           'use strict';

           var module = angular.module('grafana.directives');

           module.directive('metricQueryEditorRaspimonPandas', function() {
               return {controller: 'RaspimonPandasQueryCtrl', templateUrl: 'app/plugins/datasource/raspimon_pandas/partials/query.editor.html'};
           });

           module.directive('metricQueryOptionsRaspimonPandas', function() {
               return {templateUrl: 'app/plugins/datasource/raspimon_pandas/partials/query.options.html'};
           });

       });
