angular.module('app').directive('stbChart', ['$http', 'stbUtils', function($http, stbUtils) {
  return {
    restrict: 'EA',
    scope: {
      sensorName : "@",
      sensorSince : "@",
      maxRows : "@"
    },
    replace: true,
    template: "<div class='chart'></div>",
    link: function(scope, element, attrs) {

      scope.view = {
        chart : null
      };

      var updateMinMaxDates = function() {

      };

      var removeStringData = function(data) {
        var stringColumns = ['component', 'timezone'];
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

      var convertJsonDataToCsv = function(data) {
        var rows = [];
        var series = data.series[0];

        var headers = series.columns;
        var values = series.values;

        rows.push(headers);

        _.each(values, function(values) {
            rows.push(values.join(','));
        });

        return rows.join('\n');
      };

      // load the data
      var getData = function() {
        var dataUrl = '/_data/sensor/' + scope.sensorName;//  + '?limit=' + scope.maxRows;
        /*
        if (sensorSince) {
            dataUrl += '&since=' + sensorSince;
        }
        */
        $http.get(dataUrl).then(function(sensorData) {
          // console.log(sensorData);
          scope.view.chart = renderChart(sensorData.data);
          /*
          updateMinMaxDates(scope.view.chart);
          charts.push(chart);
          if (charts.length == sensors.length) {
            _.each(charts, function(chart) {
                chart.updateOptions({
                  dateWindow: [minDate, maxDate]
                });
            });
          }
          */
        }, handleError);
      };

      var handleError = function(error) {
        console.log(error);
      };

      // render the graph

      var renderChart = function(data) {
        removeStringData(data);
        var csvString = convertJsonDataToCsv(data);
        return new Dygraph(element[0], csvString, {
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

      getData();

    }
  };
}]);
