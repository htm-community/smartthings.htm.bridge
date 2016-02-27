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
      scope.view.data = null;
      scope.view.aggregateNumber = null;
      scope.view.aggregateUnit = null;
      scope.view.aggregateUnits = CONFIG.AGGREGATE_OPTIONS;

      watchers.globalLimits = scope.$on('setLimits', function(event, newValue) {
        if (newValue.limit !== scope.view.limit || newValue.since !== scope.view.since || newValue.aggregate.number !== scope.view.aggregateNumber || newValue.aggregate.unit !== scope.view.aggregateUnit) {
          scope.view.limit = newValue.limit;
          scope.view.since = newValue.since;
          scope.view.aggregateNumber = newValue.aggregate.number;
          scope.view.aggregateUnit = newValue.aggregate.unit;
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
          var seriesColor = CONFIG.CHART_FIELDS[data.series[0].columns[i]].color || "rgb(0,0,0)";
          scope.view.fieldStates.push({
            name: data.series[0].columns[i],
            visible: true,
            id: counter,
            color : seriesColor
          });
          counter++;
        }
      };

      var highlightAnomaly = function(canvas, area, g) {
        /* draws a line for the threshold
        canvas.fillStyle = "#C4F605";
        var thresh = g.toDomYCoord(CONFIG.ANOMALY_THRESHOLD,1);
        canvas.fillRect(area.x, thresh, area.w, 1);
        */

        var timeIdx = 0;

        // draw rectangle on x0..x1
        function highlight_period(x_start, x_end, color) {
          var width = x_end - x_start;
          canvas.fillStyle = color;
          canvas.fillRect(x_start, area.y, width, area.h);
        }

        for (var i = 0; i < scope.view.fieldStates.length; i++) {
          var start,
              end,
              first,
              last,
              color,
              field,
              fieldIndex,
              threshold,
              transparency,
              previousIndex;

          if (CONFIG.THRESHOLD_HIGHLIGHT_FIELDS.indexOf(scope.view.fieldStates[i].name) !== -1 && scope.view.fieldStates[i].visible) {
            field = scope.view.fieldStates[i];
            fieldIndex = scope.view.data.series[0].columns.indexOf(field.name);
            if (fieldIndex < 0) {
              return;
            }
            color = field.color.replace("rgb", "rgba").replace(")", ",0.5)");
            start = null;
            end = null;
            last = null;
            first = null;
            var data = scope.view.data.series[0].values;
            for (var t = 0; t < data.length; t++) {
              if (data[t][fieldIndex] >= CONFIG.ANOMALY_THRESHOLD && start === null) {
                start = g.toDomXCoord(data[t][0].getTime());
                first = t;
              }
              if (data[t][fieldIndex] >= CONFIG.ANOMALY_THRESHOLD) {
                last = t;
              }
              if (start !== null && (data[t][fieldIndex] < CONFIG.ANOMALY_THRESHOLD || t >= data.length - 1)) {
                // get leading slope
                if (t === last) {
                  end = g.toDomXCoord(data[last][0].getTime());
                } else {
                  var x1 = g.toDomXCoord(data[t][0].getTime()) - g.toDomXCoord(data[last][0].getTime());
                  var y1 = data[last][fieldIndex] - data[t][fieldIndex];
                  var z = Math.atan(x1 / y1);
                  var y2 = data[last][fieldIndex] - CONFIG.ANOMALY_THRESHOLD;
                  var x2 = y2 * Math.tan(z);
                  end = g.toDomXCoord(data[last][0].getTime()) + x2;
                }
                // get trailing slope
                previousIndex = first - 1;
                if (previousIndex >= 0) {
                  var x3 = start - g.toDomXCoord(data[previousIndex][0].getTime());
                  var y3 = data[first][fieldIndex] - data[previousIndex][fieldIndex];
                  var z2 = Math.atan(x3 / y3);
                  var y4 = data[first][fieldIndex] - CONFIG.ANOMALY_THRESHOLD;
                  var x4 = y4 * Math.tan(z2);
                  start = start - x4;
                }
                highlight_period(start, end, color);
                start = null;
                end = null;
                last = null;
                first = null;
              }
            }
          }
        }
      };

      var setColors = function(colors) {
        for (i = 0; i < colors.length; i++) {
          scope.view.fieldStates[i].color = colors[i];
        }
      };

      scope.toggleVisibility = function(field) {
        scope.view.chart.setVisibility(field.id, field.visible);
      };

      scope.showVisibilityToggle = function() {
        var show = false;
        angular.forEach(scope.view.fieldStates, function(field){
          if (field.name === "anomalyScore" || field.name === "anomalyLikelihood") {
            show = true;
          }
        });
        return show;
      };

      scope.checkAggregate = function() {
        if (!scope.view.aggregateUnit || !scope.view.since) {
          scope.view.aggregateNumber = null;
          scope.view.aggregateUnit = null;
        }
      };

      var preprocessData = function(data) {
        removeStringData(data);
        setDates(data);
        scope.view.data = data;
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
        if (scope.view.aggregateNumber !== null && scope.view.aggregateUnit !== null) {
          options.params.aggregation = scope.view.aggregateNumber.toString() + scope.view.aggregateUnit;
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
            sigFigs: 5,

            series: {
              value: {
                strokeWidth: 2,
                strokePattern: [4, 1],
                color: CONFIG.CHART_FIELDS.value.color
              },
              anomalyScore: {
                axis: 'y2',
                color: CONFIG.CHART_FIELDS.anomalyScore.color
              },
              anomalyLikelihood: {
                axis: 'y2',
                color: CONFIG.CHART_FIELDS.anomalyLikelihood.color
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
            },
            underlayCallback: highlightAnomaly
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
