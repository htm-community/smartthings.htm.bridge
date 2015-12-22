angular.module('app').directive('stbChart', ['$http', 'stbUtils', 'CONFIG', function($http, stbUtils, CONFIG) {
  return {
    restrict: 'EA',
    scope: {
      sensorName : "@"
    },
    replace: true,
    templateUrl: "directives/stbChart.tpl.html",
    link: function(scope, element, attrs) {

      var i,
          watchers = {};

      // scope.view should be inherited from the parent scope, but if it is not:
      if (!scope.view) {
        scope.view = {};
      }

      scope.view.chart = null;
      scope.view.limitOptions = CONFIG.LIMIT_OPTIONS;
      scope.view.limit = CONFIG.LIMIT_OPTIONS[0];
      scope.view.since = null;
      scope.view.sinceOptions = CONFIG.SINCE_OPTIONS;



      watchers.globalLimit = scope.$on('setLimit', function(event, newValue) {
        if (newValue !== scope.view.limit) {
          scope.view.limit = newValue;
          scope.getData();
        }
      });

      watchers.globalSince = scope.$on('setSince', function(event, newValue) {
        if (newValue !== scope.view.since) {
          console.log(newValue);
          scope.view.since = newValue;
          scope.getData();
        }
      });

      var getSince = function(since) {
        var now = moment();
        var duration = moment.duration(since.number, since.units);
        return now.subtract(duration).unix();
      };

      var removeStringData = function (data) {
        var stringColumns = CONFIG.STRING_COLUMNS;
        var doomedIndexes = [];
        var series = data.series[0];
        angular.forEach(series.columns, function(name, index) {
          if (stringColumns.indexOf(name) !== -1) {
            doomedIndexes.push(index);
          }
        });
        // Now that we know which indexes are doomed, we reverse the order so we
        // can extract them from the list from the end
        doomedIndexes = doomedIndexes.reverse();
        angular.forEach(doomedIndexes, function(doomed) {
            series.columns.splice(doomed, 1);
        });
        angular.forEach(series.values, function(row) {
            angular.forEach(doomedIndexes, function(doomed) {
                row.splice(doomed, 1);
            });
        });
      };

      // parseDate():
      // takes a string and attempts to convert it into a Date object
      // return: Date object, or null if parsing failed
      var parseDate = function(strDateTime) { // FIXME: Can using the ISO format simplify this?
        // can we get the browser to parse this successfully?
        var numDate = new Date(strDateTime);
        if (numDate.toString() !== "Invalid Date") {
          return numDate;
        }
        var dateTime = String(strDateTime).split(" "); // we are assuming that the delimiter between date and time is a space
        var args = [];
        // is the date formatted with slashes or dashes?
        var slashDate = dateTime[0].split("/");
        var dashDate = dateTime[0].split("-");
        if ((slashDate.length === 1 && dashDate.length === 1) || (slashDate.length > 1 && dashDate.length > 1)) {
          // if there were no instances of delimiters, or we have both delimiters when we should only have one
          handleError("Could not parse the timestamp", "warning", true);
          return null;
        }
        // if it is a dash date, it is probably in this format: yyyy:mm:dd
        if (dashDate.length > 2) {
          args.push(dashDate[0]);
          args.push(dashDate[1]);
          args.push(dashDate[2]);
        }
        // if it is a slash date, it is probably in this format: mm/dd/yy
        else if (slashDate.length > 2) {
          args.push(slashDate[2]);
          args.push(slashDate[0]);
          args.push(slashDate[1]);
        } else {
          handleError("There was something wrong with the date in the timestamp field.", "warning", true);
          return null;
        }
        // is there a time element?
        if (dateTime[1]) {
          var time = dateTime[1].split(":");
          args = args.concat(time);
        }
        for (var t = 0; t < args.length; t++) {
          args[t] = parseInt(args[t]);
        }
        numDate = new Function.prototype.bind.apply(Date, [null].concat(args));
        if (numDate.toString() === "Invalid Date") {
          handleError("The timestamp appears to be invalid.", "warning", true);
          return null;
        }
        return numDate;
      };

      var setDates = function(data) {
        // find timestamp column
        var index = 0;
        for (i = 0; i < data.series[0].columns.length; i++) {
          if (data.series[0].columns[i] === "time" || data.series[0].columns[i] === "timestamp") {
            index = i;
            break;
          }
        }
        for (i = 0; i < data.series[0].values.length; i++) {
          data.series[0].values[i][index] = parseDate(data.series[0].values[i][index]);
        }
        return data;
      };

      var preprocessData = function(data) {
        removeStringData(data);
        setDates(data);
      };

      // load the data
      scope.getData = function() {
        var dataUrl = '/_data/sensor/' + scope.sensorName;
        var options = {
          'params' : {}
        };
        if (scope.view.limit !== null) {
          options.params.limit = scope.view.limit;
        }
        if (scope.view.since !== null) {
          options.params.since = getSince(scope.view.since);
        }
        $http.get(dataUrl, options).then(function(sensorData) {
          // console.log(sensorData);
          if (angular.isDefined(sensorData.data.series)) {
            preprocessData(sensorData.data);
            if (scope.view.chart !== null) {
              scope.view.chart.updateOptions({'file': sensorData.data.series[0].values});
            } else {
              scope.view.chart = renderChart(sensorData.data);
            }
          } else {
            scope.view.chart = null;
          }
        }, handleError);
      };

      var handleError = function(error) {
        console.log(error);
      };

      // render the graph

      var renderChart = function(data) {
        var container = element.find('.chart-container');
        return new Dygraph(
          container[0],
          data.series[0].values,
          {
            labels: data.series[0].columns,
            series: {
              value: {
                strokeWidth: 2,
                strokePattern: [4, 1]
              },
              anomalyScore: {
                axis: 'y2',
                color: 'orange'
              },
              anomalyLikelihood: {
                axis: 'y2',
                color: 'red'
              }
            },
            axes: {
              y2: {
                valueRange: [0, 1.1]
              }
            },
            legend: 'follow',
            labelsSeparateLines: true
        });
      };

      scope.getData();

      scope.$on("$destroy", function(){
        angular.forEach(watchers, function(watcher){
          watcher();
        });
      });

    }
  };
}]);
