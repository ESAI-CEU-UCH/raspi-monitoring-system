// original version for Graphite plugin in Grafana:
// https://github.com/grafana/grafana/tree/master/public/app/plugins/datasource/graphite
define([
    'lodash',
    'jquery'
],
       function (_, $) {
           'use strict';

           var index = [];
           var categories = {
               All: [],
           };

           function addFuncDef(funcDef) {
               funcDef.params = funcDef.params || [];
               funcDef.defaultParams = funcDef.defaultParams || [];

               if (funcDef.category) {
                   funcDef.category.push(funcDef);
               }
               index[funcDef.name] = funcDef;
               index[funcDef.shortName || funcDef.name] = funcDef;
           }

           var optionalSeriesRefArgs = [
               { name: 'other', type: 'value_or_series', optional: true },
               { name: 'other', type: 'value_or_series', optional: true },
               { name: 'other', type: 'value_or_series', optional: true },
               { name: 'other', type: 'value_or_series', optional: true },
               { name: 'other', type: 'value_or_series', optional: true }
           ];

           var how_options = ['sum','mean','median','min','max','None'];
           
           addFuncDef({
               name: 'rolling_mean',
               category: categories.All,
               params: [
                   { name: 'window', type: 'int' },
                   { name: 'min_periods', type: 'int' },
                   { name: 'freq', type: 'string' },
                   { name: 'center', type: 'boolean' },
                   { name: 'how', type: 'string', options: how_options },
               ],
               defaultParams: [10, null, null, false, 'mean'],
           });
           
           addFuncDef({
               name: 'rolling_count',
               category: categories.All,
               params: [
                   { name: 'window', type: 'int' },
                   { name: 'min_periods', type: 'int' },
                   { name: 'freq', type: 'string' },
                   { name: 'center', type: 'boolean' },
                   { name: 'how', type: 'string', options: how_options },
               ],
               defaultParams: [10, null, null, false, 'mean'],
           });

           addFuncDef({
               name: 'rolling_median',
               category: categories.All,
               params: [
                   { name: 'window', type: 'int' },
                   { name: 'min_periods', type: 'int' },
                   { name: 'freq', type: 'string' },
                   { name: 'center', type: 'boolean' },
                   { name: 'how', type: 'string', options: how_options },
               ],
               defaultParams: [10, null, null, false, 'median'],
           });
           
           addFuncDef({
               name: 'rolling_sum',
               category: categories.All,
               params: [
                   { name: 'window', type: 'int' },
                   { name: 'min_periods', type: 'int' },
                   { name: 'freq', type: 'string' },
                   { name: 'center', type: 'boolean' },
                   { name: 'how', type: 'string', options: how_options },
               ],
               defaultParams: [10, null, null, false, 'mean'],
           });
           
           addFuncDef({
               name: 'rolling_min',
               category: categories.All,
               params: [
                   { name: 'window', type: 'int' },
                   { name: 'min_periods', type: 'int' },
                   { name: 'freq', type: 'string' },
                   { name: 'center', type: 'boolean' },
                   { name: 'how', type: 'string', options: how_options },
               ],
               defaultParams: [10, null, null, false, 'min'],
           });

           addFuncDef({
               name: 'rolling_max',
               category: categories.All,
               params: [
                   { name: 'window', type: 'int' },
                   { name: 'min_periods', type: 'int' },
                   { name: 'freq', type: 'string' },
                   { name: 'center', type: 'boolean' },
                   { name: 'how', type: 'string', options: how_options },
               ],
               defaultParams: [10, null, null, false, 'max'],
           });

           addFuncDef({
               name: 'rolling_std',
               category: categories.All,
               params: [
                   { name: 'window', type: 'int' },
                   { name: 'min_periods', type: 'int' },
                   { name: 'freq', type: 'string' },
                   { name: 'center', type: 'boolean' },
                   { name: 'how', type: 'string', options: how_options },
               ],
               defaultParams: [10, null, null, false, 'None'],
           });
           
           addFuncDef({
               name: 'rolling_var',
               category: categories.All,
               params: [
                   { name: 'window', type: 'int' },
                   { name: 'min_periods', type: 'int' },
                   { name: 'freq', type: 'string' },
                   { name: 'center', type: 'boolean' },
                   { name: 'how', type: 'string', options: how_options },
               ],
               defaultParams: [10, null, null, false, 'None'],
           });

           addFuncDef({
               name: 'rolling_skew',
               category: categories.All,
               params: [
                   { name: 'window', type: 'int' },
                   { name: 'min_periods', type: 'int' },
                   { name: 'freq', type: 'string' },
                   { name: 'center', type: 'boolean' },
                   { name: 'how', type: 'string', options: how_options },
               ],
               defaultParams: [10, null, null, false, 'mean'],
           });

           addFuncDef({
               name: 'rolling_kurtosis',
               category: categories.All,
               params: [
                   { name: 'window', type: 'int' },
                   { name: 'min_periods', type: 'int' },
                   { name: 'freq', type: 'string' },
                   { name: 'center', type: 'boolean' },
                   { name: 'how', type: 'string', options: how_options },
               ],
               defaultParams: [10, null, null, false, 'None'],
           });
           
           addFuncDef({
               name: 'cumprod',
               category: categories.All,
               params: [],
               defaultParams: [],
           });

           addFuncDef({
               name: 'cumsum',
               category: categories.All,
               params: [],
               defaultParams: [],
           });
           
           addFuncDef({
               name: 'diff',
               category: categories.All,
               params: [],
               defaultParams: [],
           });

           addFuncDef({
               name: 'div',
               category: categories.All,
               params: [ { name: 'n', type: 'float' } ],
               defaultParams: [1.0],
           });

           addFuncDef({
               name: 'mul',
               category: categories.All,
               params: [ { name: 'n', type: 'float' } ],
               defaultParams: [1.0],
           });

           addFuncDef({
               name: 'add',
               category: categories.All,
               params: [ { name: 'n', type: 'float' } ],
               defaultParams: [0.0],
           });
           
           addFuncDef({
               name: 'dropna',
               category: categories.All,
               params: [],
               defaultParams: [],
           });

           addFuncDef({
               name: 'fillna',
               category: categories.All,
               params: [ { name: 'n', type: 'float' } ],
               defaultParams: [0.0],
           });
           
           addFuncDef({
               name: 'mod',
               category: categories.All,
               params: [ { name: 'n', type: 'float' } ],
               defaultParams: [1.0],
           });
           
           addFuncDef({
               name: 'nlargest',
               category: categories.All,
               params: [ { name: 'n', type: 'int' } ],
               defaultParams: [1.0],
           });

           addFuncDef({
               name: 'nsmallest',
               category: categories.All,
               params: [ { name: 'n', type: 'int' } ],
               defaultParams: [1.0],
           });
           
           addFuncDef({
               name: 'nonzero',
               category: categories.All,
               params: [],
               defaultParams: [],
           });

           addFuncDef({
               name: 'rank',
               category: categories.All,
               params: [],
               defaultParams: [],
           });

           addFuncDef({
               name: 'round',
               category: categories.All,
               params: [],
               defaultParams: [],
           });
           
           addFuncDef({
               name: 'shift',
               category: categories.All,
               params: [ { name: 'n', type: 'int' } ],
               defaultParams: [0.0],
           });

           addFuncDef({
               name: 'pow',
               category: categories.All,
               params: [ { name: 'n', type: 'float' } ],
               defaultParams: [1.0],
           });

           addFuncDef({
               name: 'abs',
               category: categories.All,
               params: [],
               defaultParams: [],
           });
           
           addFuncDef({
               name: 'clip',
               category: categories.All,
               params: [ { name: 'a', type: 'float' }, { name: 'a', type: 'float' } ],
               defaultParams: [0.0,1.0],
           });
           
           addFuncDef({
               name: 'clip_lower',
               category: categories.All,
               params: [ { name: 'n', type: 'float' } ],
               defaultParams: [0.0],
           });

           addFuncDef({
               name: 'clip_upper',
               category: categories.All,
               params: [ { name: 'n', type: 'float' } ],
               defaultParams: [1.0],
           });

           addFuncDef({
               name: 'interpolate',
               category: categories.All,
               params: [],
               defaultParams: [],
           });

           addFuncDef({
               name: 'resample',
               category: categories.All,
               params: [
                   { name: 'rule', type: 'string' },
                   { name: 'how', type: 'string', options: how_options },
               ],
               defaultParams: [null,'mean'],
           });
           
           _.each(categories, function(funcList, catName) {
               categories[catName] = _.sortBy(funcList, 'name');
           });

           function FuncInstance(funcDef, options) {
               this.def = funcDef;
               this.params = [];

               if (options && options.withDefaultParams) {
                   this.params = funcDef.defaultParams.slice(0);
               }

               this.updateText();
           }

           FuncInstance.prototype.render = function(metricExp) {
               var str = this.def.name + '(';
               var parameters = _.map(this.params, function(value, index) {

                   var paramType = this.def.params[index].type;
                   if (paramType === 'int' || paramType === 'value_or_series' || paramType === 'boolean') {
                       return value;
                   }
                   else if (paramType === 'int_or_interval' && $.isNumeric(value)) {
                       return value;
                   }

                   return "'" + value + "'";

               }, this);

               if (metricExp) {
                   parameters.unshift(metricExp);
               }

               return str + parameters.join(', ') + ')';
           };

           FuncInstance.prototype._hasMultipleParamsInString = function(strValue, index) {
               if (strValue.indexOf(',') === -1) {
                   return false;
               }

               return this.def.params[index + 1] && this.def.params[index + 1].optional;
           };

           FuncInstance.prototype.updateParam = function(strValue, index) {
               // handle optional parameters
               // if string contains ',' and next param is optional, split and update both
               if (this._hasMultipleParamsInString(strValue, index)) {
                   _.each(strValue.split(','), function(partVal, idx) {
                       this.updateParam(partVal.trim(), idx);
                   }, this);
                   return;
               }

               if (strValue === '' && this.def.params[index].optional) {
                   this.params.splice(index, 1);
               }
               else {
                   this.params[index] = strValue;
               }

               this.updateText();
           };

           FuncInstance.prototype.updateText = function () {
               if (this.params.length === 0) {
                   this.text = this.def.name + '()';
                   return;
               }

               var text = this.def.name + '(';
               text += this.params.join(', ');
               text += ')';
               this.text = text;
           };

           return {
               createFuncInstance: function(funcDef, options) {
                   if (_.isString(funcDef)) {
                       if (!index[funcDef]) {
                           throw { message: 'Method not found ' + name };
                       }
                       funcDef = index[funcDef];
                   }
                   return new FuncInstance(funcDef, options);
               },

               getFuncDef: function(name) {
                   return index[name];
               },

               getCategories: function() {
                   return categories;
               }
           };

       });
