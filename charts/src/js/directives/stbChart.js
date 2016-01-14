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
      scope.view.fieldStates = [];
      scope.view.loading = false;
      scope.view.data;



      watchers.globalLimit = scope.$on('setLimit', function(event, newValue) {
        if (newValue !== scope.view.limit) {
          scope.view.limit = newValue;
          scope.getData();
        }
      });

      watchers.globalSince = scope.$on('setSince', function(event, newValue) {
        if (newValue !== scope.view.since) {
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

      var setFieldState = function(data) {
        scope.view.fieldStates.length = 0;
        var counter = 0;
        for (i = 0; i < data.series[0].columns.length; i++) {
          if (data.series[0].columns[i] === "time") {
            continue;
          }
          scope.view.fieldStates.push({
            name: data.series[0].columns[i],
            visible: true,
            id: counter,
            color : "rgb(0,0,0)"
          });
          counter++;
        }
      };

      // highlight areas where a select function value crosses a threshold
      // used in dygraph's underlayCallback
      var highlightAnomaly = function(canvas, area, g) {

        var timeIdx = 0;

        // draw rectangle on x0..x1
        function highlight_period(x_start, x_end, color) {
          var canvas_left_x = g.toDomXCoord(x_start);
          var canvas_right_x = g.toDomXCoord(x_end);
          var canvas_width = canvas_right_x - canvas_left_x;
          canvas.fillStyle = color;
          canvas.fillRect(canvas_left_x, area.y, canvas_width, area.h);
        }

        // find x values matching condition on y-value
        // params: data (all fields), watchedFieldName (string), threshold (for condition >thr)
        // return array with indices of anomalies
        function find_where(data, watchedFieldName, threshold) {
          var results = [];
          var fnIdx = 2;
          /*
          if (fnIdx === -1) {
            handleError("Highlighting cannot work, field anomalyScore not found!", "danger", true);
            return [];
          }*/
          for (var i = 0; i < data.length; i++) {
            var value = data[i][fnIdx];
            // the condition is here
            if (value >= 0.9) {
              var time = data[i][timeIdx];
              //console.log("Found anomaly at "+time+" with value "+value);
              results.push(time);
            }
          }
          return results;
        } //end find_where

        //highlight_period(2, 5, yellow); //test
        // find relevant points
        //for (var i = 0; i < $scope.view.fieldState.length; i++) {
          var selected, modDt, color, field;
          field = $scope.view.fieldState[fnIdx];
          //if (field.highlighted === true && field.highlightThreshold !== null) {
            selected = find_where($scope.view.data);
            // compute optimal/visible high. radius as 1% of screen area
            modDt = 0.01 * $scope.view.data.length;
            // plot all of them
            var transparency = 0.4; // min/max opacity for overlapping highs
            color = field.color.replace("rgb", "rgba").replace(")", "," + transparency + ")");
            var lastHigh = -1;
            for (var x = 0; x < selected.length; x++) {
              if(selected[x] - modDt >= lastHigh) {
                highlight_period(selected[x] - modDt, selected[x] + modDt, color);
                lastHigh = selected[x] + modDt;
              }
            }
          //}
        //}

      };

      var setColors = function(colors) {
        for (i = 0; i < colors.length; i++) {
          scope.view.fieldStates[i].color = colors[i];
        }
      };

      scope.toggleVisibility = function(field) {
        scope.view.chart.setVisibility(field.id, field.visible);
      };

      var preprocessData = function(data) {
        removeStringData(data);
        setDates(data);
        $scope.view.data = data.series[0].values;
      };

      // load the data
      scope.getData = function() {
        scope.view.loading = true;
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
        scope.view.loading = false;
        console.log(error);
      };

      // render the graph

      var renderChart = function(data) {
        setFieldState(data);
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
            labelsSeparateLines: true,
            drawCallback: function(graph, is_initial) {
              if (is_initial) {
                setColors(graph.getColors());
              }
              scope.view.loading = false;
            }/*,
            underlayCallback: highlightAnomaly*/
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
