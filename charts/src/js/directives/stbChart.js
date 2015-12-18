angular.module('app').directive('stbChart', ['$http', 'stbUtils', function($http, stbUtils) {
  return {
    restrict: 'EA',
    scope: {
      sensorName : "@",
      sensorSince : "@",
      maxRows : "@"
    },
    link: function(scope, element, attrs) {

      scope.view = {
        graph : null
      };

      // load the data
      var getData = function(sensorName) {
        console.log(scope.sensorName);
        var dataUrl = '/_data/sensor/' + scope.sensorName;//  + '?limit=' + scope.maxRows;
        /*
        if (sensorSince) {
            dataUrl += '&since=' + sensorSince;
        }
        */
        //var id = scope.sensorName.replace('/', '_').replace(/\+/g, '-');
        $http.get(dataUrl).then(function(sensorData) {
          console.log(sensorData);
          /*
          var chart = renderSensorChart(id, sensorData);
          updateMinMaxDates(chart);
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
        // var width = $('#' + id + '-container').width();
        return new Dygraph(element, csvString, {
            // width: width,
            height: 400,
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
