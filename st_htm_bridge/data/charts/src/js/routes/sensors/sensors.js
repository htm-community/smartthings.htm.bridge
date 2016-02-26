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

  $scope.setLimits = function() {
    $scope.$broadcast("setLimits", {
      limit : $scope.view.limit,
      since : $scope.view.since,
      aggregate : $scope.view.aggregate
    });
  };

  $scope.checkAggregate = function() {
    if (!$scope.view.aggregate.unit || !$scope.view.aggregate.number) {
      $scope.view.aggregate.number = null;
      $scope.view.aggregate.unit = null;
    }
  };

  $scope.view = {
    sinceOptions : CONFIG.SINCE_OPTIONS,
    limitOptions : CONFIG.LIMIT_OPTIONS,
    limit : CONFIG.LIMIT_OPTIONS[0],
    since : null,
    aggregateOptions : CONFIG.AGGREGATE_OPTIONS,
    aggregate : {
      number : null,
      unit : null
    }
  };

}]);

angular.module('sensors').controller('SensorTypeController', ['$scope', '$http', '$stateParams', function($scope, $http, $stateParams) {

}]);

angular.module('sensors').controller('SensorController', ['$scope', '$http', '$stateParams', function($scope, $http, $stateParams) {

  $scope.view = {
    sensor : $stateParams.type + "/" + $stateParams.sensor
  };
}]);
