angular.module('home', ['ui.router']);

angular.module('home').controller('HomeController', ['$scope', '$http', function($scope, $http) {

  $scope.view = {
    models : []
  };

  $http.get('/_models').then(function(response){
    $scope.view.models = response.data;
  });


}]);
