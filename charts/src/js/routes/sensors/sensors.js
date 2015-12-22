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

angular.module('sensors').controller('SensorsListController', ['$scope', '$http', function($scope, $http) {

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

}]);

angular.module('sensors').controller('SensorTypeController', ['$scope', '$http', '$stateParams', function($scope, $http, $stateParams) {

}]);

angular.module('sensors').controller('SensorController', ['$scope', '$http', '$stateParams', function($scope, $http, $stateParams) {

  $scope.view = {
    sensor : $stateParams.type + "/" + $stateParams.sensor
  };
}]);
