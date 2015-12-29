angular.module('app', [
  'ui.bootstrap',
  'templates',
  'ui.router',
  'home',
  'sensors',
  'pageNotFound']);

// some Settings:
angular.module('app').constant('CONFIG', {
  'STRING_COLUMNS': ['component', 'timezone'],
  'LIMIT_OPTIONS': [100, 500, 1000, 5000, 10000, 50000],
  'SINCE_OPTIONS': [{
    number: 10,
    units: 'minutes'
  }, {
    number: 1,
    units: 'hour'
  }, {
    number: 3,
    units: 'hours'
  }, {
    number: 6,
    units: 'hours'
  }, {
    number: 12,
    units: 'hours'
  }, {
    number: 1,
    units: 'day'
  }, {
    number: 3,
    units: 'days'
  }, {
    number: 1,
    units: 'week'
  }]
});

angular.module('app').config(['$stateProvider', '$urlRouterProvider', function($stateProvider, $urlRouterProvider) {
  // set up the states
  $stateProvider
    .state('home', {
      url: "/",
      templateUrl: "routes/home/home.tpl.html",
      controller: "HomeController"
    })
    .state('pageNotFound', {
      url: "/pageNotFound",
      templateUrl: "routes/pageNotFound/pageNotFound.tpl.html",
      controller: "PageNotFoundController"
    });
  // For any unmatched url, redirect to page not found
  $urlRouterProvider.when('', '/');
  $urlRouterProvider.otherwise('/pageNotFound');
}]);

angular.module('templates', []);

// Web UI:

angular.module('app').controller('appCtrl', ['$scope', function($scope) {



}]);

angular.module('pageNotFound', [])

.controller('PageNotFoundController', ['$scope', function ($scope) {


}]);

angular.module('app').directive('breadcrumb', ['$state', function($state) {
  return {
    restrict: 'E',
    replace: true,
    templateUrl: "directives/breadcrumb.tpl.html",
    link: function(scope, element, attrs) {

      // TODO: Make this more abstracted and better

      scope.breadcrumbs = [];

      scope.$on('$stateChangeSuccess', function(event, toState, toParams){
        scope.breadcrumbs.length = 0;
        if ($state.current.name === 'sensors.list') {
          scope.breadcrumbs.push({
            name : "Sensors",
              state : "sensors.list",
              active : true
            }
          );
        } else if ($state.current.name === 'sensors.type.sensor') {
          scope.breadcrumbs.push(
            { name : "Sensors",
              state : "sensors.list",
              active : false
            }
          );
          scope.breadcrumbs.push(
            { name : toParams.type + "/" + toParams.sensor,
              state : "sensors.type.sensor({ type: '" + toParams.type + "', sensor: '" + toParams.sensor + "' })",
              active : true
            }
          );
        }
      });
    }
  };
}]);

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
            }
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

angular.module('app').factory('stbUtils', function(){

  var service = {
    getUrlQueryString : function() {
        var questionMarkIndex = window.location.href.indexOf('?');
        var queryString = '';
        if (questionMarkIndex > 1) {
            queryString = window.location.href.slice(window.location.href.indexOf('?') + 1);
        }
        return queryString;
    },
    getUrlVars : function() {
        var vars = [], hash;
        var hashes = getUrlQueryString().split('&');
        for(var i = 0; i < hashes.length; i++)
        {
            hash = hashes[i].split('=');
            vars.push(hash[0]);
            vars[hash[0]] = hash[1];
        }
        return vars;
    }
  };

  return service;
});

angular.module('home', ['ui.router']);

angular.module('home').controller('HomeController', ['$scope', '$http', function($scope, $http) {

  $scope.view = {
    models : [],
    loading: true
  };

  $http.get('/_models').then(function(response){
    $scope.view.models = response.data;
    $scope.view.loading = false;
  }, onError);

  var onError = function(error) {
    console.log(error);
    $scope.view.loading = false;
  };


}]);

angular.module('pageNotFound', [])

.controller('PageNotFoundController', ['$scope', function ($scope) {


}]);

angular.module('sensors', ['ui.router']);

angular.module('sensors').config(['$stateProvider', '$urlRouterProvider', function ($stateProvider, $urlRouterProvider) {
    $stateProvider
      // sensors
      .state('sensors', {
        url: '/sensors',
        abstract: true,
        templateUrl: 'routes/sensors/sensors.tpl.html'
      })
      .state('sensors.list', {
        url: '',
        templateUrl: 'routes/sensors/sensors.list.tpl.html',
        controller: "SensorsListController"
      })
      .state('sensors.type', {
        url: '/:type',
        templateUrl: 'routes/sensors/sensor.type.tpl.html',
        controller: "SensorTypeController"
      })
      .state('sensors.type.sensor', {
        url: '/:sensor',
        templateUrl: 'routes/sensors/sensor.tpl.html',
        controller: "SensorController"
      });
    }
  ]
);

angular.module('sensors').controller('SensorsListController', ['$scope', '$http', 'CONFIG', function($scope, $http, CONFIG) {

  $scope.sensors = [];

  $scope.sensorPath = function(sensorName) {
    // break up paths
    var arr = sensorName.split("/");
    return {
      type : arr[0],
      sensor : arr[1]
    };
  };

  $http.get('/_data/sensors').then(function(response){
    $scope.sensors = response.data;
  });

  $scope.setLimit = function() {
    $scope.$broadcast("setLimit", $scope.view.limit);
  };

  $scope.setSince = function() {
    $scope.$broadcast("setSince", $scope.view.since);
  };

  $scope.view = {
    sinceOptions : CONFIG.SINCE_OPTIONS,
    limitOptions : CONFIG.LIMIT_OPTIONS,
    limit : CONFIG.LIMIT_OPTIONS[0],
    since : null
  };

}]);

angular.module('sensors').controller('SensorTypeController', ['$scope', '$http', '$stateParams', function($scope, $http, $stateParams) {

}]);

angular.module('sensors').controller('SensorController', ['$scope', '$http', '$stateParams', function($scope, $http, $stateParams) {

  $scope.view = {
    sensor : $stateParams.type + "/" + $stateParams.sensor
  };
}]);

angular.module("templates").run(["$templateCache", function($templateCache) {$templateCache.put("directives/breadcrumb.tpl.html","<ol class=\"breadcrumb\">\n  <li><a ui-sref=\"home\">Home</a></li>\n  <li ng-repeat=\"breadcrumb in breadcrumbs\" ng-class=\"{ \'active\' : breadcrumb.active }\"><a ng-if=\"!breadcrumb.active\" ui-sref=\"{{breadcrumb.state}}\">{{breadcrumb.name}}</a><span ng-if=\"breadcrumb.active\">{{breadcrumb.name}}</li>\n</ol>\n");
$templateCache.put("directives/stbChart.tpl.html","<div class=\"chart\">\n  <div class=\"chart-controls form-horizontal\">\n    <div class=\"form-group\">\n      <div class=\"col-md-3\">\n        <label class=\"col-md-6 control-label\">Row Limit:</label>\n        <div class=\"col-md-6\">\n          <select class=\"form-control\" ng-options=\"limit for limit in view.limitOptions\" ng-model=\"view.limit\" ng-change=\"getData()\">\n            <option value=\"\">None</option>\n          </select>\n        </div>\n      </div>\n      <div class=\"col-md-3\">\n        <label class=\"col-md-6 control-label\">Time limit:</label>\n        <div class=\"col-md-6\">\n          <select class=\"form-control\" ng-options=\"(value.number + \' \' + value.units) for (name, value) in view.sinceOptions\" ng-model=\"view.since\" ng-change=\"getData()\">\n            <option value=\"\">None</option>\n          </select>\n        </div>\n      </div>\n      <div class=\"col-md-6\">\n        <label class=\"col-md-3 control-label\">Visibility:</label>\n        <div class=\"col-md-9\">\n          <ul class=\"set-visiblity\">\n            <li ng-repeat=\"field in view.fieldStates track by field.id\" ng-if=\"field.name === \'anomalyScore\' || field.name === \'anomalyLikelihood\'\"><input type=\"checkbox\" ng-model=\"field.visible\" ng-click=\"toggleVisibility(field)\"> <label style=\"color: {{field.color}}\">{{field.name}}</label></li>\n          </ul>\n        </div>\n      </div>\n    </div>\n  </div>\n  <div class=\"loading\" ng-show=\"view.loading\"><span class=\"loading-spin\"></span></div>\n  <div class=\"chart-container\"></div>\n</div>\n");
$templateCache.put("routes/home/home.tpl.html","<div class=\"jumbotron\">\n    <h1>SmartThings HTM Bridge</h1>\n\n    <p>This is a <a href=\"https://github.com/rhyolight/smartthings.htm.bridge\">work in progress</a>.</p>\n\n    <p>SmartApps can <code>POST</code> data to this URL to relay it into HTM.</p>\n\n    <p><a class=\"btn btn-primary btn-lg\" ui-sref=\"sensors.list\" role=\"button\">See Charts</a></p>\n\n</div>\n\n<p>This web server relays SmartThings data from a SmartApp into an <a href=\"https://github.com/nupic-community/htm-over-http\">HTM HTTP server</a>.</p>\n\n<div class=\"model-list\">\n  <h3>The following models are active in HTM:</h3>\n  <div class=\"loading\" ng-show=\"view.loading\"><span class=\"loading-spin\"></span></div>\n  <ul>\n      <li ng-repeat=\"model in view.models\">{{model}}</li>\n  </ul>\n</div>\n");
$templateCache.put("routes/pageNotFound/pageNotFound.tpl.html","<div class=\"page-not-found container-fluid\">\n  <div class=\"jumbotron\">\n  <h3>We are sorry, but could not find the page you are looking for.</h3>\n  </div>\n</div>\n");
$templateCache.put("routes/sensors/sensor.tpl.html","<div class=\"panel panel-info\">\n  <div class=\"panel-heading\">\n    <h3 class=\"panel-title\">\n      {{view.sensor}}\n    </h3>\n  </div>\n  <stb-chart sensor-name=\"{{view.sensor}}\"></stb-chart>\n</div>\n");
$templateCache.put("routes/sensors/sensor.type.tpl.html","<div ui-view></div>\n");
$templateCache.put("routes/sensors/sensors.list.tpl.html","<div class=\"panel panel-warning sensors-panel\">\n    <div class=\"panel-heading clearfix\">\n      <div class=\"row dropdowns\">\n        <div class=\"col-md-4\">\n          <div class=\"btn-group\">\n            <button class=\"btn btn-default dropdown-toggle\" type=\"button\" id=\"dropdownMenu1\" data-toggle=\"dropdown\" aria-haspopup=\"true\" aria-expanded=\"true\">\n              Jump to a chart <span class=\"caret\"></span>\n            </button>\n            <ul class=\"dropdown-menu\" aria-labelledby=\"dropdownMenu1\">\n                <li ng-repeat=\"sensor in sensors\"><a ui-sref=\"sensors.type.sensor(sensorPath(sensor))\">{{sensor}}</a></li>\n            </ul>\n          </div>\n        </div>\n        <div class=\"col-md-8 form-inline limits\">\n          <span class=\"set-limits\">Set limits for all charts:</span>\n          <div class=\"btn-group\">\n            <label for=\"limitOptions\">Row limit</label>\n            <select class=\"form-control\" name=\"limitOptions\" ng-options=\"limit for limit in view.limitOptions\" ng-model=\"view.limit\" ng-change=\"setLimit()\">\n              <option value=\"\">None</option>\n            </select>\n          </div>\n          <div class=\"btn-group\">\n            <label for=\"limitOptions\">Time limit</label>\n            <select class=\"form-control\" name=\"sinceOptions\" ng-options=\"(value.number + \' \' + value.units) for (name, value) in view.sinceOptions\" ng-model=\"view.since\" ng-change=\"setSince()\">\n              <option value=\"\">None</option>\n            </select>\n          </div>\n        </div>\n      </div>\n    </div>\n    <div class=\"panel-body\">\n        <h2 class=\"panel-title\" id=\"top\">About the Charts</h2>\n        <p>\n            Anomaly values are plotted on the secondary Y axis on the right. Door open/close values are either <code>0</code> or <code>1</code>. I don\'t understand the acceleration data yet. Data is coming from a <a href=\"https://github.com/rhyolight/smartthings-apps/blob/master/http-poster.groovy\">SmartThings app</a>. It is being send via HTTP to <a href=\"https://github.com/numenta/nupic\">NuPIC</a> running behind a <a href=\"https://github.com/nupic-community/hitc\">REST API</a>. Sensor values and HTM results are saved to a time-series database called <a href=\"https://docs.influxdata.com/influxdb/v0.9/concepts/key_concepts/\">InfluxDB</a>.\n        </p>\n       <!-- <p>\n            You can also use the URL query parameters to declare how many data points you want to show in the graph(s) below. Just add <code>?limit=X</code> to the URL, or use the dropdown in the panel header above.\n        </p> -->\n    </div>\n</div>\n<div class=\"panel panel-info\" ng-repeat=\"sensor in sensors\">\n  <div class=\"panel-heading\">\n    <h3 class=\"panel-title\">\n        <a ui-sref=\"sensors.type.sensor(sensorPath(sensor))\">{{sensor}}</a>\n    </h3>\n  </div>\n  <stb-chart sensor-name=\"{{sensor}}\"></stb-chart>\n</div>\n");
$templateCache.put("routes/sensors/sensors.tpl.html","<div class=\"page-header\">\n  <h1>Live SmartThings Sensor Values <small>and HTM anomaly scores</small></h1>\n</div>\n\n<breadcrumb></breadcrumb>\n<div ui-view></div>\n");}]);