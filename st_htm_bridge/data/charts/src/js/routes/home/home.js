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
